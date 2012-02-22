class ChannelMode:
    def __init__(self):
        self.creator = None
        self.operators = set()
        self.voice = set()

        self.anonymous = False
        self.moderated = False
        self.invite = False
        self.no_message = False
        self.quiet = False
        self.private = False
        self.secret = False
        self.reop = False
        self.topic = False

        self.ban_masks = set()
        self.exception_masks = set()
        self.invite_masks = set()

        self.key = None
        self.limit = None

    def user_mode(self, nick):
        #TODO return real values
        return "+ns"
