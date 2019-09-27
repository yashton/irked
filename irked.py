#!/usr/bin/env python3
#
# irked IRC Daemon
# Copyright (C) 2012 Cameron Matheson and Ashton Snelgrove
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import asyncore
import logging
import socket as _socket
import re
import irc
import time
import subprocess
import os.path
import argparse
import configparser
import sys
import random
import hashlib
from irc.client import IrcClient
from irc.server import IrcServer
from irc.channel import Channel
from irc.handler import IrcHandler
from irc.extensions import IrcExtensions
from irc.statistics import Statistic, StatisticCollection

MOTD_FILE = "motd"
INFO_FILE = "info"
CONFIG_FILE = 'irked.conf'

LOG_FILE = "irked.log"
LOG_FORMAT = "%(asctime)s %(filename)s:" + \
    "%(lineno)d in %(funcName)s %(levelname)s: %(message)s"
LOG_LEVEL = logging.DEBUG
LOGGER = "irked"

DEFAULT_HOST = ''
DEFAULT_PORT = 6667
DEFAULT_NAME = 'irked.server'

#
# The dispatcher is responsible for setting up a socket for IRC connections and
# spawning appropriate handlers for incoming connections (either IrcClient or
# IrcServer
#
# Sockets are polled by asyncore.  It fires callback methods on the handlers
# when data is availabe for reading
#
class IrcDispatcher(asyncore.dispatcher):

    def __init__(self, host=None, port=None, name=None, config=CONFIG_FILE):
        self.config_file = config
        self.config = configparser.ConfigParser()
        self.config.read(self.config_file)
        self.init_logger()
        self.setup_extensions()
        self.server_config(host, port, name)

        asyncore.dispatcher.__init__(self)
        self.create_socket(_socket.AF_INET, _socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind(self.address)
        self.listen(5)
        self.logger.info('Bound to "%s", listening on port %d' % self.address)

        self.token = random.randint(1, 1000)
        self.connections = set()
        self.clients = dict()
        self.servers = dict()
        self.services = dict()
        self.channels = dict()
        self.user_modes = dict()
        for i in irc.IRC_MODES:
            self.user_modes[i] = True
        self.channel_modes = dict()
        for i in irc.IRC_CHANNEL_MODES:
            self.channel_modes[i] = True

        self.version = self.gen_version()
        self.version_comment = 'Development'

        self.statistics = StatisticCollection()
        self.statistics.sent = Statistic()
        self.statistics.received = Statistic()
        self.statistics.messages = Statistic()

        self.launched = time.strftime("%c %Z")
        self.logger.info('Server %s running irked version %s launched on %s',
                         self.name,
                         self.version,
                         self.launched)

    def server_config(self, host, port, name):
        if host is None:
            host = self.config.get('server', 'host', fallback=DEFAULT_HOST)
        if port is None:
            port = self.config.getint('server', 'port', fallback=DEFAULT_PORT)
        self.address = (host, port)

        if name is None:
            name = self.config.get('server', 'name', fallback=DEFAULT_NAME)
        self.name = name

        self.motd_file = self.config.get('server', 'motd_file', fallback=MOTD_FILE)
        self.info_file = self.config.get('server', 'info_file', fallback=INFO_FILE)

    def init_logger(self):
        log_file = self.config.get("log", "log_file", fallback=LOG_FILE)
        log_level_string = self.config.get("log", "log_level", fallback=None)
        if log_level_string is not None:
            try:
                log_level = logging.__dict__[log_level_string]
            except KeyError:
                log_level = LOG_LEVEL
        else:
            log_level = LOG_LEVEL

        self.logger = logging.getLogger(LOGGER)
        self.logger.setLevel(log_level)
        file_handler = logging.FileHandler(log_file)
        formatter = logging.Formatter(LOG_FORMAT)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        self.logger.info("Initialized logger %s at level %d to file %s.",
                         LOGGER,
                         log_level,
                         log_file)

    def setup_extensions(self):
        self.extensions = IrcExtensions(self.logger);
        try:
            load = self.config['extensions']
        except KeyError:
            self.logger.warning("No extensions configuration section. No extensions loaded.")
            return
        for name, location in load.items():
            self.logger.debug("Loading extension '%s'", name)
            try:
                options = self.config[name]
            except KeyError as err:
                self.logger.warning("No extension configuration for '%s'", name)
                options = dict()
            self.extensions.register(name, location, options)
        self.logger.info("Loaded extensions: [%s]", ", ".join(self.extensions.modules.keys()))

    def sconnect(self, server, port):
        socket = _socket.socket(_socket.AF_INET, _socket.SOCK_STREAM)
        socket.connect((server, port))
        handler = IrcHandler(socket, self)
        self.connections.add(handler)
        handler.raw_send("PASS %s\r\n" % "password")
        server_msg = "SERVER %s %d %d :%s\r\n"
        handler.raw_send(server_msg % (self.name, 0, self.token, "Test server"))
        for server in self.servers.items():
            if server is handler:
                continue
            for remote in server.neighbors.items():
                handler.raw_send(server_msg % (server.name,
                                               server.hopcount+1,
                                               server.token,
                                               server.info))

    def squit(self, server, comment):
        handler = self.servers[server]
        try:
            handler.connection.close()
        except Exception as err:
            self.logger.error("Exception during socket close: %s" % \
                                  err)
        finally:
            for neighbor in self.servers:
                neighbor.netsplit(server)
            del self.servers[server]

    def channel_add(self, channel, owner):
        self.extensions.pre_channel_create(channel);
        self.channels[channel] = Channel(channel, self)
        self.channels[channel].modes.creator = owner
        self.channels[channel].modes.operators.add(owner)

    def handle_accepted(self, socket, port):
        self.logger.info('Yay, connection from %s', repr(port))
        handler = IrcHandler(socket, self)
        self.connections.add(handler)

    def notify_channel(self, channel, sender, message, notify_sender = True):
        """send message to all users in the given channel"""

        # TODO: check that the sender has permission to send messages here

        prefixed_message = '%s %s\r\n' % (sender.prefix(), message)
        for client in self.channels[channel].clients:
            if client == sender and not notify_sender:
                continue
            if not client.connection:
                continue
            client.connection.raw_send(prefixed_message)
        for server in self.servers.items():
            if sender.servertoken() == server.token:
                continue
            server.connection.raw_send(prefixed_message)

    def prefix(self):
        # FIXME
        return ':%s' % self.name

    def __repr__(self):
        return "<IrcServer: clients=%s names=%s channels=%s>" % \
            (repr(self.connections),
             repr(self.clients.keys()),
             repr(self.channels))

    def gen_version(self):
        '''Fetch the current revision number for the working directory for
        use as a version number'''
        try:
            branch = subprocess.check_output(["hg", "branch"])
            command = ["hg", "heads",
                       branch.strip(),
                        "--template", "{rev}:{node|short} ({date|isodate})"]
            version = subprocess.check_output(command)
            return "%s-%s" % ("irked", version.decode("utf-8"))
        except subprocess.CalledProcessError:
            return "unknown"

    def has_motd(self):
        '''Indicates whether a message of the day is available.'''
        return os.path.isfile(self.motd_file)

    def motd(self):
        '''Returns an iterable set of motd lines.'''
        if os.path.isfile(self.motd_file):
            for line in open(self.motd_file):
                yield line.rstrip()

    def info(self):
        '''Returns an iterable set of info lines.'''
        yield "irked IRC daemon version %(version)s" % \
            {'version' : self.gen_version()}
        if os.path.isfile(self.info_file):
            for line in open(self.info_file):
                yield line.rstrip()

    def is_valid_oper_pass(self, username, password):
        if username not in self.config['opers']:
            return False
        passwd_encrypt = self.config['opers'][username]
        salt = passwd_encrypt[:4]
        h = hashlib.sha1()
        h.update(salt.encode())
        h.update(password.encode())
        passwd_match = salt + h.hexdigest()
        return passwd_encrypt == passwd_match

    def allows_oper(self):
        #TODO O-line implementation
        return True

if __name__ == '__main__':
    epilog = 'Command line options have priority over config file values.'
    parser = argparse.ArgumentParser(description='irked IRC daemon.',
                                     epilog=epilog)
    parser.add_argument('-s', '--server',
                        nargs='?', default=None,
                        help='Server host bind address.')
    parser.add_argument('-p', '--port',
                        type=int, nargs='?', default=None,
                        help='Server port. Defaults to %d.' % DEFAULT_PORT)
    parser.add_argument('-n', '--name',
                        nargs='?', default=None,
                        help='Server name.')
    parser.add_argument('-c', '--config',
                        nargs='?', default=CONFIG_FILE,
                        help='Configuration file. (default: %(default)s)')
    args = parser.parse_args()

    server = IrcDispatcher(host=args.server,
                           port=args.port,
                           name=args.name,
                           config=args.config)
    asyncore.loop()
