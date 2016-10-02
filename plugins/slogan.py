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
    u"I'd walk a mile for a {0}.",
    u"Between {0} and madness lies obsession.",
    u"Between love and madness lies {0}.",
    u"Don't be {0}.",
    u"Outwit. Outplay. {0}.",
    u"Save {0}. Live Better.",
    u"If you want to impress {0}, put him on your Black list.",
    u"The {0} is always and completely {0}!",
    u"The customer is always and completely {0}!",
    u"When there is no {0}.",
    u"At the heart of the {0}.",
    u"The greatest tragedy is {0}.",
    u"{0} is no substitute.",
    u"Impossible is {0}.",
    u"{0} is the path to joy.",
    u"Pleasure is the path to {0}.",
    u"Let your {0} do the walking.",
    u"Because {0}'s complicated enough.",
    u"Connecting {0}.",
    u"{0}. It's a Mind Game.",
    u"Power, beauty and {0}.",
    u"{0}'s everywhere you want to be.",
    u"Reach out and touch {0}.",
    u"Get N or get {0}."
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
