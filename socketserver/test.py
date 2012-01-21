#! /usr/bin/python3
import socket
import sys
import time
import random

HOST, PORT = "localhost", 6667

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((HOST, PORT))
try:
    while True:
        data = ""
        for i in range(0,250):
            data += chr(random.randrange(32, 126))
        sock.send(bytes(data + "\n", "utf-8"))
        received = str(sock.recv(1024), "utf-8")
        time.sleep(0.1)
finally:
    sock.close()
