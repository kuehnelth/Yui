#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
import random

phrases = [
    ['hi', 'hello'],
    ['yo', 'sup'],
    ['hallo', 'tag', 'moin'],
    ['こんにちは', 'こんちわ'],
    ['よ', 'やぁ', 'おっす']
]

def getRandomExcept(arr, ex):
    if not ex in arr:
        return random.choice(arr)
    idx = arr.index(ex)
    arrEx = arr[:idx] + arr[idx+1:]
    return random.choice(arrEx)

def greetings(bot,msg):
    global phrases

    answer = None
    lower = msg.msg.lower()
    lower = re.sub('[!?\. ]', '', lower)
    for s in phrases:
        if lower in s:
            answer = getRandomExcept(s, lower)
    if answer:
        bot.sendMessage(msg.replyTo, answer)
        return

    #responds to any message starting with the bot's nick
    #and otherwise only contains spaces or the caracters <>!?.o
    #which allows for some things like \o/ or >.< or !?!?!
    #if that's the case, the bot answers the same back to whomever mentioned him
    botnick = bot.getNick()
    if msg.msg.lower().startswith(botnick):
        suffix = msg.msg[len(botnick):]
        if not suffix or re.match(r'^[o<>/\\!\?\. ]+$',suffix) is not None:
            bot.sendMessage(msg.replyTo, msg.user + suffix)
            return

def init(bot):
    bot.events.register('messageRecv',greetings)

def close(bot):
    bot.events.unregister('messageRecv',greetings)
