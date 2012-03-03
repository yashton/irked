'''IRC automated client (bot) helper module'''
import random
import linecache
import re
import subprocess
import time
import irc

COMMANDS = {
    "PASS" : "PASS %(secret)s",
    "NICK" : "NICK %(nick)s",
    "USER" : "USER %(user)s %(mode)d * %(realname)s",
    "OPER" : "OPER %(user)s %(pass)s",
    "USER_MODE" : "MODE %(nick)s %(change)s",
    "CHANNEL_MODE" : "MODE %(channel) %(change)s %(params)s",
    "SERVICE" : "SERVICE %(nickname)s %(reserved)s %(distribution)s " + \
        "%(type)s %(reserved)s %(info)s",
    "QUIT" : "QUIT :%(message)s",
    "SQUIT" : "SQUIT %(server)s :%(comment)s",
    "JOIN" : "JOIN %(channel)s %(key)s",
    "PART" : "PART %(channel)s :%(message)s",
    "TOPIC" : "TOPIC %(channel)s",
    "TOPIC_SET" : "TOPIC %(channel)s :%(topic)s",
    "NAMES" : "NAMES %(channel)s %(target)s",
    "LIST" : "LIST %(channel)s %(target)s",
    "KICK" : "KICK %(channel)s %(user)s :%(comment)s",
    "PRIVMSG" : "PRIVMSG %(target)s :%(message)s",
    "MOTD" : "MOTD %(target)s",
    "LUSERS" : "LUSERS %(mask)s %(target)s",
    "VERSION" : "VERSION %(target)s",
    "STATS" : "STATS %(query)s %(target)s",
    "LINKS" : "LINKS %(remote)s %(masks)s",
    "CONNECT" : "CONNECT %(server)s %(port)d %(remote_server)s",
    "TRACE" : "TRACE %(target)s",
    "ADMIN" : "ADMIN %(target)s",
    "INFO" : "INFO %(target)s",
    "SERVLIST" : "SERVLIST %(mask)s %(type)s",
    "SQUERY" : "SQUERY %(servicename)s :%(text)s",
    "WHO" : "WHO %(mask)s %(oper_flag)s",
    "WHOIS" : "WHOIS %(target)s %(mask)s)",
    "WHOWAS" : "WHOWAS %(nickname)s %(count)d %(target)s",
    "KILL" : "KILL %(nickname)s :%(comment)s",
    "PING" : "PING %(server1)s %(server2)s",
    "PONG" : "PONG %(server1)s %(server2)s"
}

