import sqlite3
import time
DB = None

def configure(options):
    global DB

    DB = sqlite3.connect(options['db'])
    cur = DB.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS channelogs (' \
                'id integer PRIMARY KEY AUTOINCREMENT,' \
                'timestamp integer,' \
                'channel varchar(20),' \
                'nick varchar(10),' \
                'message varchar(255))')

# TODO: i really want this to be a post_channel_privmsg
def pre_channel_privmsg(channel, nick, message):
    global DB
    cur = DB.cursor()

    values = (int(time.time() * 1000), channel, nick, message)
    cur.execute('INSERT INTO channelogs (timestamp, channel, nick, message) ' \
                'VALUES (?, ?, ?, ?)', values)
    DB.commit()
    return True, message
