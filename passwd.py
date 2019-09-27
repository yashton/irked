#! /usr/bin/python3
import random
import hashlib
import configparser

from getpass import getpass

CONFIG_FILE = 'irked.conf'

username = input("Username: ")
passwd = getpass("Password: ")
salt = ''.join([random.choice('bcdfghjklmnpqrstvwxyz') for i in range(4)])
h = hashlib.sha1()
h.update(salt.encode())
h.update(passwd.encode())
passwd_encrypt = salt + h.hexdigest()

config = configparser.ConfigParser()
config.read(CONFIG_FILE)
config['opers'][username] = passwd_encrypt
with open(CONFIG_FILE, 'w') as configfile:
    config.write(configfile)
