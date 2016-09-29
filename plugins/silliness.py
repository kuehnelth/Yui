#!/usr/bin/python
# -*- coding: utf-8 -*-

import re

#responds to any message starting with the bot's nick
#and otherwise only contains spaces or the caracters <>!?.o
#which allows for some things like \o/ or >.< or !?!?!
#if that's the case, the bot answers the same back to whomever mentioned him
def sillyAnswers(bot,msg):
    botnick = bot.nick.lower()
    if msg.msg.lower().startswith(botnick) and msg.user.lower() != botnick:
        suffix = msg.msg[len(botnick):]
        if not suffix or re.match(r'^[o<>/\\!\?\. ]+$',suffix) is not None:
            bot.sendChannelMessage(msg.replyTo, msg.user + suffix)

def init(bot):
    bot.events.register('channelMessageReceive',sillyAnswers)

def close(bot):
    bot.events.unregister('channelMessageReceive',sillyAnswers)
