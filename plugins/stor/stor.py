#!/usr/bin/python

import os
import collections
import re

storDir = ''
storList = {}

msgDeque = {}

def bufferMsgs(msg):
    global msgDeque
    chan = msg.channel
    text = '<%s> %s' % (msg.user, msg.msg)
    if chan not in msgDeque:
        msgDeque[chan] = collections.deque(maxlen=200)
    msgDeque[chan].append(text)

def stor(bot, msg):
    global storList
    global storDir

    if msg.msg.startswith('!sto'):
        isOwner = msg.user == bot.owner
        split = msg.msg.split(' ')

        #list tags and stors in them
        if len(split) < 2:
            l = []
            for t, i in storList.items():
                l.append('%s (%d)' % (t, len(i)))
            bot.sendMsg(msg.replyTo, 'tags: ' + ', '.join(l))
        else:
            #figure out parameters
            tag = None
            lineNr = 0
            lineCnt = 1
            split.pop(0)
            strip = split[0].lstrip('-+')
            if not strip.isdigit():
                tag = split[0]
                split.pop(0)
            try:
                if len(split) > 0:
                    lineNr = int(split[0].lstrip('-+'))
                    split.pop(0)
                if len(split) > 0:
                    lineCnt = int(split[0])
            except Exception as ex:
                pass

            #TODO: do something more optimised than copying the whole thing to a list...
            #(slicing doesn't work on deques)
            if msg.channel in msgDeque:
                lst = list(msgDeque[msg.channel])
            else:
                lst = []

            #check line number boundaries
            if lineNr > len(lst) or lineCnt > lineNr:
                bot.sendMsg(msg.replyTo, "I have no memory of this")
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
            bot.sendMsg(msg.replyTo, 'stored "%s"' % l)

    #push the received message into the buffer
    bufferMsgs(msg)


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

def getLinks(channel):
    regex = r'(https?://\S+)'
    links = []
    global msgDeque
    if not channel in msgDeque:
        return []
    for l in msgDeque[channel]:
        links.append(re.findall(regex, l))
    return links

def addStor(tag, msg):
    global storList
    global storDir
    if not tag:
        tag = 'no_tag'

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
    bot.events['channelMessage'].append(stor)

