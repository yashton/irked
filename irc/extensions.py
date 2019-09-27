HANDLER_LIST = [
    'transform_privmsg',
    'pre_channel_create',
    'pre_channel_privmsg',
]

class IrcExtensions:
    def __init__(self, logger):
        self.modules = dict()
        self.logger = logger
        self.handlers = dict()
        for handler in HANDLER_LIST:
            self.handlers[handler] = list()

    def register(self, name, location, options):
        if len(location) > 0:
            self.logger.debug("Adding extension module path '%s'", location)
            sys.path.insert(1, location)
        try:
            module = __import__(name)
        except ImportError as err:
            self.logger.error("Unable to import extension module '%s': %s",
                              name, err)
            return
        try:
            module.configure(options)
        except AttributeError:
            self.logger.error("Module '%s' does not provide method 'configure'",
                              name)
            return
        for handler in self.handlers:
            if handler in module.__dict__:
                self.logger.debug("Registering handler '%s' from extension %s",
                                  handler, name)
                self.handlers[handler].append(module.__dict__[handler])
        self.modules[name] = module

    def transform_privmsg(self, message):
        for function in self.handlers['transform_privmsg']:
            message = function(message)
        return message

    def pre_channel_create(self, channel):
        for function in self.handlers['pre_channel_create']:
            function(channel)

    def pre_channel_privmsg(self, channel, sender_nick, message):
        success = True
        for function in self.handlers['pre_channel_privmsg']:
            success, message = function(channel, sender_nick, message)
            if not success:
                return (success, message)
        return (success, message)
