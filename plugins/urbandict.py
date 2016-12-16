#!/usr/bin/python
# -*- coding: utf-8 -*-


import urllib.request
import json
import csv

def ud(bot,msg):
    if not msg.msg.startswith('!ud '):
        return

    #split = msg.msg.split(' ')
    split = list(csv.reader([msg.msg], delimiter=' ', quotechar='"', skipinitialspace=True))[0]
    if len(split) < 2:
        return

    word = split[1]
    definition = None
    idx = 0

    try:
        if len(split) > 2:
            idx = int(split[2]) - 1
        url = 'http://api.urbandictionary.com/v0/define?term=%s' % urllib.request.quote(word.encode('utf-8'))
        resp = urllib.request.urlopen(url)
        #get encoding
        enc = resp.headers['content-type'].split('charset=')[-1]
        content = resp.read().decode(enc)
        js = json.loads(content)
        definition = js['list'][idx]['definition']
    except Exception as ex:
        print(ex)

    if not definition:
        answer = 'No results for "%s" :(' % word
    else:
        answer = '"%s": %s' % (word, definition)
    bot.sendMessage(msg.replyTo, answer)

def init(bot):
    bot.events.register('messageRecv',ud)

def close(bot):
    bot.events.unregister('messageRecv',ud)
