import sys
import socket
import select
import irc.bot

epoll = select.epoll()
generator = irc.bot.WordGen('/usr/share/dict/words')
connections = {}

def ready(fileno):
    return lambda: epoll.modify(fileno, select.EPOLLOUT)

def register(address):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.connect(address)
    #sock.listen(BACKLOG_QUEUE_SIZE)
    sock.setblocking(0)
    epoll.register(sock.fileno(), select.EPOLLIN)
    client = irc.bot.Bot(sock, ready(sock.fileno()), generator)
    connections[sock.fileno()] = client

register((sys.argv[1], int(sys.argv[2])))
try:
    while True:
        events = epoll.poll(1)
        for fileno, event in events:
            client = connections[fileno]
            if event & select.EPOLLIN:
                data = client.sock.recv(1024)
                client.handle(data)
            elif event & select.EPOLLOUT:
                byteswritten = client.sock.send(client.out_buffer)
                client.out_buffer = client.out_buffer[byteswritten:]
                if len(client.out_buffer) == 0:
                    epoll.modify(fileno, select.EPOLLIN)
            elif event & select.EPOLLHUP:
                epoll.unregister(fileno)
                client.sock.close()
                del connections[fileno]

finally:
    epoll.close()
