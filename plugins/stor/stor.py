#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import collections
import re
import random

storDir = ''
storList = {}

msgDeque = {}

def bufferMsgs(msg):
    global msgDeque
    chan = msg.replyTo
    text = u'<%s> %s' % (msg.user, msg.msg)
    if chan not in msgDeque:
        msgDeque[chan] = collections.deque(maxlen=200)
    msgDeque[chan].append(text)

def stor(bot, msg):
    global storList
    global storDir

    isOwner = msg.user == bot.owner

    split = msg.msg.split(' ')

    #recall random message
    if msg.msg.startswith('!rcl'):
        tag = msg.channel #default tag to channel name
        if len(split) > 1:
            tag = split[1]
        if tag not in storList or len(storList[tag]) < 1:
            bot.sendChannelMessage(msg.replyTo, u'I have no memory of this')
        else:
            l = len(storList[tag])
            rnd = random.randint(0,l-1)
            rcl = storList[tag][rnd]
            bot.sendChannelMessage(msg.replyTo, u'Stored msg (%d/%d): %s' % (rnd+1,l,rcl))

    #store one or more messages
    elif msg.msg.startswith('!sto'):
        #list tags and stors in them
        if len(split) < 2:
            l = []
            for t, i in storList.items():
                l.append(u'%s(%d)' % (t, len(i)))
            bot.sendChannelMessage(msg.replyTo, u'Tags: ' + ', '.join(l))
        #add a message
        else:
            #figure out parameters
            tag = msg.channel #default tag to channel name
            lineNr = 0 #from which message (counting backwards through the log)
            lineCnt = 1 #how many messages (counting forwards starting at lineNr)
            split.pop(0)
            strip = split[0].lstrip('-+')
            if not strip.isdigit():
                tag = split[0]
                split.pop(0)

                #don't let people store things in some channel's specific tag
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

            addStor(tag, l)
            bot.sendChannelMessage(msg.replyTo, 'Stored [%s] "%s"' % (tag,l))

    #push the received message into the buffer
    bufferMsgs(msg)


#load existing stored messages from disk
def loadStors():
    global storDir
    global storList

    for f in os.listdir(storDir):
        path = os.path.join(storDir, f)
        tag, ext = os.path.splitext(f)
        if ext == '.txt':
            storList[tag] = []
            try:
                file = open(path,'r')
                for line in file:
                    line = line.rstrip('\r\n')
                    storList[tag].append(line)
                file.close()
            except Exception as ex:
                pass

#store a message to a specified tag
def addStor(tag, msg):
    global storList
    global storDir

    try:
        file = open(os.path.join(storDir, tag) + '.txt', 'a')
        file.writelines(msg+'\n')
        file.close()
    except Exception as ex:
        pass
    else:
        if tag not in storList:
            storList[tag] = []
        storList[tag].append(msg)

def init(bot):
    global storDir
    storDir = os.path.dirname(__file__)
    storDir = os.path.join(storDir, 'stors')
    if not os.path.exists(storDir):
        os.makedirs(storDir)
    loadStors()
    bot.events.register('channelMessage',stor)

def close(bot):
    bot.events.unregister('channelMessage', stor)
