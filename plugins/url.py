#!/usr/bin/python
import re
import urllib2

def getUrlTitle(url):
    regex = r'<title>(.+?)</title>'
    data = urllib2.urlopen(url).read(1024*8)
    title = re.findall(regex, data, re.IGNORECASE)
    if len(title) > 0:
        return title[0]

def url(bot, msg):
    regex = r'(https?://\S+)'
    urls = re.findall(regex, msg.msg)
    for u in urls:
        bot.sendMsg(msg.replyTo, 'Title: %s' % getUrlTitle(u))


def init(bot):
    bot.events['channelMessage'].append(url)
