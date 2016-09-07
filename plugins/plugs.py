#!/usr/bin/python

def plugs(bot, msg):
    if msg.user != bot.owner:
        return
    split = msg.msg.split(' ')
    if len(split) < 2:
        return;
    if split[0] == '!plug':
        if bot.pluginLoader.load(split[1],bot):
            bot.sendChannelMessage(msg.replyTo, 'Loaded %s' % split[1])
        else:
            bot.sendChannelMessage(msg.replyTo, 'Couldn\'t load %s' % split[1])
    elif split[0] == '!unplug':
        if bot.pluginLoader.unload(split[1],bot):
            bot.sendChannelMessage(msg.replyTo, 'Unloaded %s' % split[1])
        else:
            bot.sendChannelMessage(msg.replyTo, 'Couldn\'t unload %s' % split[1])

def init(bot):
    bot.events.register('channelMessage',plugs)

def close(bot):
    bot.events.unregister('channelMessage',plugs)
