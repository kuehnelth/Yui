#!/usr/bin/python
# -*- coding: utf-8 -*-

import sqlite3
import os

rules = {
        "n":"AND wordtype LIKE '%n.%'",
        "v":"AND wordtype LIKE '%v.%'",
        "adv":"AND wordtype LIKE '%adv.%'",
        "adj":"AND wordtype LIKE '%a.%'",
        "ing":"AND wordtype LIKE '%a.%' AND word LIKE '%ing'",
        "prep":"AND wordtype LIKE '%prep.%'",
        "pron":"AND wordtype LIKE '%pron.%'",
}


def racron(bot, msg):
    args = msg.msg.split(' ')
    if len(args) < 2 or args[0] != '!acr':
        return

    if len(args[1]) > 10:
        bot.sendChannelMessage(msg.replyTo, msg.user+': fuck off')
        return


    arg = 1
    str = ''
    path = os.path.join(os.path.dirname(__file__),'dict.sqlite')
    con = sqlite3.connect(path)
    with con:
        for c in args[1]:
            rule = ""
            arg += 1
            if arg < len(args):
                if args[arg] in rules:
                    rule = rules[args[arg]]
                else:
                    str += args[arg] + ' '
                    continue;
            cur = con.cursor()
            cur.execute("SELECT LOWER(word) FROM entries WHERE LOWER(word) LIKE '"+c+"%' "+rule+" ORDER BY RANDOM() LIMIT 1;")
            row = cur.fetchone()
            if row != None:
                str += (row[0] + ' ')
    bot.sendChannelMessage(msg.replyTo, str)


def init(bot):
    bot.events.register('channelMessageReceive',racron)

def close(bot):
    bot.events.unregister('channelMessageReceive',racron)
