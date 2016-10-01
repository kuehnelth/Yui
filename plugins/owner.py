#!/usr/bin/python
# -*- coding: utf-8 -*-

def admin(bot,msg):
    if msg.msg.startswith('!admin'):
        bot.sendChannelMessage(msg.replyTo, u'Admins: [%s], Mods: [%s]' % (','.join(bot.config['admins']), ','.join(bot.config['moderators'])))
        return

    if msg.msg.startswith('!source'):
        bot.sendChannelMessage(msg.replyTo, u'https://github.com/Rj48/ircbot')
        return

    #admin commands below
    if msg.user not in bot.config['admins']:
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
            split = split[1].split(' ', 1)
            if len(split) > 1:
                bot.sendChannelMessage(split[0], split[1])

def init(bot):
    bot.events.register('channelMessageReceive',admin)

def close(bot):
    bot.events.unregister('channelMessageReceive',admin)
