#!/usr/bin/env python3

import asyncore
import socket
import re

class EchoHandler(asyncore.dispatcher):

    def __init__(self, socket, server):
        asyncore.dispatcher_with_send.__init__(self, socket)
        self.buffer = bytearray()

        self.server = server
        self.server.clients.add(self)

        self.nick = None
        self.user = None
        self.registered = False

    def handle_read(self):
        # FIXME: i think this breaks if the final message is incomplete (it
        # will send that message anyway)
        data = self.recv(8192)
        if data:
            str_data = bytes.decode(data)
            print(repr(str_data))
            messages = re.split('[\r\n]+', str_data)
            for message in messages:
                if len(message):
                    self.dispatch(message)

    def handle_write(self):
        sent = self.send(self.buffer)
        self.buffer = self.buffer[sent:]

    def parse(self, msg):
        return re.split('\s+', msg)

    def dispatch(self, msg):
        message = self.parse(msg)
        command = message[0].upper()
        args = message[1:]
        print('DEBUG: command=%s args=%s' % (command, args))

        if command == 'NICK':
            # TODO: err 437

            if not len(args):
                self._send(431, ':No nickname given')
                return

            # TODO: validate nickname (432)

            nick = args[0]
            if nick in self.server.names:
                self._send(433, '%s :Nickname is already in use' % self.nick)
                return

            # TODO: nickname collision (436) -- multiple server stuff

            # TODO: restricted (484)

            # i'm not really sure when it's best to lock the nick, freenode
            # seems to not lock the nick until you're registered, so i guess
            # that's how we should do it too
            if self.registered:
                old_nick = self.nick
                # TODO: nick delay mechanism
                self.server.names.remove(old_nick)
                self.server.names.add(nick)

            self.nick = nick

        elif command == 'USER':
            if len(args) < 4:
                self. _err_need_more_params(command)
                return

            if self.registered:
                self._send(462, ':Unauthorized command (already registered)')

            user = args[0]
            mode = args[1]
            realname = str.join(" ", args[3:]) # NOTE: real command parser will fix this

            self.user = user, mode, realname

            # TODO? write a nick-changing method that checks for this nick (race condition?)
            self.server.names.add(self.nick) 
            self.registered = True
            self._send(1, 'Welcome to the Internet Relay Network %s' % self.nick)
            self._send(2, 'Your host is FIXME, running version FIXME')
            self._send(3, 'This server was created FIXME')
            self._send(4, 'FIXMEservername FIXMEversion FIXMEusemodes FIXMEchannelmodes')

            # TODO: show motd

        elif command == 'JOIN':
            # TODO: support multiple channels at once
            # TODO: support leaving all channels ('0')
            # TODO: support keys
            channel = args[0]

            if channel not in self.server.channels:
              self.server.channels[channel] = Channel(channel, server)
            self.server.channels[channel].add(self)

        elif command == 'QUIT':
            self.server.clients.remove(self)

            # TODO: notify relevant servers/clients

            if self.registered:
                self.server.names.remove(self.nick)

            # TODO: send error message (see RFC)
            self.close()
        else:
            # raise an error
            pass

        print(repr(self.server))

    def prefix(self):
        return ":%s" % self.nick

    def _err_need_more_params(self, command):
        self._send(461, '%s :Not enough parameters' % command)

    def _send(self, code, message):
        msg = '%s %03d %s %s\n' % (self.server.prefix(), code, self.nick, message)
        self.raw_send(msg)

    def raw_send(self, message):
        self.buffer += message.encode()

    def readable(self):
        return True

    def writeable(self):
        return (len(self.buffer) > 0)

    def __repr__(self):
        return "<IrcClient: nick=" + repr(self.nick) + " registered=" + repr(self.registered) + " user=" + repr(self.user) + ">"

class IrcServer(asyncore.dispatcher):

    def __init__(self, host, port):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind((host, port))
        self.listen(5)
        print('Listening on port %s' % port)

        self.clients = set()
        self.names = set()
        self.channels = dict()

    def handle_accepted(self, socket, port):
        print('Yay, connection from %s' % repr(port))
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
        client._send(331, '%s :No topic is set' % self.name)
        self.rpl_name_reply(client)

    def remove(self, nick):
        pass

    def rpl_name_reply(self, client):
        # TODO: probably need to split the names list up in case it's too long
        names = [c.nick for c in self.clients]
        client._send(353, '= %s :%s' % (self.name, str.join(' ', names)))
        client._send(366, '%s :End of NAMES list' % self.name)

    def _send(self, sender, message):
        self.server.notify_channel(self.name, sender.prefix(), message)
        
server = IrcServer('', 6667)
asyncore.loop()
