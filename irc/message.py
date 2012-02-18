import irc

class IrcClientMessageMixin:
    def helper_not_in_channel(self, channel_name):
        self.server.logger.debug("Topic request from nick %s "+ \
                                     "not a member of channel %s",
                                 self.connection.nick,
                                 channel_name)
        self.connection._send(irc.ERR_NOTONCHANNEL,
                              "%s :You're not on that channel",
                              channel_name)

    def helper_ban_list(self, channel_name, channel):
        for mask in channel.ban_masks:
            self.connection._send(irc.RPL_BANLIST, "%s %s", channel_name, mask)
        self.connection._send(irc.RPL_ENDOFBANLIST,
                              "%s :End of channel ban list", channel_name)

    def helper_exception_list(self, channel_name, channel):
        for mask in channel.exception_masks:
            self.connection._send(irc.RPL_EXCEPTLIST, "%s %s", channel_name, mask)
        self.connection._send(irc.RPL_ENDOFEXCEPTLIST,
                              "%s :End of channel exception list", channel_name)

    def helper_invite_list(self, channel_name, channel):
        for mask in channel.invite_masks:
            self.connection._send(irc.RPL_BANLIST, "%s %s", channel_name, mask)
        self.connection._send(irc.RPL_ENDOFBANLIST,
                              "%s :End of channel invite list", channel_name)


    def helper_not_in_channel(self, nick, channel):
        self.connection._send(irc.ERR_USERNOTINCHANNEL,
                              "%s %s :They aren't on that channel",
                              nick, channel)

    def helper_chan_op_privs_needed(self, channel):
        self.connection._send(irc.ERR_CHANOPRIVSNEEDED,
                              "%s :You're not channel operator", channel)

    def prefix(self):
        nick = self.connection.nick
        username = self.connection.user[0]
        host = self.connection.getsockname()[0]
        return ":%s!%s@%s" % (nick, username, host)
