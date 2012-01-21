#!/usr/bin/env python3

import asyncore
import socket

class EchoHandler(asyncore.dispatcher_with_send):

    def handle_read(self):
        data = self.recv(8192)
        if data:
            self.send(data)
        #print("%s: <--- %s" % (self.getpeername()[1], data))
        #print("%s: ---> %s" % (self.getpeername()[1], data))

class EchoServer(asyncore.dispatcher):
    clients = 0

    def __init__(self, host, port):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind((host, port))
        self.listen(5)
        print('Listening on port %s' % port)

    def handle_accepted(self, socket, port):
        self.clients += 1
        print('Yay, connection %d from %s' % (self.clients, repr(port)))
        handler = EchoHandler(socket)

server = EchoServer('', 6666)
asyncore.loop()
