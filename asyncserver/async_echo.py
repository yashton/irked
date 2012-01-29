#!/usr/bin/env python3

import asyncore
import logging
import socket
import re
import irc

LOG_FILE = "/tmp/bb_ircd.log"
LOG_FORMAT = "%(asctime)s %(filename)s:" + \
    "%(lineno)d in %(funcName)s %(levelname)s: %(message)s"
LOG_LEVEL = logging.DEBUG

LOGGER = logging.getLogger('bb_ircd')
LOGGER.setLevel(LOG_LEVEL)
FILE_HANDLER = logging.FileHandler(LOG_FILE)
FORMATTER = logging.Formatter(LOG_FORMAT)
FILE_HANDLER.setFormatter(FORMATTER)
LOGGER.addHandler(FILE_HANDLER)

class EchoHandler(asyncore.dispatcher):

    def __init__(self, socket, server):
        asyncore.dispatcher_with_send.__init__(self, socket)
        self.out_buffer = bytearray()
        self.in_buffer = b''
        self.server = server
        self.server.clients.add(self)

        self.nick = None
        self.user = None
        self.registered = False

    def handle_read(self):
        self.in_buffer += self.recv(8192)
        if len(self.in_buffer) > 0:
            LOGGER.debug(self.in_buffer)
            messages = re.split(b'[\r\n]+', self.in_buffer)
            if messages[-1] != b'':
                self.in_buffer = messages[-1]
            else:
                self.in_buffer = b''
            for message in messages[:-1]:
                LOGGER.debug(message)
                self.dispatch(bytes.decode(message))

    def handle_write(self):
        sent = self.send(self.out_buffer)
        self.out_buffer = self.out_buffer[sent:]

    def parse(self, msg):
        return re.split('\s+', msg)

    def dispatch(self, msg):
        message = self.parse(msg)
        command = message[0].upper()
        args = message[1:]
        LOGGER.debug('command=%s args=%s', command, args)

        if command == 'NICK':
            self.cmd_nick(args)
        elif command == 'USER':
            self.cmd_user(args)
        elif command == 'JOIN':
            self.cmd_join(args)
        elif command == 'QUIT':
            self.cmd_quit(args)
        else:
            LOGGER.error("Unknown command %s with args %s", command, args)
            pass

    def cmd_nick(self, args):
        # TODO: err irc.ERR_UNAVAILRESOURCE
        if not len(args):
            self._send(irc.ERR_NONICKNAMEGIVEN, ':No nickname given')
            return

        # TODO: validate nickname (irc.ERR_ERRONEUSNICKNAME)

        nick = args[0]
        if nick in self.server.names:
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
            self.server.names.remove(old_nick)
            self.server.names.add(nick)
        self.nick = nick

    def cmd_user(self, args):
        if len(args) < 4:
            self. _err_need_more_params(command)
            return

        if self.registered:
            self._send(irc.ERR_ALREADYREGISTRED, ':Unauthorized command (already registered)')

        user = args[0]
        mode = args[1]
        realname = str.join(" ", args[3:]) # NOTE: real command parser will fix this

        self.user = user, mode, realname

        # TODO? write a nick-changing method that checks for this nick (race condition?)
        self.server.names.add(self.nick) 
        self.registered = True
        self._send(irc.RPL_WELCOME, 'Welcome to the Internet Relay Network %s' % self.nick)
        self._send(irc.RPL_YOURHOST, 'Your host is FIXME, running version FIXME')
        self._send(irc.RPL_CREATED, 'This server was created FIXME')
        self._send(irc.RPL_MYINFO, 'FIXMEservername FIXMEversion FIXMEusemodes FIXMEchannelmodes')
            
        # TODO: show motd


    def cmd_join(self, args):
        # TODO: support multiple channels at once
        # TODO: support leaving all channels ('0')
        # TODO: support keys
        channel = args[0]

        if channel not in self.server.channels:
            self.server.channels[channel] = Channel(channel, server)
        self.server.channels[channel].add(self)

    def cmd_quit(self, args):
        self.server.clients.remove(self)
        
        # TODO: notify relevant servers/clients
        
        if self.registered:
            self.server.names.remove(self.nick)

        # TODO: send error message (see RFC)
        self.close()
        


        LOGGER.debug(repr(self.server))

    def prefix(self):
        return ":%s" % self.nick

    def _err_need_more_params(self, command):
        self._send(irc.ERR_NEEDMOREPARAMS, '%s :Not enough parameters' % command)

    def _send(self, code, message):
        msg = '%s %03d %s %s\n' % (self.server.prefix(), code, self.nick, message)
        self.raw_send(msg)

    def raw_send(self, message):
        self.out_buffer += message.encode()

    def readable(self):
        return True

    def writeable(self):
        return (len(self.out_buffer) > 0)

    def __repr__(self):
        return "<IrcClient: nick=" + repr(self.nick) + " registered=" + repr(self.registered) + " user=" + repr(self.user) + ">"

class IrcServer(asyncore.dispatcher):

    def __init__(self, host, port):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind((host, port))
        self.listen(5)
        LOGGER.info('Listening on port %s', port)

        self.clients = set()
        self.names = set()
        self.channels = dict()

    def handle_accepted(self, socket, port):
        LOGGER.info('Yay, connection from %s', repr(port))
        handler = EchoHandler(socket, self)
        self.clients.add(handler)

    def notify_channel(self, channel, prefix, message):
        """send message to all users in the given channel"""
        for client in self.channels[channel].clients:
            client.raw_send('%s %s\n' % (prefix, message))

    def prefix(self):
        # FIXME
        return ":server"

    def __repr__(self):
        return "<IrcServer: clients=" + repr(self.clients) + " names=" + repr(self.names) + " channels=" + repr(self.channels) + ">"

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
        client._send(irc.RPL_NOTOPIC, '%s :No topic is set' % self.name)
        self.rpl_name_reply(client)

    def remove(self, nick):
        pass

    def rpl_name_reply(self, client):
        # TODO: probably need to split the names list up in case it's too long
        names = [c.nick for c in self.clients]
        client._send(irc.RPL_NAMREPLY, '= %s :%s' % (self.name, str.join(' ', names)))
        client._send(irc.RPL_ENDOFNAMES, '%s :End of NAMES list' % self.name)

    def _send(self, sender, message):
        self.server.notify_channel(self.name, sender.prefix(), message)
        
server = IrcServer('', 6667)
asyncore.loop()
