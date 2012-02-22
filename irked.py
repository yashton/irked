#!/usr/bin/env python3

import asyncore
import logging
import socket as _socket
import re
import irc
import time
import subprocess
import os.path
import sys
import argparse
import configparser
from irc.client import IrcClient, IrcServer
from irc.channel import Channel

MOTD_FILE = "motd"
INFO_FILE = "info"
CONFIG_FILE = 'irked.conf'

LOG_FILE = "irked.log"
LOG_FORMAT = "%(asctime)s %(filename)s:" + \
    "%(lineno)d in %(funcName)s %(levelname)s: %(message)s"
LOG_LEVEL = logging.DEBUG
LOGGER = "irked"

DEFAULT_HOST = ''
DEFAULT_PORT = 6667
DEFAULT_NAME = 'irked.server'

class IrcHandler(asyncore.dispatcher):

    def __init__(self, socket, server):
        asyncore.dispatcher.__init__(self, socket)
        self.out_buffer = bytearray()
        self.in_buffer = b''

        self.server = server
        self.server.connections.add(self)

        self.handler = None
        self.nick = None
        self.user = None
        self.has_nick = False
        self.has_user = False
        # TODO verify: need to get hostname, not IP address.
        self.host = "%s:%d" % socket.getpeername()
        self.registered = False

    def handle_read(self):
        self.in_buffer += self.recv(8192)
        if len(self.in_buffer) > 0:
            self.server.logger.debug(self.in_buffer)
            messages = re.split(b'[\r\n]+', self.in_buffer)
            # Complete messages end in trailing newlines, yielding empty string.
            if messages[-1] != b'':
                self.in_buffer = messages[-1]
            else:
                self.in_buffer = b''
            for message in messages[:-1]:
                self.server.logger.debug(message)
                self.dispatch(bytes.decode(message))

    def handle_write(self):
        self._flush()

    def _flush(self):
        sent = self.send(self.out_buffer)
        self.out_buffer = self.out_buffer[sent:]

    def close(self):
        while len(self.out_buffer):
            self._flush()
        asyncore.dispatcher.close(self)

    def parse(self, message):
        # this stuff will be useful for the server, but the client message
        # syntax is simpler (prefixes are ignored, for example)
        #hostname = '[-a-zA-Z0-9.]+' # FIXME: this is overly simple
        #nick     = '[a-zA-Z\[\]\\`_^{}]+[-a-zA-Z\[\]\\`_^{}]'
        #user     = '[\x01-\x09\x0b-\x0c\x0e-\x1f\x21-\x3f\x41-\xff]+'

        #prefix  = '(?::(?P<prefix>%s|%s!%s@%s) +)?' % (hostname, nick, user, hostname)
        #command = '(?P<command>[a-zA-Z]+|\d\d\d)'
        #params  = '(?P<params>.*)'

        #message_pattern = '%s%s +%s' % (prefix, command, params)

        #if match = re.match(message_pattern, message):
        #    return match.groupdict()

        # prefix is ignored from clients
        message = re.sub('^:[^ ]+ ', '', message)

        trailing = None
        match = re.search(':(.*)$', message)
        if match:
            trailing = match.groups()[0]
            message = message[:match.start()]

        params  = message.split()
        if trailing != None:
            params.append(trailing)

        command = params[0].upper()
        params = params[1:]

        return (command, params)

    def dispatch(self, msg):
        command, args = self.parse(msg)
        self.server.logger.debug('received from %s: command=%s args=%s', self.nick, command, args)

        if command == 'PASS':
            pass
            #TODO password hashing 
        elif command == 'NICK':
            self.cmd_nick(args)
        elif command == 'USER':
            self.cmd_user(args)
        elif command == 'SERVER':
            self.handler = IrcServer(self, self.server)
            self.handler.cmd_server(args)
        else:
            if self.handler is not None:
                self.handler.cmd(command, args)
            else:
                self.server.logger.error("Command %s was sent before USER or SERVER: %s",
                                         command,
                                         msg)

    def cmd_nick(self, args):
        # TODO: err irc.ERR_UNAVAILRESOURCE
        if not len(args):
            self._send(irc.ERR_NONICKNAMEGIVEN)
            return

        # TODO: validate nickname (irc.ERR_ERRONEUSNICKNAME)

        nick = args[0]
        if nick in self.server.clients:
            self._send(irc.ERR_NICKNAMEINUSE, nickname=nick)
            return

        # TODO: nickname collision (irc.ERR_NICKCOLLISION) -- multiple server stuff

        # TODO: restricted (irc.ERR_RESTRICTED)
        # i'm not really sure when it's best to lock the nick, freenode
        # seems to not lock the nick until you're registered, so i guess
        # that's how we should do it too
        if self.registered:
            old_nick = self.nick
            # TODO: nick delay mechanism
            self.server.clients[nick] = self.handler
            del self.server.clients[old_nick]

        self.nick = nick
        self.has_nick = True

        if self.has_user and not self.registered:
            self.register()

    def cmd_user(self, args):
        if len(args) < 4:
            self._send(irc.ERR_NEEDMOREPARAMS, command='USER')
            return

        if self.registered:
            self._send(irc.ERR_ALREADYREGISTRED)

        user = args[0]
        mode = args[1]
        realname = args[3]
        self.user = user, mode, realname

        self.has_user = True
        if self.has_nick:
            self.register()

    def register(self):
        # TODO? write a nick-changing method that checks for this nick (race condition?)
        self.server.clients[self.nick] = self
        self.registered = True
        self._send(irc.RPL_WELCOME,
                   nick=self.nick,
                   user=self.user[0],
                   host=self.host)
        self._send(irc.RPL_YOURHOST,
                   server=self.server.name,
                   version=self.server.version)
        self._send(irc.RPL_CREATED,
                   launched=self.server.launched)
        self._send(irc.RPL_MYINFO,
                   server=self.server.name,
                   version=self.server.version,
                   user_modes=irc.mode_str(self.server.user_modes),
                   channel_modes=irc.mode_str(self.server.channel_modes))
        self.handler = IrcClient(self, self.server)

    def _err_need_more_params(self, command):
        self._send(irc.ERR_NEEDMOREPARAMS, '%s :Not enough parameters' % command)

    def _send(self, code, **format_args):
        name, message = irc.IRC_CODE[code]
        formatted_message = message % format_args
        msg = '%s %03d %s %s\n' % (self.server.prefix(), code, self.nick or "*", formatted_message)
        self.server.logger.debug("sent %s to %s", name, self.nick)
        self.raw_send(msg)

    def raw_send(self, message):
        self.server.logger.debug("sent to %s: '%s'",
                                 self.nick,
                                 message.rstrip("\r\n"))
        self.out_buffer += message.encode()

    def readable(self):
        return True

    def writeable(self):
        return (len(self.out_buffer) > 0)

    def _host(self):
        return self.getsockname()[0]

    def __repr__(self):
        return "<IrcClient: nick=" + repr(self.nick) + " registered=" + repr(self.registered) + " user=" + repr(self.user) + ">"

