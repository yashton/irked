#!/usr/bin/env python3

import asyncore
import logging
import socket as _socket
import re
import irc
import time
import subprocess
from irc.client import IrcClient, IrcServer

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
            self._send(irc.ERR_NONICKNAMEGIVEN)
            return

        # TODO: validate nickname (irc.ERR_ERRONEUSNICKNAME)

        nick = args[0]
        if nick in self.server.clients:
            self._send(irc.ERR_NICKNAMEINUSE, nickname=self.nick)
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

    def _send(self, code, **format_args):
        name, message = irc.IRC_CODE[code]
        formatted_message = message % format_args
        msg = '%s %03d %s %s\n' % (self.server.prefix(), code, self.nick, formatted_message)
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

    def __repr__(self):
        return "<IrcClient: nick=" + repr(self.nick) + " registered=" + repr(self.registered) + " user=" + repr(self.user) + ">"

class IrcDispatcher(asyncore.dispatcher):

    def __init__(self, host, port, name = ''):
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

        if len(name) == 0:
            self.name = 'irked.server' # config option

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

    def is_valid_oper_pass(self, username, password):
        #TODO O-line implementation
        return True

    def allows_oper(self):
        #TODO O-line implementation
        return True

class Channel:
    def __init__(self, name, server):
        self.name    = name
        self.clients = set()
        self.topic   = None

        self.modes = ChannelMode()
        self.server  = server

    def add(self, client):
        self.clients.add(client)
        self._send(client, 'JOIN %s' % self.name)

        # TODO: proper topic sending
        if self.topic is None or self.topic == '':
            client.connection._send(irc.RPL_NOTOPIC, channel=self.name)
        else:
            client.connection._send(irc.RPL_TOPIC, channel=self.name, topic=self.topic)

        self.rpl_name_reply(client)

    def remove(self, client, message = None, parted = True):
        if client in self.clients:
            if parted:
                if message:
                    self._send(client, 'PART %s :%s' % (self.name, message))
                else:
                    self._send(client, 'PART %s' % self.name)
            self.clients.remove(client)
        else:
            client.connection._send(irc.ERR_NOTONCHANNEL, channel=self.name)

    def kick(self, kicker, kickee, reason):
        # TODO: kickee probably can be more than just a nick

        if kicker not in self.clients:
            kicker.connection._send(irc.ERR_NOTONCHANNEL, channel_name=self.name)
            return

        if kicker not in channel.modes.operators:
            kicker.connection._send(irc.ERR_CHANOPRIVSNEEDED, channel=self.name)
            return

        if kickee not in [c.connection.nick for c in self.clients]:
            kicker.connection_send(irc.ERR_USERNOTINCHANNEL,
                                   nickname=kickee, channel=self.name)
            return

        if not reason:
            reason = kickee

        self._send(kicker, "KICK %s %s :%s" % (self.name, kickee, reason))

    def rpl_name_reply(self, client):
        # TODO: probably need to split the names list up in case it's too long
        names = [c.connection.nick for c in self.clients]
        client.connection._send(irc.RPL_NAMREPLY,
                                channel=self.name, nick=str.join(' ', names))
        client.connection._send(irc.RPL_ENDOFNAMES, channel=self.name)

    def _send(self, sender, message, notify_sender = True):
        self.server.notify_channel(self.name, sender, message, notify_sender)

class ChannelMode:
    def __init__(self):
        self.creator = None
        self.operators = set()
        self.voice = set()

        self.anonymous = False
        self.moderated = False
        self.invite = False
        self.no_message = False
        self.quiet = False
        self.private = False
        self.secret = False
        self.reop = False
        self.topic = False

        self.ban_masks = set()
        self.exception_masks = set()
        self.invite_masks = set()

        self.key = None
        self.limit = None

    def user_mode(self, nick):
        #TODO return real values
        return "+ns"

if __name__ == '__main__':        
    server = IrcDispatcher('', 6667)
    asyncore.loop()
