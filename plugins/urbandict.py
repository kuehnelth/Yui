#!/usr/bin/python
# -*- coding: utf-8 -*-


import urllib2
import json
import csv

#stupid hack taken from python.org csv examples, to get unicode to work
def unicode_csv_reader(unicode_csv_data, dialect=csv.excel, **kwargs):
    # csv.py doesn't do Unicode; encode temporarily as UTF-8:
    csv_reader = csv.reader(utf_8_encoder(unicode_csv_data),
                            dialect=dialect, **kwargs)
    for row in csv_reader:
        # decode UTF-8 back to Unicode, cell by cell:
        yield [unicode(cell, 'utf-8') for cell in row]

def utf_8_encoder(unicode_csv_data):
    for line in unicode_csv_data:
        yield line.encode('utf-8')

def ud(bot,msg):
    if not msg.msg.startswith('!ud '):
        return

    #split = msg.msg.split(' ')
    split = unicode_csv_reader([msg.msg], delimiter=' ', quotechar='"', skipinitialspace=True).next()
    if len(split) < 2:
        return

    word = split[1]
    definition = None
    idx = 0

    try:
        if len(split) > 2:
            idx = int(split[2]) - 1
        url = 'http://api.urbandictionary.com/v0/define?term=%s' % urllib2.quote(word.encode('utf-8'))
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
    bot.events.register('channelMessageReceive',ud)

def close(bot):
    bot.events.unregister('channelMessageReceive',ud)
