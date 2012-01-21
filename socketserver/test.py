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
        datas = open(sys.argv[1])
        for data in datas:
            sock.send(bytes(data, "utf-8"))
            received = str(sock.recv(1024), "utf-8")
            time.sleep(0.1)
finally:
    sock.close()
