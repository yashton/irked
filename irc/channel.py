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

        # TODO: proper topic sending
        if self.topic is None or self.topic == '':
            client.connection._send(irc.RPL_NOTOPIC, channel=self.name)
        else:
            client.connection._send(irc.RPL_TOPIC, channel=self.name, topic=self.topic)

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
            client.connection._send(irc.ERR_NOTONCHANNEL, channel=self.name)

    def kick(self, kicker, kickee, reason):
        # TODO: kickee probably can be more than just a nick

        if kicker not in self.clients:
            kicker.connection._send(irc.ERR_NOTONCHANNEL, channel_name=self.name)
            return

        if kicker not in self.modes.operators:
            kicker.connection._send(irc.ERR_CHANOPRIVSNEEDED, channel=self.name)
            return

        if kickee not in [c.connection.nick for c in self.clients]:
            kicker.connection_send(irc.ERR_USERNOTINCHANNEL,
                                   nickname=kickee, channel=self.name)
            return

        if not reason:
            reason = kickee

        self._send(kicker, "KICK %s %s :%s" % (self.name, kickee, reason))

    def rpl_name_reply(self, client):
        # TODO: probably need to split the names list up in case it's too long
        names = [c.connection.nick for c in self.clients]
        client.connection._send(irc.RPL_NAMREPLY,
                                channel=self.name, nick=str.join(' ', names))
        client.connection._send(irc.RPL_ENDOFNAMES, channel=self.name)

    def rpl_who(self, client):
        for c in self.clients:
            client.connection._send(irc.RPL_WHOREPLY,
                    channel=self.name, user=c.connection.user[0],
                    host=c.connection._host(), server=self.server.name,
                    nick=c.connection.nick, foo1="*", foo2="", hopcount=0,
                    realname=c.connection.user[2])

    def _send(self, sender, message, notify_sender = True):
        self.server.notify_channel(self.name, sender, message, notify_sender)
