import irc

class IrcClient:
    def __init__(self, connection, server):
        self.server = server
        self.connection = connection

    def cmd_user(self, args):
        if len(args) < 4:
            self.connection._err_need_more_params(command)
            return

        if self.connection.registered:
            self.connection._send(irc.ERR_ALREADYREGISTRED, ':Unauthorized command (already registered)')

        user = args[0]
        mode = args[1]
        realname = str.join(" ", args[3:]) # NOTE: real command parser will fix this

        self.user = user, mode, realname

        # TODO? write a nick-changing method that checks for this nick (race condition?)
        self.server.clients[self.connection.nick] = self
        self.connection.registered = True
        self.connection._send(irc.RPL_WELCOME, 'Welcome to the Internet Relay Network %s' % self.connection.nick)
        self.connection._send(irc.RPL_YOURHOST, 'Your host is FIXME, running version FIXME')
        self.connection._send(irc.RPL_CREATED, 'This server was created FIXME')
        self.connection._send(irc.RPL_MYINFO, 'FIXMEservername FIXMEversion FIXMEusemodes FIXMEchannelmodes')
            
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
        
        if self.connection.registered:
            del self.server[self.connection.nick]

        # TODO: send error message (see RFC)
        self.connection.close()

    def cmd(self, command, args):
        self.server.logger.warning("Unimplemented command %s with args %s",
                                   command,
                                   args)

class IrcServer:
    def cmd_server(self, args):
        pass
