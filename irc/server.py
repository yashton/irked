class IrcServer:
    hopcount = 0
    info = None
    token = None

    def __init__(self, connection, server):
        self.connection = connection
        self.server = server

    def cmd_server(self, args):
        #TODO this should handle additional server notifications for network expansion.
        pass
