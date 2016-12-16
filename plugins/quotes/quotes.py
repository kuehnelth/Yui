#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import random
import csv

quoteDir = ''
quoteList = {}

def quote(bot, msg):
    global quoteList
    global quoteDir

    isMod = msg.user in bot.config['moderators'] or msg.user in bot.config['admins']

    split = list(csv.reader([msg.msg], delimiter=' ', quotechar='"', skipinitialspace=True))[0]

    #list tags and quotes in them
    if len(split) >= 1 and split[0] == '!qtags':
        l = []
        for t, i in quoteList.items():
            l.append('%s(%d)' % (t, len(i)))
        bot.sendMessage(msg.replyTo, 'Tags: ' + ', '.join(l))
        return

    #store a quote
    if isMod and len(split) > 1 and split[0] == '!qadd':
        #figure out parameters
        tag = msg.channel #default tag to channel name
        content = split[1]

        if len(split) > 2:
            tag = split[1]
            content = split[2]
            #don't let people store quotes in some channel's specific tag
            if tag.startswith('#'):
                bot.sendMessage(msg.replyTo, 'No.')
                return

        storeQuote(tag, content)
        bot.sendMessage(msg.replyTo, 'Stored quote in [%s]' % tag)
        return

    #recall quote
    if len(split) >= 1 and split[0] == '!quote':
        tag = msg.channel #default tag to channel name

        if len(split) > 1:
            tag = split[1]
        if tag not in quoteList or len(quoteList[tag]) < 1:
            bot.sendMessage(msg.replyTo, 'No tag named "%s" :(' % tag)
        else:
            l = len(quoteList[tag])
            rnd = random.randint(0,l-1)
            rcl = quoteList[tag][rnd]
            bot.sendMessage(msg.replyTo, 'Quote for [%s] (%d/%d): %s' % (tag,rnd+1,l,rcl))
        return

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
    bot.events.register('messageRecv',quote)

def close(bot):
    bot.events.unregister('messageRecv', quote)
