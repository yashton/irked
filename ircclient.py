import os.path
import irc

class IrcClient:
    def __init__(self, connection, server):
        self.server = server
        self.connection = connection

    def cmd_user(self, args):
        if len(args) < 4:
            self.connection._err_need_more_params('USER')
            return

        if self.connection.registered:
            self.connection._send(irc.ERR_ALREADYREGISTRED, ':Unauthorized command (already registered)')

        user = args[0]
        mode = args[1]
        realname = str.join(" ", args[3:]) # NOTE: real command parser will fix this

        self.connection.user = user, mode, realname

        # TODO? write a nick-changing method that checks for this nick (race condition?)
        self.server.clients[self.connection.nick] = self
        self.connection.registered = True
        self.connection._send(irc.RPL_WELCOME, 'Welcome to the Internet Relay Network %s!%s@%s',
                              self.connection.nick,
                              self.connection.user[0],
                              self.connection.host)
        self.connection._send(irc.RPL_YOURHOST, 'Your host is %s, running version %s',
                              self.server.name,
                              self.server.version)
        self.connection._send(irc.RPL_CREATED, 'This server was created %s',
                              self.server.launched)
        self.connection._send(irc.RPL_MYINFO, '%s %s %s %s',
                              self.server.name,
                              self.server.version,
                              self.server.usermodes,
                              self.server.channelmodes)

        self.cmd_motd(list())

    def cmd_motd(self, args):
        #TODO Need to fetch motd from other servers.
        if (not os.path.isfile(self.server.motd)):
            self.connection._send(irc.ERR_NOMOTD, ":MOTD File is missing")
            return
        self.connection._send(irc.RPL_MOTDSTART, ":- %s Message of the day - " % self.server.name)
        motd = open(self.server.motd)
        for line in motd:
            self.connection._send(irc.RPL_MOTD, ":- %s" % line)
        self.connection._send(irc.RPL_ENDOFMOTD, ":End of MOTD command")

    def cmd_join(self, args):
        # TODO: support multiple channels at once
        # TODO: support leaving all channels ('0')
        # TODO: support keys
        channel = args[0]

        if channel not in self.server.channels:
            self.server.channel_add(channel)
        self.server.channels[channel].add(self)

    def cmd_quit(self, args):
        self.server.clients.remove(self)
        
        # TODO: notify relevant servers/clients
        
        if self.connection.registered:
            del self.server[self.connection.nick]

        # TODO: send error message (see RFC)
        self.connection.close()

    def cmd(self, command, args):
        if command == 'MOTD':
            self.cmd_motd(args)
        elif command == 'JOIN':
            self.cmd_join(args)
        else:
            self.server.logger.warning("Unimplemented command %s with args %s",
                                       command,
                                       args)
    def prefix(self):
        return ":%s" % self.connection.nick

class IrcServer:
    def cmd_server(self, args):
        pass
