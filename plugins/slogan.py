#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
import random

slogans = [
    u"Melts in {0}'s Mouth, Not in Your Hands",
    u"Just Do {0}",
    u"Shave Time. Shave {0}.",
    u"Because {0}'s Worth It",
    u"There are some things {0} can't buy. For everything else, there's MasterCard.",
    u"The Ultimate {0}ing Machine",
    u"Every {0} Helps",
    u"A {0} is Forever",
    u"Betcha Can't Eat Just {0}",
    u"Vorsprung durch {0}",
    u"{0} Runs on Dunkin",
    u"America Runs on {0}",
    u"I'm Lovin' {0}",
    u"{0}'s Lovin' It",
    u"All the {0} That's Fit to Print",
    u"Maybe she's born with it. Maybe it's {0}.",
    u"Don´t leave home without {0}",
    u"Think {0}.",
    u"I'd walk a mile for a {0}."
]

def slogan(bot, msg):
    if not msg.msg.startswith("!slogan"):
        return
    name = msg.user
    split = msg.msg.split(' ', 1)
    if len(split) > 1:
        name = split[1]
    response = random.choice(slogans)
    formatted = response.format(name)
    bot.sendChannelMessage(msg.replyTo,'"%s"' % formatted)

def init(bot):
    bot.events.register('channelMessageReceive', slogan)

def close(bot):
    bot.events.unregister('channelMessageReceive', slogan)
