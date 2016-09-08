#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
import urllib2

def getUrlTitle(url, enc=['utf8', 'shift-jis', 'euc-jp']):
    regex = r'<title>(.+?)</title>'

    try:
        resp = urllib2.urlopen(url)
        content = ''
        if 'content-type' in resp.headers:
            enc.append(resp.headers['content-type'].split('charset=')[-1])
        content = resp.read(1024*2)
        title = re.findall(regex, content, re.IGNORECASE)
    except Exception as ex:
        return None
    else:
        if len(title) > 0:
            for e in enc:
                try:
                    return title[0].decode(e)
                except Exception as ex:
                    pass

def url(bot, msg):
    #don't react to stuff sent by the bot
    if msg.user == bot.nick:
        return

    regex = r'(https?://\S+)'
    urls = re.findall(regex, msg.msg)
    for u in urls:
        title = getUrlTitle(u)
        #don't say anything, if we can't figure out the title
        if not title:
            return
        print repr(title)
        bot.sendChannelMessage(msg.replyTo, title)


def init(bot):
    bot.events.register('channelMessage',url)

def close(bot):
    bot.events.unregister('channelMessage',url)