class IrcDispatcher(asyncore.dispatcher):

    def __init__(self, host=None, port=None, name=None, config=CONFIG_FILE):
        self.config_file = config
        self.init_logger()
        self.parse_config(host, port, name)

        asyncore.dispatcher.__init__(self)
        self.create_socket(_socket.AF_INET, _socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind(self.address)
        self.listen(5)
        self.logger.info('Bound to "%s", listening on port %d' % self.address)

        self.connections = set()
        self.clients = dict()
        self.servers = dict()
        self.services = dict()
        self.channels = dict()
        self.user_modes = dict()
        for i in irc.IRC_MODES:
            self.user_modes[i] = True
        self.channel_modes = dict()
        for i in irc.IRC_CHANNEL_MODES:
            self.channel_modes[i] = True

        self.version = self.gen_version()
        self.version_comment = 'Development'
        self.launched = time.strftime("%c %Z")
        self.logger.info('Server %s running irked version %s launched on %s',
                         self.name,
                         self.version,
                         self.launched)

    def parse_config(self, host, port, name):
        config = configparser.ConfigParser()
        config.read(self.config_file)

        if host is None:
            host = config.get('server', 'host', fallback=DEFAULT_HOST)
        if port is None:
            port = config.getint('server', 'port', fallback=DEFAULT_PORT)
        self.address = (host, port)

        if name is None:
            name = config.get('server', 'name', fallback=DEFAULT_NAME)
        self.name = name

        self.motd = config.get('server', 'motd_file', fallback=MOTD_FILE)
        self.info_file = config.get('server', 'info_file', fallback=INFO_FILE)

    def init_logger(self):
        config = configparser.ConfigParser()
        config.read(self.config_file)
        log_file = config.get("log", "log_file", fallback=LOG_FILE)
        log_level_string = config.get("log", "log_level", fallback=None)
        if log_level_string is not None:
            try:
                log_level = logging.__dict__[log_level_string]
            except KeyError:
                log_level = LOG_LEVEL
        else:
            log_level = LOG_LEVEL

        self.logger = logging.getLogger(LOGGER)
        self.logger.setLevel(log_level)
        file_handler = logging.FileHandler(log_file)
        formatter = logging.Formatter(LOG_FORMAT)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        self.logger.info("Initialized logger %s at level %d to file %s.",
                         LOGGER,
                         log_level,
                         log_file)

    def channel_add(self, channel, owner):
        self.channels[channel] = Channel(channel, self)
        self.channels[channel].modes.creator = owner
        self.channels[channel].modes.operators.add(owner)

    def handle_accepted(self, socket, port):
        self.logger.info('Yay, connection from %s', repr(port))
        handler = IrcHandler(socket, self)
        self.connections.add(handler)

    def notify_channel(self, channel, sender, message, notify_sender = True):
        """send message to all users in the given channel"""

        # TODO: check that the sender has permission to send messages here

        for client in self.channels[channel].clients:
            if client == sender and not notify_sender:
                continue
            client.connection.raw_send('%s %s\n' % (sender.prefix(), message))

    def prefix(self):
        # FIXME
        return ':%s' % self.name

    def __repr__(self):
        return "<IrcServer: clients=" + repr(self.connections) + " names=" + repr(self.clients.keys()) + " channels=" + repr(self.channels) + ">"

    def gen_version(self):
        '''Fetch the current revision number for the working directory for
        use as a version number'''
        try:
            branch = subprocess.check_output(["hg", "branch"])
            command = ["hg", "heads",
                       branch.strip(),
                        "--template", "{rev}:{node|short} ({date|isodate})"]
            version = subprocess.check_output(command)
            return "%s-%s" % ("irked", version.decode("utf-8"))
        except CalledProcessError:
            return "unknown"

    def info(self):
        '''Returns an iterable set of info lines.'''
        yield "irked IRC daemon version %(version)s" % {'version' : self.gen_version()}
        if os.path.isfile(self.info_file):
            for line in open(self.info_file):
                yield line.rstrip()

    def is_valid_oper_pass(self, username, password):
        #TODO O-line implementation
        return True

    def allows_oper(self):
        #TODO O-line implementation
        return True

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='irked IRC daemon.',
                                     epilog='Command line options have priority over config file values.')
    parser.add_argument('-s', '--server',
                        nargs='?', default=None,
                        help='Server host bind address.')
    parser.add_argument('-p', '--port',
                        type=int, nargs='?', default=None,
                        help='Server port. Defaults to %d.' % DEFAULT_PORT)
    parser.add_argument('-n', '--name',
                        nargs='?', default=None,
                        help='Server name.')
    parser.add_argument('-c', '--config',
                        nargs='?', default=CONFIG_FILE,
                        help='Configuration file. (default: %(default)s)')
    args = parser.parse_args()

    server = IrcDispatcher(host=args.server,
                           port=args.port,
                           name=args.name,
                           config=args.config)
    asyncore.loop()
