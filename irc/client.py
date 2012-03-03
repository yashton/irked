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

        self.cmd_motd(list())

    def cmd_motd(self, args):
        #TODO Need to fetch motd from other servers.
        if (not os.path.isfile(self.server.motd)):
            self.connection.reply(irc.ERR_NOMOTD)
            return
        self.connection.reply(irc.RPL_MOTDSTART, server=self.server.name)
        motd = open(self.server.motd)
        for line in motd:
            self.connection.reply(irc.RPL_MOTD, motd_line=line.rstrip())
        self.connection.reply(irc.RPL_ENDOFMOTD)

    def cmd_join(self, args):
        # TODO: support keys
        if len(args) == 0:
            self.connection.reply(irc.ERR_NEEDMOREPARAMS, command='JOIN')
            return

        if args[0] == "0":
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
            self.connection.reply(irc.ERR_NEEDMOREPARAMS, command='PART')

        channels = re.split(",", args[0])

        part_message = None
        if len(args) == 2:
            part_message = args[1]

        for channel in channels:
            self.server.channels[channel].remove(self, part_message)

    def cmd_time(self, args):
        # TODO: multi-server stuff
        self.connection.reply(irc.RPL_TIME,
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
            err_msg = 'ERROR :Closing Link: %s (%s)\r\n' % \
                (self.prefix(), args[0])
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
            self.connection.reply(irc.ERR_NEEDMOREPARAMS, command='TOPIC')
        channel_name = args[0]

        if channel_name not in self.server.channels:
            self.connection.reply(irc.ERR_NOSUCHCHANNEL, channel=channel_name)
            return

        channel = self.server.channels[channel_name]
        self.server.logger.debug("Topic request for %s: %s",
                                 channel_name, channel.topic)

        if len(args) > 1:
            channel.set_topic(self, args[1])
        else:
            channel.rpl_topic(self)

    def cmd_list(self, args):
        # TODO: server target

        # TODO: this probably needs to support some channel mode stuff
        if len(args):
            names = re.split(",", args[0])
            channels = [self.server.channels[n] for n in names
                        if n in self.server.channels]
        else:
            channels = self.server.channels.values()

        for channel in channels:
            # need to check visibility here
            self.connection.reply(irc.RPL_LIST,
                                  channel=channel.name,
                                  visible=len(channel.clients),
                                  topic=channel.topic or "")
        self.connection.reply(irc.RPL_LISTEND)

    def cmd_kick(self, args):
        """ KICK command, rfc2812 3.2.8 """

        # TODO: channel can be a chanmask

        if len(args) < 2:
            self.connection.reply(irc.ERR_NEEDMOREPARAMS, command="KICK")
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
                self.connection.reply(irc.ERR_NOSUCHCHANNEL,
                                      channel=channels[0])
                return
            for user in users:
                channel.kick(self, user, comment)
        else:
            pass # TODO

    def cmd_privmsg(self, args):
        if len(args) == 0:
            self.connection.reply(irc.ERR_NORECIPIENT, command='JOIN')
            return
        if len(args) == 1:
            self.connection.reply(irc.ERR_NOTEXTTOSEND)
            return

        target, text = args[0:2]

        # TODO: need to check channel modes to see if sending is allowed
        if re.match('#', target):
            if target not in self.server.channels:
                self.connection.reply(irc.ERR_NOSUCHNICK, nick=target)
                return
            self.server.channels[target].privmsg(self, text)
        else:
            # TODO, nick/etc messaging
            pass

    def cmd_ping(self, args):
        # TODO: multi-server stuff
        if not len(args):
            self.connection.reply(irc.ERR_NEEDMOREPARAMS, command='PING')
            return
        target = args[0]

        self.connection.raw_send("%s PONG :%s\r\n" %
                                 (self.server.prefix(), target))

    def cmd_who(self, args):
        # TODO: who can take a mask, but we're just supporting channels for now
        # (pidgin needs this to join a channel)
        if not len(args):
            self.connection.reply(irc.ERR_NEEDMOREPARAMS, command='WHO')
            return

        channel = args[0] # TODO
        ops_only = False  # TODO
        if len(args) > 1 and args[1] == "o":
            ops_only = True

        # TODO: respect modes (like +i)
        if channel in self.server.channels:
            self.server.channels[channel].rpl_who(self)
        self.connection.reply(irc.RPL_ENDOFWHO)

    def cmd_away(self, args):
        # not implementing this for now (it's an optional feature)
        self.connection.reply(irc.RPL_UNAWAY)

    def cmd_mode(self, args):
        if not len(args) > 0:
            self.connection.reply(irc.ERR_NEEDMOREPARAMS, command='MODE')
            return
        target = args[0]
        if irc.is_channel_name(target):
            self.cmd_chan_mode(target, args[1:])
        else:
            self.cmd_user_mode(target, args[1:])

    def cmd_user_mode(self, target, args):
        if target != self.connection.nick:
            self.connection.reply(irc.ERR_USERSDONTMATCH)
            return
        if len(args) == 0:
            self.connection.reply(irc.RPL_UMODEIS,
                                  mode=irc.mode_str(self.modes))
            return
        op, flag = args[0]
        if not (flag in irc.IRC_USER_MODES and (op != '+' or op != '-')) \
           or args[0] == '+o':
            self.connection.reply(irc.ERR_UMODEUNKNOWNFLAG)
            return
        self.modes[flag] = op == "+"

    def cmd_chan_mode(self, target, args):
        self.server.logger.debug("MODE channel %s: %s", target, args)

        if target not in self.server.channels:
            self.connection.reply(irc.ERR_NOSUCHCHANNEL, channel=target)
            return
        channel = self.server.channels[target]

        if len(args) == 0:
            modes = channel.modes.mode_string()
            mode_params = '' # we don't support any mode params right now
            self.connection.reply(irc.RPL_CHANNELMODEIS,
                    channel=target, modes=modes, params=mode_params)
            return

        # TODO: support setting all modes at once
        match = re.match('([-+])([a-zA-Z])(?: +)?(.*)', args[0])
        if not match:
            return

        op, mode, params = match.groups()
        to_add = op == '+'
        mode_changed = channel.modes.set(mode, to_add, params)
        if mode_changed:
            channel._send(self,
                    'MODE %s %s%s %s' % (target, op, mode, params))

    def cmd_oper(self, args):
        if len(args) != 2:
            self.connection.reply(irc.ERR_NEEDMOREPARAMS, command='OPER')
            return
        username, password = args
        if not self.server.allows_oper():
            self.connection.reply(irc.ERR_NOOPERHOST)
            return
        if not self.server.is_valid_oper_pass(username, password):
            self.connection.reply(irc.ERR_PASSWDMISMATCH)
            return
        self.modes['o'] = True
        self.connection.reply(irc.RPL_YOUREOPER)
        self.connection.reply(irc.RPL_UMODEIS, mode=irc.mode_str(self.modes))


    def cmd_invite(self, args):
        '''Implements RCF 2812 Section 3.2.7 and RFC 1459 Section 4.2.7'''
        if len(args) != 2:
            self.connection.reply(irc.ERR_NEEDMOREPARAMS, command='INVITE')
            return
        nickname, channel_name = args
        if nickname not in self.server.clients:
            self.connection.reply(irc.ERR_NOSUCHNICK, nickname=nickname)
            return
        target = self.server.clients[nickname]
        # (irc.RPL_AWAY, '%s :%s', nickname, away_message)
        if channel_name in self.server.channels:
            channel = self.server.channels[channel_name]
            if self not in channel.clients:
                self.connection.reply(irc.ERR_NOTONCHANNEL,
                                      channel_name=channel_name)
                return
            elif target in channel.clients:
                self.connection.reply(irc.ERR_USERONCHANNEL,
                                      nickname=nickname, channel=channel_name)
                return
            elif channel.modes.invite and self not in channel.modes.operators:
                self.connection.reply(irc.ERR_CHANOPRIVSNEEDED,
                                      channel=channel_name)
                return
        self.connection.reply(irc.RPL_INVITING,
                              nickname=nickname,
                              channel=channel_name)
        target.connection.reply(irc.RPL_INVITING,
                                nickname=nickname,
                                channel=channel_name)

    def cmd_lusers(self, args):
        '''Implements RFC 2812 Section 3.4.2'''
        users = len(self.server.clients)
        services = len(self.server.services)
        servers = len(self.server.servers) + 1
        clients = users + services
        unknowns = len(self.server.connections) + 1 - clients - servers
        opers = len([i for i in self.server.clients.values() if i.modes['o']])
        channels = len(self.server.channels)
        self.connection.reply(irc.RPL_LUSERCLIENT,
                              users=users, services=services, servers=servers)
        self.connection.reply(irc.RPL_LUSERME,
                              clients=clients, servers=(servers-1))
        if opers > 0:
            self.connection.reply(irc.RPL_LUSEROP, opers=opers)
        if unknowns > 0:
            self.connection.reply(irc.RPL_LUSERUNKNOWN, unknown=unknowns)
        if channels > 0:
            self.connection.reply(irc.RPL_LUSERCHANNELS, channels=channels)
        if len(args) > 0:
            #TODO Multi server info
            server_name = args[0]
            self.connection.reply(irc.ERR_NOSUCHSERVER, server=server_name)

    def cmd_version(self, args):
        if len(args) > 0:
            #TODO Multi server info
            server_name = args[0]
            self.connection.reply(irc.ERR_NOSUCHSERVER, server=server_name)
            return
        version = self.server.version
        comment = self.server.version_comment
        debug = self.server.logger.getEffectiveLevel()
        server = self.server.name
        self.connection.reply(irc.RPL_VERSION,
                              version=version,
                              debug=debug,
                              server=server,
                              comment=comment)

    def cmd_info(self, args):
        if len(args) > 0:
            server_name = args[0]
            self.connection.reply(irc.ERR_NOSUCHSERVER, server=server_name)
        for info in self.server.info():
            self.connection.reply(irc.RPL_INFO, info=info)
        self.connection.reply(irc.RPL_ENDOFINFO)

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
        return ":%s!%s@%s" % (nick, username, self.connection._host())

class IrcServer:
    def cmd_server(self, args):
        pass
