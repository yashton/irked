SAID = dict()

def configure(options):
    pass

def pre_channel_create(channel):
    SAID[channel] = set()

def pre_channel_privmsg(channel, nick, message):
    if message in SAID[channel]:
        return (False, message)
    SAID[channel].add(message)
    return (True, message)
