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

def urlEncodeNonAscii(string):
    return re.sub('[\x80-\xFF]', lambda c: '%%%02x' % ord(c.group(0)), string)

def getUrlTitle(url, enc=['utf8', 'shift-jis', 'ISO-8859', 'Windows-1251', 'euc-jp']):
    #test if it's a valid URL and encode it properly, if it is
    parts = urllib2.urlparse.urlparse(url)
    if not ((parts[0] == 'http' or parts[0] == 'https') and parts[1] and parts[1] != 'localhost' and not parts[1].split('.')[-1].isdigit()):
        return None

    #handle unicode URLs
    url = urllib2.urlparse.urlunparse(
            p.encode('idna') if i == 1 else urlEncodeNonAscii(p.encode('utf-8'))
            for i, p in enumerate(parts)
    )

    title = None
    parser = TitleParser()
    try:
        resp = urllib2.urlopen(url, timeout=5)

        #try the charset set in the html header first, if there is one
        #if 'content-type' in resp.headers:
        #    enc.insert(0,enc.append(resp.headers['content-type'].split('charset=')[-1]))

        #read in chunks, up to 1mb
        chunkSize = 1024
        for i in range(0, 1024*1024*1024, chunkSize):
            chunk = resp.read(chunkSize)
            parser.feed(chunk)
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
    words = msg.msg.split(' ')
    titles = []
    maxUrls = 5
    foundTitle = False
    for w in words:
        maxUrls -= 1
        if maxUrls == 0:
            break

        title = getUrlTitle(w)
        if title:
            titles.append('"%s"' % title)
            foundTitle = True
        else:
            titles.append('[no title]')

    #don't say anything, if we couldn't get any titles
    if foundTitle:
        concat = ', '.join(titles)
        bot.sendChannelMessage(msg.replyTo, concat)


def init(bot):
    bot.events.register('channelMessage',url)

def close(bot):
    bot.events.unregister('channelMessage',url)
