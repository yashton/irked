import os.path
import re
import time
import irc
from irc.message import IrcClientMessageMixin

class IrcClient(IrcClientMessageMixin):
    def __init__(self, connection, server):
        self.server = server
        self.connection = connection
        self.modes = dict()
        for i in irc.IRC_MODES:
            self.modes[i] = False

    def cmd_user(self, args):
        if len(args) < 4:
            self.connection._send(irc.ERR_NEEDMOREPARAMS, command='USER')
            return

        if self.connection.registered:
            self.connection._send(irc.ERR_ALREADYREGISTRED)

        user = args[0]
        mode = args[1]
        realname = args[3]
        self.connection.user = user, mode, realname

        # TODO? write a nick-changing method that checks for this nick (race condition?)
        self.server.clients[self.connection.nick] = self
        self.connection.registered = True
        self.connection._send(irc.RPL_WELCOME,
                              nick=self.connection.nick,
                              user=self.connection.user[0],
                              host=self.connection.host)
        self.connection._send(irc.RPL_YOURHOST,
                              server=self.server.name,
                              version=self.server.version)
        self.connection._send(irc.RPL_CREATED,
                              launched=self.server.launched)
        self.connection._send(irc.RPL_MYINFO,
                              server=self.server.name,
                              version=self.server.version,
                              user_modes=irc.mode_str(self.server.user_modes),
                              channel_modes=irc.mode_str(self.server.channel_modes))

        self.cmd_motd(list())

    def cmd_motd(self, args):
        #TODO Need to fetch motd from other servers.
        if (not os.path.isfile(self.server.motd)):
            self.connection._send(irc.ERR_NOMOTD)
            return
        self.connection._send(irc.RPL_MOTDSTART, server=self.server.name)
        motd = open(self.server.motd)
        for line in motd:
            self.connection._send(irc.RPL_MOTD, motd_line=line)
        self.connection._send(irc.RPL_ENDOFMOTD)

    def cmd_join(self, args):
        # TODO: support multiple channels at once
        # TODO: support leaving all channels ('0')
        # TODO: support keys
        channel = args[0]

        if len(args) == 0:
            self.connection._send(irc.ERR_NEEDMOREPARAMS, command='JOIN')
            return

        if args[0] =="0":
            for channel in self.server.channels.values():
                channel.remove(self)
            return

        channels = re.split(",", args[0])
        for channel in channels:
            if channel not in self.server.channels:
                self.server.channel_add(channel, self)
            self.server.channels[channel].add(self)

    def cmd_part(self, args):
        if len(args) == 0:
            self.connection._send(irc.ERR_NEEDMOREPARAMS, command='PART')

        channels = re.split(",", args[0])

        part_message = None
        if len(args) == 2:
            part_message = args[1]

        for channel in channels:
            self.server.channels[channel].remove(self, part_message)

    def cmd_time(self, args):
        # TODO: multi-server stuff
        self.connection._send(irc.RPL_TIME,
                              server=self.server.name,
                              time=time.asctime(time.localtime()))

    def cmd_quit(self, args):
        to_notify = set({self})
        to_leave = set()
        for channel in self.server.channels.values():
            if self in channel.clients:
                to_leave.add(channel)
                to_notify |= channel.clients

        if len(args):
            message = '%s QUIT :%s\r\n' % (self.prefix(), args[0])
            err_msg = 'ERROR :Closing Link: %s (%s)\r\n' % (self.prefix(), args[0])
        else:
            message = '%s QUIT\r\n' % self.prefix()
            err_msg = 'ERROR :Closing Link: %s\r\n' % self.prefix()

        for client in to_notify:
            client.connection.raw_send(message)

        for channel in to_leave:
            channel.remove(self, parted = False)

        self.server.connections.remove(self.connection)
        del self.server.clients[self.connection.nick]

        # send error message (see RFC)
        self.connection.raw_send(err_msg)
        self.connection.close()

    def cmd_topic(self, args):
        self.server.logger.debug("TOPIC args: %s", args)
        if len(args) == 0:
            self.connection._send(irc.ERR_NEEDMOREPARAMS, command='TOPIC')
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
                                      channel=channel_name)
            else:
                self.connection._send(irc.RPL_TOPIC,
                                      channel=channel_name, topic=channel.topic)

    def cmd_list(self, args):
        # TODO: server target

        # TODO: this probably needs to support some channel mode stuff
        if len(args):
            names = re.split(",", args[0])
            channels = [self.server.channels[n] for n in names if n in self.server.channels]
        else:
            channels = self.server.channels.values()

        for channel in channels:
            self.connection._send(irc.RPL_LIST,
                                  channel=channel.name,
                                  visible=len(channel.clients), # need to check visibility here
                                  topic=channel.topic or "")
        self.connection._send(irc.RPL_LISTEND)

    def cmd_kick(self, args):
        """ KICK command, rfc2812 3.2.8 """

        # TODO: channel can be a chanmask

        if len(args) < 2:
            self.connection._send(irc.ERR_NEEDMOREPARAMS, command="KICK")
            return

        chan_list, user_list = args[0:2]

        channels = re.split(",", chan_list)
        users = re.split(",", user_list)

        # according to the RFC, there must be one channel and multiple users,
        # or an equal number of channels and users.  There is no error response
        # for invalid messages though, so I'm just going to truncate the input
        if len(channels) != 1 and len(channels) != len(users):
            channels = channels[0]

        comment = None
        if len(args) > 2:
            comment = args[2]

        if len(channels) == 1:
            channel = self.server.channels[channels[0]]
            if not channel:
                self.connection._send(irc.ERR_NOSUCHCHANNEL,
                                      channel=channels[0])
                return
            for user in users:
                channel.kick(self, user, comment)
        else:
            pass # TODO

    def cmd_privmsg(self, args):
        if len(args) == 0:
            self.connection._send(irc.ERR_NORECIPIENT, command='JOIN')
            return
        if len(args) == 1:
            self.connection._send(irc.ERR_NOTEXTTOSEND)
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

    def cmd_ping(self, args):
        # TODO: multi-server stuff
        if not len(args):
            self.connection._send(irc.ERR_NEEDMOREPARAMS, command='PING')
        target = args[0]

        self.connection.raw_send("%s PONG :%s\r\n" %
                                 (self.server.prefix(), target))

    def cmd_away(self, args):
        # not implementing this for now (it's an optional feature)
        self.connection._send(irc.RPL_UNAWAY)

    def cmd_mode(self, args):
        if not len(args) > 0:
            self.connection._send(irc.ERR_NEEDMOREPARAMS, command='MODE')
            return
        target = args[0]
        if irc.is_channel_name(target):
            self.cmd_chan_mode(target, args[1:])
        else:
            self.cmd_user_mode(target, args[1:])

    def cmd_user_mode(self, target, args):
        if target != self.connection.nick:
            self.connection._send(irc.ERR_USERSDONTMATCH)
            return
        if len(args) == 0:
            self.connection._send(irc.RPL_UMODEIS, mode=irc.mode_str(self.modes))
            return
        op, flag = args[0]
        if not (flag in irc.IRC_USER_MODES and (op != '+' or op != '-')) or args[0] == '+o':
            self.connection._send(irc.ERR_UMODEUNKNOWNFLAG)
            return
        self.modes[flag] = op == "+"

    def cmd_chan_mode(self, target, args):
        self.server.logger.debug("MODE channel %s: %s", target, args)
        channel = self.server.channels[target]
        if channel.modes is None:
            self.connection._send(irc.ERR_NOCHANMODES, channel=target)
        #TODO Only handling single mode changes
        if len(args) == 0:
            modes = channel.modes.user_mode(self.connection.nick)
            self.connection._send(irc.RPL_CHANNELMODEIS,
                                  channel=self.connection.nick, mode=target, params=modes)
        elif len(args) == 1:
            if self not in channel.modes.operators:
                self.helper_chan_op_privs_needed(target)
                return
            command = args[0]
            if command == '+a' or command == '-a':
                channel.modes.anonymous = command[0] == '+'
            elif command == '+m' or command == '-m':
                channel.modes.moderated = command[0] == '+'
            elif command == '+i' or command == '-i':
                channel.modes.invite = command[0] == '+'
            elif command == '+n' or command == '-n':
                channel.modes.no_message = command[0] == '+'
            elif command == '+p' or command == '-p':
                channel.modes.private = command[0] == '+'
            elif command == '+s' or command == '-s':
                channel.modes.secret = command[0] == '+'
            elif command == '+r' or command == '-r':
                if target[0] == '!':
                    channel.modes.reop = command[0] == '+'
            elif command == '+t' or command == '-t':
                channel.modes.topic = command[0] == '+'
            elif command == '-l':
                channel.modes.limit = None
            elif command == '-k':
                channel.modes.key = None
            elif command == '+b':
                self.helper_ban_list(target, channel)
            elif command == '+e':
                self.helper_exception_list(target, channel)
            elif command == '+I':
                self.helper_invite_list(target, channel)
            elif command == 'O':
                self.connection._send(irc.RPL_UNIQOPIS,
                                      channel=target, nickname=channel.modes.creator.connection.nick)
            else:
                self.connection._send(irc.ERR_UNKNOWNMODE,
                                      mode=command, channel=target)
        elif len(args) == 2:
            if self not in channel.modes.operators:
                self.helper_chan_op_privs_needed(target)
                return
            command, param = args
            if command == '+k':
                if channel.modes.key is None:
                    channel.modes.key = param
                else:
                    self.connection._send(irc.ERR_KEYSET,
                                          channel=target)
            elif command == '+l':
                channel.limit = int(param)
            elif command == '+o' or command == '-o':
                client = self.server.clients[param]
                if client not in channel.clients:
                    self.helper_not_in_channel(param, target)
                else:
                    if command[0] == '+':
                        channel.modes.operators.add(client)
                    else:
                        try:
                            channel.modes.operators.remove(client)
                        except KeyError:
                            pass
            elif command == '+v' or command == '-v':
                client = self.server.clients[param]
                if client not in channel.clients:
                    self.helper_not_in_channel(param, target)
                else:
                    if command[0] == '+':
                        channel.modes.voice.add(client)
                    else:
                        try:
                            channel.modes.voice.remove(client)
                        except KeyError:
                            pass
            elif command == '+I' or command == '-I':
                if command[0] == '+':
                    channel.invite_masks.add(param)
                else:
                    try:
                        channel.invite_masks.remove(param)
                    except KeyError:
                        pass
            elif command == '+b' or command == '-b':
                if command[0] == '+':
                    channel.ban_masks.add(param)
                else:
                    try:
                        channel.ban_masks.remove(param)
                    except KeyError:
                        pass
            elif command == '+e' or command == '-e':
                if command[0] == '+':
                    channel.exception_masks.add(param)
                else:
                    try:
                        channel.exception_masks.remove(param)
                    except KeyError:
                        pass
        else:
            self.connection._send(irc.ERR_NEEDMOREPARAMS, command='MODE')

    def cmd_oper(self, args):
        if len(args) != 2:
            self.connection._send(irc.ERR_NEEDMOREPARAMS, command='OPER')
            return
        username, password = args
        if not self.server.allows_oper():
            self.connection._send(irc.ERR_NOOPERHOST)
            return
        if not self.server.is_valid_oper_pass(username, password):
            self.connection._send(irc.ERR_PASSWDMISMATCH)
            return
        self.modes['o'] = True
        self.connection._send(irc.RPL_YOUREOPER)
        self.connection._send(irc.RPL_UMODEIS, mode=irc.mode_str(self.modes))


    def cmd_invite(self, args):
        '''Implements RCF 2812 Section 3.2.7 and RFC 1459 Section 4.2.7'''
        if len(args) != 2:
            self.connection._send(irc.ERR_NEEDMOREPARAMS, command='INVITE')
            return
        nickname, channel_name = args
        if nickname not in self.server.clients:
            self.connection._send(irc.ERR_NOSUCHNICK, nickname=nickname)
            return
        target = self.server.clients[nickname]
        # (irc.RPL_AWAY, '%s :%s', nickname, away_message)
        if channel_name in self.server.channels:
            channel = self.server.channels[channel_name]
            if self not in channel.clients:
                self.connection._send(irc.ERR_NOTONCHANNEL,
                                      channel_name=channel_name)
                return
            elif target in channel.clients:
                self.connection._send(irc.ERR_USERONCHANNEL,
                                      nickname=nickname, channel=channel_name)
                return
            elif channel.modes.invite and self not in channel.modes.operators:
                self.connection._send(irc.ERR_CHANOPRIVSNEEDED,
                                      channel=channel_name)
                return
        self.connection._send(irc.RPL_INVITING, nickname=nickname, channel=channel_name)
        target.connection._send(irc.RPL_INVITING, nickname=nickname, channel=channel_name)

    def cmd_lusers(self, args):
        '''Implements RFC 2812 Section 3.4.2'''
        users = len(self.server.clients)
        services = len(self.server.services)
        servers = len(self.server.servers) + 1
        clients = users + services
        unknowns = len(self.server.connections) + 1 - clients - servers
        opers = len([i for i in self.server.clients.values() if i.modes['o']])
        channels = len(self.server.channels)
        self.connection._send(irc.RPL_LUSERCLIENT,
                              users=users, services=services, servers=servers)
        self.connection._send(irc.RPL_LUSERME,
                              clients=clients, servers=(servers-1))
        if opers > 0:
            self.connection._send(irc.RPL_LUSEROP, opers=opers)
        if unknowns > 0:
            self.connection._send(irc.RPL_LUSERUNKNOWN, unknown=unknowns)
        if channels > 0:
            self.connection._send(irc.RPL_LUSERCHANNELS, channels=channels)
        if len(args) > 0:
            #TODO Multi server info
            server_name = args[0]
            self.connection._send(irc.ERR_NOSUCHSERVER, server=server_name)

    def cmd_version(self, args):
        if len(args) > 0:
            #TODO Multi server info
            server_name = args[0]
            self.connection._send(irc.ERR_NOSUCHSERVER, server=server_name)
            return
        version = self.server.version
        comment = self.server.version_comment
        debug = self.server.logger.getEffectiveLevel()
        server = self.server.name
        self.connection._send(irc.RPL_VERSION,
                              version=version,
                              debug=debug,
                              server=server,
                              comment=comment)

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
