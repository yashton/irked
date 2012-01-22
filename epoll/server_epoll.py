''' Echo server prototype.
Based on code form http://scotdoyle.com/python-epoll-howto.html'''

import socket
import select

EOL1 = b'\r\n'
EOL2 = b'\n'

HOST, PORT = 'localhost', 6667
BACKLOG_QUEUE_SIZE = 50

serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
serversocket.bind((HOST, PORT))
serversocket.listen(BACKLOG_QUEUE_SIZE)
serversocket.setblocking(0)

epoll = select.epoll()
epoll.register(serversocket.fileno(), select.EPOLLIN)

try:
    connections = {}; requests = {}; responses = {}; addresses = {}
    while True:
        events = epoll.poll(1)
        for fileno, event in events:
            if fileno == serversocket.fileno():
                connection, address = serversocket.accept()
                connection.setblocking(0)
                fileno = connection.fileno()
                epoll.register(fileno, select.EPOLLIN)
                connections[fileno] = connection
                addresses[fileno] = address
                requests[fileno] = b''
                responses[fileno] = b''
            elif event & select.EPOLLIN:
                data = connections[fileno].recv(1024)
                requests[fileno] += data
                responses[fileno] += data.upper()
                if EOL1 in requests[fileno] or EOL2 in requests[fileno]:
                    epoll.modify(fileno, select.EPOLLOUT)
                    print('Request from %s with fileno %d: %s%s'
                          % (addresses[fileno],
                             fileno,
                             requests[fileno][:16],
                             '...' if len(requests[fileno]) > 16 else ''))
            elif event & select.EPOLLOUT:
                byteswritten = connections[fileno].send(responses[fileno])
                responses[fileno] = responses[fileno][byteswritten:]
                if len(responses[fileno]) == 0:
                    epoll.modify(fileno, 0)
                    connections[fileno].shutdown(socket.SHUT_RDWR)
            elif event & select.EPOLLHUP:
                epoll.unregister(fileno)
                connections[fileno].close()
                del connections[fileno]
                del addresses[fileno]
                del requests[fileno]
                del responses[fileno]

finally:
    epoll.unregister(serversocket.fileno())
    epoll.close()
    serversocket.close()
