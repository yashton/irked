#! /usr/bin/python3
import socketserver
import multiprocessing
import logging

HOST, PORT = "localhost", 6667
LOG_FILE = "/tmp/snelgrov.log"
LOG_FORMAT = "%(asctime)s %(levelname)s %(filename)s:" + \
    "%(lineno)d in %(funcName)s : %(message)s"
LOG_LEVEL = logging.DEBUG

LOGGER = logging.getLogger('prototype')
LOGGER.setLevel(LOG_LEVEL)
FILE_HANDLER = logging.FileHandler(LOG_FILE)
FORMATTER = logging.Formatter(LOG_FORMAT)
FILE_HANDLER.setFormatter(FORMATTER)
LOGGER.addHandler(FILE_HANDLER)

class EchoRequestHandler(socketserver.StreamRequestHandler):
    def handle(self):
        LOGGER.info("Connected: %s:%d",
                    self.client_address[0],
                    self.client_address[1])
        try:
            for line in self.rfile:
                self.data = line
                LOGGER.debug("Received from %s:%d - %s%s",
                             self.client_address[0],
                             self.client_address[1],
                             self.data[:16],
                             "..." if len(self.data) > 16 else "")
                self.wfile.write(self.data.upper())
        except Exception as err:
            LOGGER.error("Error from %s:%d - %s",
                        self.client_address[0],
                        self.client_address[1],
                        err)
        LOGGER.info("Finished %s:%d",
                     self.client_address[0],
                     self.client_address[1])

class SocketIrcServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

if __name__ == "__main__":
    server = SocketIrcServer((HOST, PORT), EchoRequestHandler)
    server.serve_forever()
