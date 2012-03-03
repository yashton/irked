import irc

class IrcClientMessageMixin:
    def helper_ban_list(self, channel_name, channel):
        for mask in channel.ban_masks:
            self.connection.reply(irc.RPL_BANLIST,
                                  channel=channel_name, mask=mask)
        self.connection.reply(irc.RPL_ENDOFBANLIST,
                              channel=channel_name)

    def helper_exception_list(self, channel_name, channel):
        for mask in channel.exception_masks:
            self.connection.reply(irc.RPL_EXCEPTLIST,
                                  channel=channel_name, mask=mask)
        self.connection.reply(irc.RPL_ENDOFEXCEPTLIST,
                              channel=channel_name)

    def helper_invite_list(self, channel_name, channel):
        for mask in channel.invite_masks:
            self.connection.reply(irc.RPL_INVITELIST,
                                  channel=channel_name, mask=mask)
        self.connection.reply(irc.RPL_ENDOFINVITELIST,
                              channel=channel_name)

    def helper_chan_op_privs_needed(self, channel):
        self.connection.reply(irc.ERR_CHANOPRIVSNEEDED, channel=channel)

    def prefix(self):
        nick = self.connection.nick
        username = self.connection.user[0]
        host = self.connection.getsockname()[0]
        return ":%s!%s@%s" % (nick, username, host)
