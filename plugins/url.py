#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
import urllib2

from HTMLParser import HTMLParser

class TitleParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.reading = False
        self.done = False
        self.title = ''

    def handle_starttag(self, tag, attrs):
        if tag == 'title':
            self.reading = True

    def handle_endtag(self, tag):
        if tag == 'title':
            self.reading = False
            self.done = True

    def handle_data(self, data):
        if self.reading:
            self.title += data

    def handle_charref(self, ref):
        if self.reading:
            self.handle_entityref('#' + ref)

    def handle_entityref(self, ref):
        if self.reading:
            self.title += '&%s;' % ref


def getUrlTitle(url, enc=['utf8', 'shift-jis', 'ISO-8859', 'Windows-1251', 'euc-jp']):
    title = ''
    parser = TitleParser()
    try:
        resp = urllib2.urlopen(url)

        #try the charset set in the html header first, if there is one
        #if 'content-type' in resp.headers:
        #    enc.insert(0,enc.append(resp.headers['content-type'].split('charset=')[-1]))

        #read in chunks, up to 1mb
        chunkSize = 1024
        for i in range(0, 1024*1024*1024, chunkSize):
            parser.feed(resp.read(chunkSize))
            if parser.done:
                title = parser.title
                break
        parser.close()
    except Exception as ex:
        return None
    else:
        if len(title) > 0:
            for e in enc:
                try:
                    dec = title.decode(e)
                    dec = parser.unescape(dec)
                    return dec
                except Exception as ex:
                    pass
        return title

def url(bot, msg):
    #don't react to stuff sent by the bot
    if msg.user == bot.nick:
        return

    #find urls in channel message
    regex = r'(https?://\S+)'
    urls = re.findall(regex, msg.msg)
    for u in urls:
        title = getUrlTitle(u)
        #don't say anything, if we can't figure out the title
        if not title:
            return
        bot.sendChannelMessage(msg.replyTo, title)


def init(bot):
    bot.events.register('channelMessage',url)

def close(bot):
    bot.events.unregister('channelMessage',url)
