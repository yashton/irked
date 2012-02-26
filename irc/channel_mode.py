class ChannelMode:
    def __init__(self):
        self.operators = set()

        # available_modes don't get reported in the mode string (it should be
        # possible to query them individually however)
        # TODO: load defaults from config file
        self.modes = {'n': True, 't': True}
        self.available_modes = set({'n', 'o', 't'})

    def mode_string(self):
        enabled_flags = [flag for flag, is_on in self.modes.items() if is_on]
        enabled_flags.sort()
        return '+' + str.join('', enabled_flags)

    def is_op(self, client):
        return client in self.operators

    def set_topic_needs_ops(self):
        return self.modes['t']

    def set(self, mode, enable, params = None):
        """ sets the given mode

            mode: a single character (n, o, or t)
            enable: boolean
            params: mode params

            returns True if the mode was changed """

        if mode not in self.available_modes:
            return

        if mode == 'o':
            # TODO: op removal
            return

        if enable:
            if self.modes[mode]:
                return
            self.modes[mode] = True
        else:
            if not self.modes[mode]:
                return
            self.modes[mode] = False

        return True

    def user_mode(self, nick):
        #TODO return real values
        return "+ns"
