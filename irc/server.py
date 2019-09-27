from irc.channel import Channel
import re
import pdb

#
# handles logic and stores data for connections to other servers in the network
#
class IrcServer:
    hopcount = 1
    info = None
    token = None
    neighbors = None

    def __init__(self, connection, server):
        self.connection = connection
        self.server = server
        self.neighbors = dict()

    def cmd_server(self, prefix, args):
        '''Implements RFC 2813 section 4.1.2 for server topology notifications'''
        servername, hopcount, token, info = args
        circular = False
        for server, handler in self.server.servers.items():
            if servername == server:
                return
            if servername in handler.neighbors:
                circular = True
                break
        if circular:
            info = "Circular server connection created." + \
                ("Disconnecting %s" % self.connection.nick)
            self.server.squit(self.connection.nick, info)

        self.neighbors[servername] = RemoteIrcServer(*args)
        message = "SERVER %s %d %s :%s" % (servername,
                                           int(hopcount)+1,
                                           token,
                                           info)
        for server in self.server.servers.values():
            if server is self:
                continue
            server.connection.raw_send(message)

    def cmd_join(self, prefix, args):
        # TODO
        # - netsplit on disagreements
        channel_name = args[0]
        if channel_name not in self.server.channels:
            self.server.channels[channel_name] = Channel(channel_name,
                                                         self.server)
        channel = self.server.channels[channel_name]

        client = self._client(prefix)
        if client:
            channel.add(client)

    def cmd_privmsg(self, prefix, args):
        # TODO
        # - support modes other than sending to channel
        channel, message = args
        sender = self._client(prefix)

        self.server.channels[channel].privmsg(sender, message)

    def cmd_part(self, prefix, args):
        channel_name = args[0]
        if channel_name not in self.server.channels:
            return
        channel = self.server.channels[channel_name]

        client = self._client(prefix)
        if client:
            channel.remove(client)

    def cmd_nick(self, prefix, args):
        if len(args) == 1:
            # TODO: support nick changes too
            pass
        else:
            nickname, hopcount, username, host, \
                servertoken, umode, realname = args
            client = RemoteClient(nickname, hopcount, servertoken, umode,
                                  username, host, realname)
            # FIXME: check for collisions and split if you get one
            self.server.clients[nickname] = client

    def cmd_quit(self, prefix, args):
        match = re.match('[^!]+', prefix)
        if match:
            nick = match.group()
            del self.server.clients[nick]

    def _client(self, prefix):
        match = re.match('[^!]+', prefix)
        if match:
            nick = match.group()
            return self.server.clients[nick]

    def cmd(self, prefix, command, args):
        try:
            cmd = getattr(self, 'cmd_%s' % command.lower())
        except AttributeError as err:
            self.server.logger.warning("Unimplemented command %s with args %s",
                                       command,
                                       args)
            return
        cmd(prefix, args)

    def notify_channel(self, channel_name, message, *format_args):
        # TODO
        # - don't just make up channels here (edit channel_add)
        if channel_name not in self.server.channels:
            self.server.channels[channel_name] = Channel(channel_name,
                                                         self.server)
        else:
            channel = self.server.channels[channel_name]
            for client in channel.clients:
                client.connection.raw_send(('%s\r\n' % message) % format_args)

    def netsplit(self, other):
        for client in other.server.clients:
            for quitting_client in self.server.clients:
                client.raw_send('%s QUIT :%s %s' % (quitting_client.prefix(),
                    other.server.name, self.server.name))

# represents a server in the IRC Network
class RemoteIrcServer:
    def __init__(self, name, hopcount, token, info):
        self.name = name
        self.hopcount = int(hopcount)
        self.token = token
        self.info = info
        self.fqdn="unknown"

# represents a client connected to a remote server
class RemoteClient:
    def __init__(self, nick, hopcount, server_token, mode,
                 username, host, realname):
        self.nickname = nick
        self.hop_count = hopcount
        self.server_token = server_token
        self.mode = mode
        self.user = (username, host, realname)
        self.connection = None

    def nick(self):
        return self.nickname

    def hopcount(self):
        return self.hop_count

    def username(self):
        return self.user[0]

    def host(self):
        return self.user[1]

    def realname(self):
        return self.user[2]

    def servertoken(self):
        return self.server_token

    def prefix(self):
        return ':%s!%s@%s' % (self.nick(), self.username(), self.host())

    def is_op(self):
        return self.mode.find("o") > -1

    def rpl_whoami(self, requester):
        # TODO: move this junk somewhere so it can be shared with the irc/client
        # version
        requester.connection.reply(irc.RPL_WHOISUSER,
                nick=self.nick, user=self.user[0], host=self.user[1],
                realname=self.user[3])
