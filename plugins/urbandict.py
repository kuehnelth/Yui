#!/usr/bin/python
# -*- coding: utf-8 -*-


import urllib2
import json

def ud(bot,msg):
    if not msg.msg.startswith('!ud') or msg.user == bot.nick:
        return

    split = msg.msg.split(' ')
    if len(split) < 2:
        return

    word = split[1]
    definition = None
    idx = 0

    try:
        if len(split) > 2:
            idx = int(split[2]) - 1
        url = 'http://api.urbandictionary.com/v0/define?term=%s' % word
        resp = urllib2.urlopen(url)
        #get encoding
        enc = resp.headers['content-type'].split('charset=')[-1]
        content = unicode(resp.read(),enc)
        js = json.loads(content)
        definition = js['list'][idx]['definition']
    except Exception as ex:
        pass

    if not definition:
        answer = 'No results for "%s" :(' % word
    else:
        answer = '"%s": %s' % (word, definition)
    bot.sendChannelMessage(msg.replyTo, answer)

def init(bot):
    bot.events.register('channelMessage',ud)

def close(bot):
    bot.events.unregister('channelMessage',ud)
