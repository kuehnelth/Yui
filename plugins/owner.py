#!/usr/bin/python

def ownercmd(bot,msg):
    if msg.user != bot.owner:
        return

    split = msg.msg.split(' ', 1)
    if len(split) > 1 and split[0] == '!join':
        bot.join(split[1])
    elif split[0] == '!part':
        if len(split) > 1:
            bot.part(split[1])
        else:
            bot.part(msg.channel)
    elif split[0] == '!quit':
        if len(split) > 1:
            bot.quit(split[1])
        else:
            bot.quit('')
    elif len(split) > 1 and split[0] == '!nick':
        bot.setNick(split[1])
    elif len(split) > 1 and split[0].startswith('!echo'):
            split = split[1].split(' ')
            if len(split) > 1:
                bot.sendMsg(split[0], split[1])

def list(bot, msg):
    if msg.user == bot.owner:
        for cmd in bot.onMsgHandlers:
            bot.sendMsg(msg.channel, cmd.match)

def init(bot):
    bot.events['channelMessage'].append(ownercmd)
