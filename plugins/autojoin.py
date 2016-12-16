#!/usr/bin/python

def join(bot):
    if 'channels' in bot.config:
        for chan in bot.config['channels']:
            bot.join(chan)

def init(bot):
    bot.events.register('postConnect', join)

def close(bot):
    bot.events.unregister('postConnect', join)
