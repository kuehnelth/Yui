#!/usr/bin/python

def join(bot,msg):
    if msg.user == bot.owner:
        bot.join(msg.msg.split(' ')[1])

def part(bot,msg):
    if msg.user == bot.owner:
        split = msg.msg.split(' ')
        if len(split) > 1:
            bot.part(split[1])
        else:
            bot.part(msg.channel)

def quit(bot,msg):
    if msg.user == bot.owner:
        reason = msg.msg.split(' ')[1] if ' ' in msg.msg else ''
        bot.quit(reason)

def nick(bot, msg):
    if msg.user == bot.owner:
        split = msg.msg.split(' ')
        if len(split) > 1:
            bot.setNick(split[1])

def echo(bot, msg):
    print msg
    if msg.user == bot.owner:
        split = msg.msg.split(' ')
        if len(split) > 1:
            chan = split[0].split('#',1)
            chan = chan[1] if len(chan) > 1 else msg.channel
            if chan == bot.nick:
                chan = msg.user
            bot.sendMsg(chan, split[1])

def list(bot, msg):
    if msg.user == bot.owner:
        for cmd in bot.onMsgHandlers:
            bot.sendMsg(msg.channel, cmd.match)

def init(bot):
    bot.registerOnMsg('!join ', join)
    bot.registerOnMsg('!part', part)
    bot.registerOnMsg('!quit', quit)
    bot.registerOnMsg('!nick ', nick)
    bot.registerOnMsg('!echo', echo)
    bot.registerOnMsg('!list', list)