EXPECTED = {
    "PASS" : {
        irc.ERR_NEEDMOREPARAMS,
        irc.ERR_ALREADYREGISTRED},
    "NICK" : {
        irc.ERR_NONICKNAMEGIVEN,
        irc.ERR_ERRONEUSNICKNAME,
        irc.ERR_NICKNAMEINUSE,
        irc.ERR_NICKCOLLISION,
        irc.ERR_UNAVAILRESOURCE,
        irc.ERR_RESTRICTED},
    "USER" : {
        irc.ERR_NEEDMOREPARAMS,
        irc.ERR_ALREADYREGISTRED},
    "OPER" : {
        irc.ERR_NEEDMOREPARAMS,
        irc.RPL_YOUREOPER,
        irc.ERR_NOOPERHOST,
        irc.ERR_PASSWDMISMATCH},
    "USER_MODE" : {
        irc.ERR_NEEDMOREPARAMS,
        irc.ERR_USERSDONTMATCH,
        irc.ERR_UMODEUNKNOWNFLAG,
        irc.RPL_UMODEIS},
    "SERVICE" : {
        irc.ERR_ALREADYREGISTRED,
        irc.ERR_NEEDMOREPARAMS,
        irc.ERR_ERRONEUSNICKNAME,
        irc.RPL_YOURESERVICE,
        irc.RPL_YOURHOST,
        irc.RPL_MYINFO},
    "QUIT" : {},
    "SQUIT" : {
        irc.ERR_NOPRIVILEGES,
        irc.ERR_NOSUCHSERVER,
        irc.ERR_NEEDMOREPARAMS},
    "JOIN" : {
        irc.ERR_NEEDMOREPARAMS,
        irc.ERR_BANNEDFROMCHAN,
        irc.ERR_INVITEONLYCHAN,
        irc.ERR_BADCHANNELKEY,
        irc.ERR_CHANNELISFULL,
        irc.ERR_BADCHANMASK,
        irc.ERR_NOSUCHCHANNEL,
        irc.ERR_TOOMANYCHANNELS,
        irc.ERR_TOOMANYTARGETS,
        irc.ERR_UNAVAILRESOURCE,
        irc.RPL_TOPIC},
    "PART" : {
        irc.ERR_NEEDMOREPARAMS,
        irc.ERR_NOSUCHCHANNEL,
        irc.ERR_NOTONCHANNEL},
    "CHANNEL_MODE" : {
        irc.ERR_NEEDMOREPARAMS,
        irc.ERR_KEYSET,
        irc.ERR_NOCHANMODES,
        irc.ERR_CHANOPRIVSNEEDED,
        irc.ERR_USERNOTINCHANNEL,
        irc.ERR_UNKNOWNMODE,
        irc.RPL_CHANNELMODEIS,
        irc.RPL_BANLIST,
        irc.RPL_ENDOFBANLIST,
        irc.RPL_EXCEPTLIST,
        irc.RPL_ENDOFEXCEPTLIST,
        irc.RPL_INVITELIST,
        irc.RPL_ENDOFINVITELIST,
        irc.RPL_UNIQOPIS},
    "TOPIC" : {
        irc.ERR_NEEDMOREPARAMS,
        irc.ERR_NOTONCHANNEL,
        irc.RPL_NOTOPIC,
        irc.RPL_TOPIC,
        irc.ERR_CHANOPRIVSNEEDED,
        irc.ERR_NOCHANMODES},
    "NAMES" : {
        irc.ERR_TOOMANYMATCHES,
        irc.ERR_NOSUCHSERVER,
        irc.RPL_NAMREPLY,
        irc.RPL_ENDOFNAMES},
    "LIST" : {
        irc.ERR_TOOMANYMATCHES,
        irc.ERR_NOSUCHSERVER,
        irc.RPL_LIST,
        irc.RPL_LISTEND},
    "INVITE" : {
        irc.ERR_NEEDMOREPARAMS,
        irc.ERR_NOSUCHNICK,
        irc.ERR_NOTONCHANNEL,
        irc.ERR_USERONCHANNEL,
        irc.ERR_CHANOPRIVSNEEDED,
        irc.RPL_INVITING,
        irc.RPL_AWAY},
    "PRIVMSG" : {
        irc.ERR_NORECIPIENT,
        irc.ERR_NOTEXTTOSEND,
        irc.ERR_CANNOTSENDTOCHAN,
        irc.ERR_NOTOPLEVEL,
        irc.ERR_WILDTOPLEVEL,
        irc.ERR_TOOMANYTARGETS,
        irc.ERR_NOSUCHNICK,
        irc.RPL_AWAY},
    "MOTD" : {
        irc.RPL_MOTDSTART,
        irc.RPL_MOTD,
        irc.RPL_ENDOFMOTD,
        irc.ERR_NOMOTD},
    "LUSERS" : {
        irc.RPL_LUSERCLIENT,
        irc.RPL_LUSEROP,
        irc.RPL_LUSERUNKNOWN,
        irc.RPL_LUSERCHANNELS,
        irc.RPL_LUSERME,
        irc.ERR_NOSUCHSERVER},
    "VERSION" : {
        irc.ERR_NOSUCHSERVER,
        irc.RPL_VERSION},
    "STATS" : {
        irc.ERR_NOSUCHSERVER,
        irc.RPL_STATSLINKINFO,
        irc.RPL_STATSUPTIME,
        irc.RPL_STATSCOMMANDS,
        irc.RPL_STATSOLINE,
        irc.RPL_ENDOFSTATS},
    "LINKS" : {
        irc.ERR_NOSUCHSERVER,
        irc.RPL_LINKS,
        irc.RPL_ENDOFLINKS},
    "TIME" : {
        irc.ERR_NOSUCHSERVER,
        irc.RPL_TIME},
    "CONNECT" : {
        irc.ERR_NOSUCHSERVER,
        irc.ERR_NOPRIVILEGES,
        irc.ERR_NEEDMOREPARAMS},
    "TRACE" : {
        irc.ERR_NOSUCHSERVER,
        irc.RPL_TRACELINK},
    "ADMIN" : {
        irc.ERR_NOSUCHSERVER,
        irc.RPL_ADMINME,
        irc.RPL_ADMINLOC1,
        irc.RPL_ADMINLOC2,
        irc.RPL_ADMINEMAIL},
    "INFO" : {
        irc.ERR_NOSUCHSERVER,
        irc.RPL_INFO,
        irc.RPL_ENDOFINFO},
    "SERVLIST" : {
        irc.RPL_SERVLIST,
        irc.RPL_SERVLISTEND},
    "SQUERY" : {
        irc.ERR_NORECIPIENT,
        irc.ERR_NOTEXTTOSEND,
        irc.ERR_CANNOTSENDTOCHAN,
        irc.ERR_NOTOPLEVEL,
        irc.ERR_WILDTOPLEVEL,
        irc.ERR_TOOMANYTARGETS,
        irc.ERR_NOSUCHNICK,
        irc.RPL_AWAY},
    "WHO" : {
        irc.ERR_NOSUCHSERVER,
        irc.RPL_WHOREPLY,
        irc.RPL_ENDOFWHO},
    "WHOIS" : {
        irc.ERR_NOSUCHSERVER,
        irc.ERR_NONICKNAMEGIVEN,
        irc.RPL_WHOISUSER,
        irc.RPL_WHOISCHANNELS,
        irc.RPL_WHOISCHANNELS,
        irc.RPL_WHOISSERVER,
        irc.RPL_AWAY,
        irc.RPL_WHOISOPERATOR,
        irc.RPL_WHOISIDLE,
        irc.ERR_NOSUCHNICK,
        irc.RPL_ENDOFWHOIS},
    "WHOWAS" : {
        irc.ERR_NONICKNAMEGIVEN,
        irc.ERR_WASNOSUCHNICK,
        irc.RPL_WHOWASUSER,
        irc.RPL_WHOISSERVER,
        irc.RPL_ENDOFWHOWAS},
    "KILL" :  {
        irc.ERR_NOPRIVILEGES,
        irc.ERR_NEEDMOREPARAMS,
        irc.ERR_NOSUCHNICK,
        irc.ERR_CANTKILLSERVER},
    "PING" : {
        irc.ERR_NOORIGIN,
        irc.ERR_NOSUCHSERVER},
    "PONG" : {
        irc.ERR_NOORIGIN,
        irc.ERR_NOSUCHSERVER},
}

