#!/usr/bin/env python3

import asyncore
import logging
import socket as _socket
import re
import irc
import time
import subprocess
from ircclient import IrcClient, IrcServer

MOTD_FILE = "motd"

LOG_FILE = "irked.log"
LOG_FORMAT = "%(asctime)s %(filename)s:" + \
    "%(lineno)d in %(funcName)s %(levelname)s: %(message)s"
LOG_LEVEL = logging.DEBUG
LOGGER = "irked"

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
        sent = self.send(self.out_buffer)
        self.out_buffer = self.out_buffer[sent:]

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
        if trailing:
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
            self.handler = IrcClient(self, self.server)
            self.handler.cmd_user(args)
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
            self._send(irc.ERR_NONICKNAMEGIVEN, ':No nickname given')
            return

        # TODO: validate nickname (irc.ERR_ERRONEUSNICKNAME)

        nick = args[0]
        if nick in self.server.clients:
            self._send(irc.ERR_NICKNAMEINUSE, '%s :Nickname is already in use' % self.nick)
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

    def prefix(self):
        return ":%s" % self.nick

    def _err_need_more_params(self, command):
        self._send(irc.ERR_NEEDMOREPARAMS, '%s :Not enough parameters' % command)

    def _send(self, code, message, *format_args):
        formatted_message = message % format_args
        msg = '%s %03d %s %s\n' % (self.server.prefix(), code, self.nick, formatted_message)
        self.server.logger.debug("sent to %s: '%s'", self.nick, msg[:-1])
        self.raw_send(msg)

    def raw_send(self, message):
        self.out_buffer += message.encode()

    def readable(self):
        return True

    def writeable(self):
        return (len(self.out_buffer) > 0)

    def __repr__(self):
        return "<IrcClient: nick=" + repr(self.nick) + " registered=" + repr(self.registered) + " user=" + repr(self.user) + ">"

class IrcDispatcher(asyncore.dispatcher):

    def __init__(self, host, port):
        self.motd = MOTD_FILE

        self.logger = logging.getLogger(LOGGER)
        self.logger.setLevel(LOG_LEVEL)
        file_handler = logging.FileHandler(LOG_FILE)
        formatter = logging.Formatter(LOG_FORMAT)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        asyncore.dispatcher.__init__(self)
        self.create_socket(_socket.AF_INET, _socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind((host, port))
        self.listen(5)
        self.logger.info('Listening on port %s', port)

        if len(host) == 0:
            self.name = _socket.gethostname()
        else:
            self.name = host

        self.connections = set()
        self.clients = dict()
        self.servers = dict()
        self.channels = dict()

        self.version = self.gen_version()
        #TODO return correct user modes
        self.usermodes = "FIXME-usermodes"
        self.channelmodes = "FIXME-channelmodes"
        self.launched = time.strftime("%c %Z")

    def channel_add(self, channel):
        self.channels[channel] = Channel(channel, self)

    def handle_accepted(self, socket, port):
        self.logger.info('Yay, connection from %s', repr(port))
        handler = IrcHandler(socket, self)
        self.connections.add(handler)

    def notify_channel(self, channel, prefix, message):
        """send message to all users in the given channel"""
        for client in self.channels[channel].clients:
            client.connection.raw_send('%s %s\n' % (prefix, message))

    def prefix(self):
        # FIXME
        return ":server"

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

class Channel:
    def __init__(self, name, server):
        self.name    = name
        self.clients = set()
        self.topic   = None

        self.server  = server

    def add(self, client):
        self.clients.add(client)
        self._send(client, 'JOIN %s' % self.name)

        # TODO: proper topic sending
        if self.topic is None or self.topic == '':
            client.connection._send(irc.RPL_NOTOPIC, '%s :No topic is set' % self.name)
        else:
            client.connection._send(irc.RPL_TOPIC, "%s :%s", self.name, self.topic)

        self.rpl_name_reply(client)

    def remove(self, nick):
        pass

    def rpl_name_reply(self, client):
        # TODO: probably need to split the names list up in case it's too long
        names = [c.connection.nick for c in self.clients]
        client.connection._send(irc.RPL_NAMREPLY, '= %s :%s' % (self.name, str.join(' ', names)))
        client.connection._send(irc.RPL_ENDOFNAMES, '%s :End of NAMES list' % self.name)

    def _send(self, sender, message):
        self.server.notify_channel(self.name, sender.prefix(), message)


if __name__ == '__main__':        
    server = IrcDispatcher('', 6667)
    asyncore.loop()
