#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import collections
import re
import random

quoteDir = ''
quoteList = {}

msgDeque = {}

def bufferMsgs(msg):
    global msgDeque
    print u'<%s> %s' % (msg.user, msg.msg)
    chan = msg.replyTo
    text = u'<%s> %s' % (msg.user, msg.msg)
    if chan not in msgDeque:
        msgDeque[chan] = collections.deque(maxlen=200)
    msgDeque[chan].append(text)

def printQuote(bot,msg):
    global quoteList
    global quoteDir

    if msg.user == bot.nick:
        return

    isOwner = msg.user == bot.owner

    split = msg.msg.split(' ')

    #recall random message
    if msg.msg.startswith('!quote'):
        tag = msg.channel #default tag to channel name
        if len(split) > 1:
            tag = split[1]
        if tag not in quoteList or len(quoteList[tag]) < 1:
            bot.sendChannelMessage(msg.replyTo, u'I have no memory of this')
        else:
            l = len(quoteList[tag])
            rnd = random.randint(0,l-1)
            rcl = quoteList[tag][rnd]
            bot.sendChannelMessage(msg.replyTo, u'Quote for "%s" (%d/%d): %s' % (tag,rnd+1,l,rcl))

def addQuote(bot, msg):
    global quoteList
    global quoteDir

    if msg.user == bot.nick:
        return

    isOwner = msg.user == bot.owner

    split = msg.msg.split(' ')

    #store one or more quotes
    if msg.msg.startswith('!qadd'):
        #list tags and quotes in them
        if len(split) < 2:
            l = []
            for t, i in quoteList.items():
                l.append(u'%s(%d)' % (t, len(i)))
            bot.sendChannelMessage(msg.replyTo, u'Tags: ' + ', '.join(l))
            return

        #add a message
        #figure out parameters
        tag = msg.channel #default tag to channel name
        lineNr = 0 #from which message (counting backwards through the log)
        lineCnt = 1 #how many messages (counting forwards starting at lineNr)
        split.pop(0)
        strip = split[0].lstrip('-+')
        if not strip.isdigit():
            tag = split[0]
            split.pop(0)

            #don't let people store quotes in some channel's specific tag
            if tag.startswith('#'):
                bot.sendChannelMessage(msg.replyTo, u'No.')
                return
        try:
            if len(split) > 0:
                lineNr = int(split[0].lstrip('-+'))
                split.pop(0)
            if len(split) > 0:
                lineCnt = int(split[0])
        except Exception as ex:
            pass

        #don't allow people to arbitrarily long stuff
        if lineCnt > 10:
            bot.sendChannelMessage(msg.replyTo, u'No.')
            return

        #TODO: do something more optimised than copying the whole thing to a list...
        #(slicing doesn't work on deques)
        if msg.channel in msgDeque:
            lst = list(msgDeque[msg.channel])
        else:
            lst = []

        #check line number boundaries
        if lineNr > len(lst) or lineCnt > lineNr:
            bot.sendChannelMessage(msg.replyTo, u'I have no memory of this')
            return

        #add line/link
        if lineCnt == 1:
            l = lst[-lineNr]
        elif lineNr == lineCnt:
            l = ' '.join(lst[-lineNr:])
        else:
            l = ' '.join(lst[-lineNr:-lineNr+lineCnt])

        #TODO: trim string if too long?

        storeQuote(tag, l)
        bot.sendChannelMessage(msg.replyTo, 'Stored quote [%s] "%s"' % (tag,l))


def quote(bot, msg):
    addQuote(bot,msg)

    #push the received message into the buffer
    bufferMsgs(msg)


#load existing quotes
def loadQuotes():
    global quoteDir
    global quoteList

    for f in os.listdir(quoteDir):
        path = os.path.join(quoteDir, f)
        tag, ext = os.path.splitext(f)
        if ext == '.txt':
            quoteList[tag] = []
            try:
                file = open(path,'r')
                for line in file:
                    line = line.rstrip('\r\n')
                    quoteList[tag].append(line)
                file.close()
            except Exception as ex:
                pass

#store a message to a specified tag
def storeQuote(tag, msg):
    global quoteList
    global quoteDir

    try:
        file = open(os.path.join(quoteDir, tag) + '.txt', 'a')
        file.writelines(msg+'\n')
        file.close()
    except Exception as ex:
        pass
    else:
        if tag not in quoteList:
            quoteList[tag] = []
        quoteList[tag].append(msg)

def init(bot):
    global quoteDir
    quoteDir = os.path.dirname(__file__)
    quoteDir = os.path.join(quoteDir, 'quotes')
    if not os.path.exists(quoteDir):
        os.makedirs(quoteDir)
    loadQuotes()
    bot.events.register('channelMessage',quote)

def close(bot):
    bot.events.unregister('channelMessage', quote)