def ord_range(*args):
    output = list()
    for (x, y) in args:
        output += list(range(ord(x), ord(y)+1))
    return output

ALPHANUM = ord_range(('0', '9'), ('A','Z'), ('a', 'z'))

class WordGen:
    def __init__(self, words):
        self.words = words
        output = subprocess.check_output(['wc', '-l', self.words])
        self.size = int(output.split()[0])

    def word(self):
        lineno = random.randint(0, self.size)
        return linecache.getline(self.words, lineno).strip()

    def sentence(self, length=None):
        output = list()
        if length is None:
            length = random.randint(1, 20)
        while length > 0:
            output.append(self.word())
            length -= 1

        return " ".join(output)

    def garbage(self, length, alphanum=True):
        chars = list()
        while length > 0:
            if alphanum:
                char = random.choice(ALPHANUM)
            else:
                char = random.randint(33, 126)
            chars.append(chr(char))
            length -= 1
        return "".join(chars)

class Bot():
    def __init__(self, sock, ready, generator):
        self.sock = sock
        self.request_ready = ready
        self.generator = generator
        self.terminator = b'\r\n'

        self.out_buffer = b''
        self.in_buffer = b''
        self.expected = set()

        self.register(self.generator.word(),
                      self.generator.word(),
                      self.generator.word(),
                      0,
                      self.generator.sentence(length=2))
        self.join("#test")

    def handle(self, data):
        self.in_buffer += data
        if len(self.in_buffer) > 0:
            messages = re.split(b'[\r\n]+', self.in_buffer)
            if messages[-1] != b'':
                self.in_buffer = messages[-1]
            else:
                self.in_buffer = b''
            for message in messages[:-1]:
                self.process(bytes.decode(message))

    def process(self, response):
        print(response)
        args = response.split()
        try:
            code = args[1]
            if code == "PRIVMSG":
                self.send("PRIVMSG",
                          target=args[2],
                          message=self.generator.sentence())
                time.sleep(random.randint(1, 5))
        except:
            pass

    def send(self, command, **kargs):
        message = COMMANDS[command] % kargs
        expected = EXPECTED[command]
        self.expected = self.expected.union(expected)
        print(message)
        self.out_buffer += ("%s\r\n" % message).encode()
        self.request_ready()

    def register(self, secret, nick, user, mode, realname):
        self.send("PASS", secret=secret)
        self.send("USER", user=user, mode=mode, realname=realname)
        self.send("NICK", nick=nick)

    def join(self, channel):
        self.send("JOIN", channel=channel, key="")
