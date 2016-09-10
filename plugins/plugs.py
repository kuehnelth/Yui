#!/usr/bin/python
# -*- coding: utf-8 -*-

def plugs(bot, msg):
    if msg.user != bot.owner:
        return
    split = msg.msg.split(' ')
    if len(split) < 2:
        return;

    plugName = split[1]

    #(re)load plugin
    if split[0] == '!plug':
        try:
            if bot.plugins.load(plugName,bot):
                bot.sendChannelMessage(msg.replyTo, 'Loaded %s' % plugName)
                return
        except Exception as ex:
            pass

        #plugin couldn't be loaded
        bot.sendChannelMessage(msg.replyTo, 'Couldn\'t load %s' % plugName)
        return

    #unload plugin
    elif split[0] == '!unplug':
        try:
            if bot.plugins.unload(split[1],bot):
                bot.sendChannelMessage(msg.replyTo, 'Unloaded %s' % plugName)
                return
        except Exception as ex:
            pass
        #plugin couldn't be properly unloaded
        bot.sendChannelMessage(msg.replyTo, 'Couldn\'t unload %s' % plugName)

def init(bot):
    bot.events.register('channelMessage',plugs)

def close(bot):
    bot.events.unregister('channelMessage',plugs)
