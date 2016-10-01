#!/usr/bin/python

import thread
import time

def joinAfterConnectThread(bot):
    time.sleep(30)
    if 'channels' in bot.config:
        bot.join(','.join(bot.config['channels']))

def joinAfterConnect(bot):
    thread.start_new_thread(joinAfterConnectThread, (bot,))

def init(bot):
    bot.events.register('postConnect', joinAfterConnect)

def close(bot):
    bot.events.unregister('postConnect', joinAfterConnect)
