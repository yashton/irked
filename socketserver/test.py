#! /usr/bin/python3
import socket
import sys
import time
import random

HOST, PORT = sys.argv[1], int(sys.argv[2])

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((HOST, PORT))

try:
    while True:
        datas = open(sys.argv[3])
        for data in datas:
            sock.send(bytes(data, "utf-8"))
            received = str(sock.recv(1024), "utf-8")
            time.sleep(0.1)
        datas.close()
finally:
    sock.close()
