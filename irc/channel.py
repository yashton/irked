import irc
from irc.channel_mode import ChannelMode

class Channel:
    def __init__(self, name, server):
        self.name    = name
        self.clients = set()
        self.topic   = None

        self.modes = ChannelMode()
        self.server  = server

    def add(self, client):
        self.clients.add(client)
        self._send(client, 'JOIN %s' % self.name)

        if self.topic:
            client.connection.reply(irc.RPL_TOPIC,
                                    channel=self.name,
                                    topic=self.topic)

        self.rpl_name_reply(client)

    def remove(self, client, message = None, parted = True):
        if client in self.clients:
            if parted:
                if message:
                    self._send(client, 'PART %s :%s' % (self.name, message))
                else:
                    self._send(client, 'PART %s' % self.name)
            self.clients.remove(client)
        else:
            client.connection.reply(irc.ERR_NOTONCHANNEL, channel=self.name)

    def privmsg(self, sender, message):
        if self.modes.insiders_only() and sender not in self.clients:
            sender.connection.reply(irc.ERR_CANNOTSENDTOCHAN, channel=self.name)
            return

        # TODO: check ban lists, moderation, etc.

        self._send(sender,
                'PRIVMSG %s :%s' % (self.name, message),
                notify_sender = False)

    def kick(self, kicker, kickee, reason):
        # TODO: kickee probably can be more than just a nick

        if kicker not in self.clients:
            kicker.connection.reply(irc.ERR_NOTONCHANNEL,
                                    channel_name=self.name)
            return

        if kicker not in self.modes.operators:
            kicker.connection.reply(irc.ERR_CHANOPRIVSNEEDED, channel=self.name)
            return

        if kickee not in [c.connection.nick for c in self.clients]:
            kicker.connection.reply(irc.ERR_USERNOTINCHANNEL,
                                    nickname=kickee, channel=self.name)
            return

        if not reason:
            reason = kickee

        self._send(kicker, "KICK %s %s :%s" % (self.name, kickee, reason))

    def set_topic(self, client, topic):
        if client not in self.clients:
            client.connection.reply(irc.ERR_NOTONCHANNEL,
                                    channel_name=self.name)
            return

        if self.modes.set_topic_needs_ops() and not self.modes.is_op(client):
            client.connection.reply(irc.ERR_CHANOPRIVSNEEDED,
                                  channel=self.name)
            return

        self.server.logger.debug("Setting topic for %s: %s",
                self.name, topic)

        if topic == "":
            self.topic = None
        else:
            self.topic = topic

        self._send(client, "TOPIC %s :%s" % (self.name, self.topic or ""))

    def rpl_topic(self, client):
        # TODO: check that client is allowed to see the topic
        if self.topic:
            client.connection.reply(irc.RPL_TOPIC,
                                    channel=self.name, topic=self.topic)
        else:
            client.connection.reply(irc.RPL_NOTOPIC,
                                    channel=self.name)

    def rpl_name_reply(self, client):
        names = [c.connection.nick for c in self.clients]
        names = []
        for c in self.clients:
            prefix = ''
            if c in self.modes.operators:
                prefix = '@'
            names.append(prefix + c.connection.nick)

        # TODO: need to split the names list up in case it's too long
        client.connection.reply(irc.RPL_NAMREPLY,
                                channel=self.name, nick=str.join(' ', names))
        client.connection.reply(irc.RPL_ENDOFNAMES, channel=self.name)

    def rpl_who(self, client):
        for c in self.clients:
            client.connection.reply(irc.RPL_WHOREPLY,
                    channel=self.name, user=c.connection.user[0],
                    host=c.connection._host(), server=self.server.name,
                    nick=c.connection.nick, foo1="*", foo2="", hopcount=0,
                    realname=c.connection.user[2])

    def _send(self, sender, message, notify_sender = True):
        self.server.notify_channel(self.name, sender, message, notify_sender)
