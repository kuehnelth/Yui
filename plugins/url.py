#!/usr/bin/python
import re
import urllib2

def getUrlTitle(url, enc=['utf8', 'shift-jis', 'euc-jp']):
    regex = r'<title>(.+?)</title>'

    try:
        data = urllib2.urlopen(url).read(1024*8)
        title = re.findall(regex, data, re.IGNORECASE)
    except Exception as ex:
        return None
    else:
        if len(title) > 0:
            for e in enc:
                try:
                    return title[0].decode(e).encode('utf8')
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
        if not title:
            title = 'No idea :('
        bot.sendChannelMessage(msg.replyTo, title)


def init(bot):
    bot.events.register('channelMessage',url)

def close(bot):
    bot.events.unregister('channelMessage',url)
