import asyncore
import re
import irc
from irc.client import IrcClient
from irc.server import IrcServer

#
# A handler instance is spawned when a connection is made to Dispatcher.
# The handler determines what kind of client is attached (an irc client or
# server), parses commands, and passes them off to the IrcClient or IrcServer
# instance for its connection
#
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
        received = len(self.in_buffer)
        self.server.statistics.received.record(received)
        if received > 0:
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
        self.server.statistics.sent.record(sent)
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

        #prefix  =
        # '(?::(?P<prefix>%s|%s!%s@%s) +)?' % (hostname, nick, user, hostname)
        #command = '(?P<command>[a-zA-Z]+|\d\d\d)'
        #params  = '(?P<params>.*)'

        #message_pattern = '%s%s +%s' % (prefix, command, params)

        #if match = re.match(message_pattern, message):
        #    return match.groupdict()

        # FIXME: is this good enough for servers???

        # TODO: prefix MUST be ignored from clients
        prefix = None
        match = re.match(':([^ ]+) +', message)
        if match:
            prefix  = match.groups()[0]
            message = message[match.end():]

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

        return (prefix, command, params)

    def dispatch(self, msg):
        prefix, command, args = self.parse(msg)
        self.server.logger.debug('received from %s: prefix=%s ' \
                                 'command=%s args=%s',
                                 self.nick, prefix, command, args)

        if command == 'PASS':
            pass
            #TODO password hashing
        elif command == 'NICK' and not isinstance(self.handler, IrcServer):
            self.cmd_nick(args)
        elif command == 'USER':
            self.cmd_user(args)
        elif command == 'SERVER' and self.handler is None:
            self.cmd_server(args)
        else:
            if self.handler is not None:
                self.handler.cmd(prefix, command, args)
            else:
                format_str = "Command %s was sent before USER or SERVER: %s"
                self.server.logger.error(format_str,
                                         command,
                                         msg)

    def cmd_nick(self, args):
        # TODO: err irc.ERR_UNAVAILRESOURCE
        if not len(args):
            self.reply(irc.ERR_NONICKNAMEGIVEN)
            return

        # TODO: validate nickname (irc.ERR_ERRONEUSNICKNAME)

        nick = args[0]
        if nick in self.server.clients:
            self.reply(irc.ERR_NICKNAMEINUSE, nickname=nick)
            return

        # TODO: nickname collision (irc.ERR_NICKCOLLISION) multiple server stuff

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
            self.reply(irc.ERR_NEEDMOREPARAMS, command='USER')
            return

        if self.registered:
            self.reply(irc.ERR_ALREADYREGISTRED)

        user = args[0]
        mode = args[1]
        realname = args[3]
        self.user = user, mode, realname

        self.has_user = True
        if self.has_nick:
            self.register()

    def cmd_server(self, args):
        if len(args) != 4:
            self.reply(irc.ERR_NEEDMOREPARAMS, command='SERVER')

        servername, hopcount, token, info = args
        self.server.logger.info("Registered server connection %s", servername)
        self.nick = servername
        self.registered = True
        self.handler = IrcServer(self, self.server)
        self.server.servers[self.nick] = self.handler
        self.handler.hopcount = int(hopcount)
        self.handler.token = token
        self.handler.info = info
        # inform new connection of current network
        self.raw_send("PASS %s\r\n" % 'password')
        message = "SERVER %s %d %s :%s\r\n"
        self.raw_send(message % (self.server.name,
                                 1,
                                 self.server.token,
                                 "test info"))
        for name, server in self.server.servers.items():
            if self.handler is server:
                continue
            self.raw_send(message % (name,
                                     server.hopcount + 1,
                                     server.token,
                                     server.info))
            for neighbor_name, neighbor in server.neighbors.items():
                self.raw_send(message % (neighbor_name,
                                         neighbor.hopcount +1,
                                         neighbor.token,
                                         neighbor.info))

        for client in self.server.clients.values():
            self.raw_send(self.server_nick_message(client))

    def server_nick_message(self, client):
        return 'NICK {nick} {hopcount} {username} {host} ' \
               '{servertoken} {umode} :{realname}\r\n'.format(
                    nick=client.nick(), hopcount=client.hopcount(),
                    username=client.username(), host=client.host(),
                    realname=client.realname(),
                    servertoken=client.servertoken(), umode='+i')

    def register(self):
        # TODO? write a nick-changing method that checks for this nick
        # (race condition?)
        self.registered = True
        self.reply(irc.RPL_WELCOME,
                   nick=self.nick,
                   user=self.user[0],
                   host=self.host)
        self.reply(irc.RPL_YOURHOST,
                   server=self.server.name,
                   version=self.server.version)
        self.reply(irc.RPL_CREATED,
                   launched=self.server.launched)
        self.reply(irc.RPL_MYINFO,
                   server=self.server.name,
                   version=self.server.version,
                   user_modes=irc.mode_str(self.server.user_modes),
                   channel_modes=irc.mode_str(self.server.channel_modes))
        self.handler = IrcClient(self, self.server)
        self.server.clients[self.nick] = self.handler

        msg = 'NICK {nick} {hopcount} {username} {host} ' \
              '{servertoken} {umode} :{realname}\r\n'.format(
                  nick=self.nick, hopcount=0, username=self.user[0],
                  host=self.user[1], servertoken=self.server.token, umode='+i',
                  realname=self.user[2])
        for server in self.server.servers.values():
            server.connection.raw_send(msg)

    def _err_need_more_params(self, command):
        self.reply(irc.ERR_NEEDMOREPARAMS,
                   '%s :Not enough parameters' % command)

    def reply(self, code, **format_args):
        name, message = irc.IRC_CODE[code]
        formatted_message = message % format_args
        msg = '%s %03d %s %s\n' % (self.server.prefix(),
                                   code,
                                   self.nick or "*",
                                   formatted_message)
        self.server.logger.debug("sent %s to %s", name, self.nick)
        self.raw_send(msg)

    def raw_send(self, message):
        self.server.logger.debug("sent to %s: '%s'",
                                 self.nick,
                                 message.rstrip("\r\n"))
        self.out_buffer += message.encode()

    def readable(self):
        return True

    def writable(self):
        return (len(self.out_buffer) > 0)

    def _host(self):
        return self.getsockname()[0]

    def __repr__(self):
        return "<IrcClient: nick=%s registered=%s user=%s>" % \
            (repr(self.nick), repr(self.registered), repr(self.user))
