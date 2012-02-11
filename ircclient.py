import os.path
import re
import irc

class IrcClient:
    def __init__(self, connection, server):
        self.server = server
        self.connection = connection
        self.modes = dict()
        for i in irc.IRC_MODES:
            self.modes[i] = False

    def cmd_user(self, args):
        if len(args) < 4:
            self.connection._err_need_more_params('USER')
            return

        if self.connection.registered:
            self.connection._send(irc.ERR_ALREADYREGISTRED, ':Unauthorized command (already registered)')

        user = args[0]
        mode = args[1]
        realname = args[3]
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
                              irc.mode_str(self.server.user_modes),
                              irc.mode_str(self.server.channel_modes))

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

    def cmd_part(self, args):
        if len(args) == 0:
            self.connection._send(irc.ERR_NEEDMOREPARAMS,
                                  "PART :Not enough parameters")

        # TODO: support leaving multiple channels at once
        channel = args[0]

        part_message = None
        if len(args) == 2:
            part_message = args[1]

        self.server.channels[channel].remove(self, part_message)

    def cmd_quit(self, args):
        self.server.clients.remove(self)
        
        # TODO: notify relevant servers/clients
        
        if self.connection.registered:
            del self.server[self.connection.nick]

        # TODO: send error message (see RFC)
        self.connection.close()

    def cmd_topic(self, args):
        self.server.logger.debug("TOPIC args: %s", args)
        if len(args) == 0:
            self.connection._send(irc.ERR_NEEDMOREPARAMS,
                                  "TOPIC :Not enough parameters")
        channel_name = args[0]
        channel = self.server.channels[channel_name]
        self.server.logger.debug("Topic request for %s: %s",
                                 channel_name, channel.topic)
        if len(args) > 1:
            topic = args[1]
            self.server.logger.debug("Setting topic for %s: %s",
                                     channel_name, topic)
            # TODO permissions
            # ERR_CHANOPRIVSNEEDED            ERR_NOCHANMODES
            if self not in channel.clients:
                self.helper_not_in_channel(channel_name)
            else:
                channel.topic = topic
        else:
            # No topic parameter indicates a request for topic
            if self not in channel.clients:
                self.helper_not_in_channel(channel_name)
            elif channel.topic is None or channel.topic == '':
                self.server.logger.debug("No topic for %s", channel_name)
                self.connection._send(irc.RPL_NOTOPIC,
                                      "%s :No topic is set",
                                      channel_name)
            else:
                self.connection._send(irc.RPL_TOPIC, "%s :%s",
                                      channel_name, channel.topic)

    def cmd_privmsg(self, args):
        if len(args) == 0:
            self.connection._send(irc.ERR_NORECIPIENT,
                                  ':No recipient given (%s)',
                                  'JOIN')
            return
        if len(args) == 1:
            self.connection._send(irc.ERR_NOTEXTTOSEND, ':No text to send')
            return

        if len(args) != 2:
            # fail silently?
            pass

        target, text = args

        if re.match('#', target):
            self.server.notify_channel(target,
                    sender = self,
                    message = 'PRIVMSG %s :%s' % (target, text),
                    notify_sender = False)
        else:
            # TODO, nick/etc messaging
            pass

    def helper_not_in_channel(self, channel_name):
        self.server.logger.debug("Topic request from nick %s "+ \
                                     "not a member of channel %s",
                                 self.connection.nick,
                                 channel_name)
        self.connection._send(irc.ERR_NOTONCHANNEL,
                              "%s :You're not on that channel",
                              channel_name)

    def cmd_mode(self, args):
        if not len(args) > 0:
            self.connection._err_need_more_params('MODE')
            return
        target = args[0]
        if irc.is_channel_name(target):
            self.cmd_chan_mode(target, args[1:])
        else:
            self.cmd_user_mode(target, args[1:])

    def cmd_user_mode(self, target, args):
        if target != self.connection.nick:
            self.connection._send(irc.ERR_USERSDONTMATCH,
                                  ":Cannot change mode for other users")
            return
        if len(args) == 0:
            self.connection._send(irc.RPL_UMODEIS, irc.mode_str(self.modes))
            return
        op, flag = args[0]
        if not (flag in irc.IRC_USER_MODES and (op != '+' or op != '-')):
            self.connection._send(irc.ERR_UMODEUNKNOWNFLAG, ":Unknown MODE flag")
            return
        self.modes[flag] = op == "+"

    def cmd_chan_mode(self, target, args):
        self.server.logger.debug("MODE channel %s: %s", target, args)

    def cmd(self, command, args):
        try:
            cmd = getattr(self, 'cmd_%s' % command.lower())
        except AttributeError as err:
            self.server.logger.warning("Unimplemented command %s with args %s",
                                       command,
                                       args)
            return
        cmd(args)

    def prefix(self):
        nick = self.connection.nick
        username = self.connection.user[0]
        host = self.connection.getsockname()[0]
        return ":%s!%s@%s" % (nick, username, host)

class IrcServer:
    def cmd_server(self, args):
        pass
