#!/usr/bin/env python
# -*- coding: utf-8 -*-

import imp
import os
import re
import json
import irc.bot
import irc.strings



from collections import namedtuple
from collections import deque
from collections import OrderedDict

IrcMsg = namedtuple('IrcMsg', ['channel', 'user', 'msg', 'replyTo'])

class EventManager(list):
    def __call__(self, *args, **kwargs):
        for handler in self:
            handler(*args, **kwargs)

    def __init__(self):
        self.events = {}
        self.__eventBuffer = deque()

    #register a callback function to an event
    #simply creates the event, if no function is given
    def register(self, eventName, function = None, priority = 9999):
        if not eventName in self.events:
            self.events[eventName] = []
        if not function:
            return True
        self.events[eventName].append((priority, function))

    #unregister a function form an event
    def unregister(self, eventName, function):
        if not eventName in self.events:
            return False
        self.events[eventName] = [(prio, func) for prio, func in self.events[eventName] if func != function]

    #execute an event
    def fire(self, eventName, *args, **kwargs):
        if not eventName in self.events:
            return

        #currently processing an event, so push the new one into the queue
        if len(self.__eventBuffer) > 0:
            self.__eventBuffer.append((eventName, args, kwargs))
            return

        #push current event onto queue and process it, and all further added events
        self.__eventBuffer.append((eventName, args, kwargs))

        #store one exception and re-raise it after processing all event handlers
        #so we don't skip any handlers if something goes wrong in only one of them
        #TODO: make this less of an ugly hack
        exception = None

        while len(self.__eventBuffer) > 0:
            en, a, kwa = self.__eventBuffer[0]
            for prio, func in self.events[en]:
                #try:
                    func(*a, **kwa)
                #except Exception as ex:
                #    exception = ex
            self.__eventBuffer.popleft()

        #raise the last exception we saw, if we had one
        if exception:
            raise exception

class PluginLoader(object):
    #root: root dir for plugins
    def __init__(self, root):
        self.plugins = {}
        self.rootDir = root

    #loads a given .py file as a plugin
    #calls its init() function, if it has one
    #if a path to a directory is given, it tries to load a .py file in that,
    #if it has the same name as the dir
    def load(self, name, *args, **kwargs):
        name = os.path.basename(name)
        filepath = os.path.join(self.rootDir, name)

        #try to load plugin in subdir
        if os.path.isdir(filepath):
            filepath = os.path.join(filepath,name)

        filepath += '.py'
        if not os.path.exists(filepath):
            return False

        #unload and then re-load, if the plugin is already loaded
        if name in self.plugins:
            self.unload(name, *args, **kwargs)

        plugin = imp.load_source(name, filepath)

        #check if the plugin contains an init() function
        #and call it
        if plugin and callable(getattr(plugin, "init", None)):
            plugin.init(*args,**kwargs)
            self.plugins[name] = plugin
        return True

    #loads all plugins in the plugin root
    def loadAll(self, *args, **kwargs):
        for f in os.listdir(self.rootDir):
            if os.path.isdir(os.path.join(self.rootDir,f)) or f.endswith('.py'):
                self.load(f.rstrip('.py'), *args, **kwargs)

    #unload a plugin given its name
    def unload(self, name, *args, **kwargs):
        plugin = self.plugins.pop(name, None)
        if plugin:
            if callable(getattr(plugin, "close", None)):
                plugin.close(*args, **kwargs)
            return True
        return False

    def unloadAll(self, *args, **kwargs):
        plugs = list(self.plugins.keys())
        for name in plugs:
            self.unload(name, *args, **kwargs)



class IrcBot(irc.bot.SingleServerIRCBot):
    def __init__(self, configPath):
        self.configPath = configPath
        self.config = None

        self.plugins = None

        #register some events
        self.events = EventManager()
        self.events.register('messageSend')
        self.events.register('messageRecv')
        self.events.register('log')
        self.events.register('postConnect')
        self.events.register('disconnect')

        #load config
        if not self.loadConfig():
            quit()

        #load plugins
        if not self.loadPlugins():
            quit()

        #start server
        irc.bot.SingleServerIRCBot.__init__(self, [(self.config['server'], self.config['port'])], self.config['nick'], self.config['nick'])

    def dbg(self,conn,event):
        #print(conn)
        #print(event)
        return

    def on_join(self,conn,event):
        self.dbg(conn,event)
    def on_namreply(self,conn,event):
        self.dbg(conn,event)
    def on_part(self,conn,event):
        self.dbg(conn,event)
    def on_nick(self,conn,event):
        self.dbg(conn,event)
    def on_mode(self,conn,event):
        self.dbg(conn,event)
    def on_kick(self,conn,event):
        self.dbg(conn,event)

    def on_disconnect(self,conn,event):
        self.dbg(conn,event)
        self.log('info','disconnected')
        self.fireEvent('disconnect', self)

    def on_privmsg(self,conn,event):
        self.dbg(conn,event)
        evMsg = IrcMsg(channel=conn.get_nickname(),
                        user=event.source.nick,
                        msg=event.arguments[0],
                        replyTo=event.source.nick)
        self.fireEvent('messageRecv', self, evMsg)

    def on_pubmsg(self,conn,event):
        self.dbg(conn,event)
        evMsg = IrcMsg(channel=event.target,
                        user=event.source.nick,
                        msg=event.arguments[0],
                        replyTo=event.target)
        self.fireEvent('messageRecv', self, evMsg)

    #servers tend to not take joins etc. before they sent a welcome msg
    def on_welcome(self,conn,event):
        self.dbg(conn,event)
        self.log('info','connected!')
        self.fireEvent('postConnect', self)

    #append our nick is in use, append a _
    def on_nicknameinuse(self, conn, event):
        self.dbg(conn,event)
        self.log('warn','nick %s already in use' % self.getNick())
        self.setNick(self.getNick() + '_')

    def on_connect(self, conn, event):
        return

    #wrapper for EventManager.fire()
    #to handle any exceptions (i.e. crash-proofing plugins a bit)
    def fireEvent(self, eventName, *args, **kwargs):
        try:
            self.events.fire(eventName, *args, **kwargs)
        except Exception as ex:
            self.log('error', 'Exception occurred processing event "%s": %s' % (eventName, repr(ex)))

    #prints to stdout and fires the 'log' event
    def log(self, level, msg):
        print('[%s] %s'% (level, msg))
        self.fireEvent('log',self,level,msg)

    #send a message to a channel/user
    def sendMessage(self, channel, msg):
        self.connection.privmsg(channel, msg)
        evMsg = IrcMsg(channel = channel,
                        user= self.getNick(),
                        msg = msg,
                        replyTo = channel)
        self.fireEvent('channelMessageSend',self,evMsg)

    #get the current bot's nick
    def getNick(self):
        return self.connection.get_nickname()

    #set the bot's nick
    def setNick(self, nick):
        self.log('info',"Changing nick to '%s'" % nick)
        self.connection.nick(nick)

    #join a channel
    def join(self, channel):
        self.log('info','Joining channel %s'%channel)
        self.connection.join(channel)

    #leave a channel
    def part(self, channel, msg = ""):
        self.log('info','Leaving channel %s'%channel)
        self.connection.part(channel,msg)

    #quit from the server
    #also ends the main loop gracefully
    def quit(self, reason):
        self.log('info', 'Quit (%s)' % reason)
        self.connection.quit(reason)
        self.die()

    def loadConfig(self):
        try:
            with open(self.configPath) as f:
                self.config = json.load(f, object_pairs_hook=OrderedDict)
        except Exception as ex:
            self.log('error','Exception occurred while loading config: %s' % repr(ex))
            return False
        return True

    def saveConfig(self):
        self.log('info', 'Saving config')
        try:
            with open(self.configPath, 'w') as f:
                jsonStr = json.dumps(self.config, ensure_ascii=False, indent=4, separators=(',',': '))
                f.write(jsonStr.encode('utf-8'))
        except Exception as ex:
            self.log('error', 'Exception occurred while saving config: %s' % repr(ex))
            return False
        return True

    #load all plugins
    def loadPlugins(self):
        self.log('info', 'Loading plugins')
        try:
            self.plugins = PluginLoader(self.config['pluginDir'])
            for p in self.config['pluginAutoLoad']:
                self.plugins.load(p, self)
        except Exception as ex:
            self.log('fatal', 'Exception occurred while loading plugins: %s' % repr(ex))
            return False
        return True


    #some cleanup on quit
    def on_quit(self,conn,event):
        #unload all plugins
        self.plugins.unloadAll(self)
        #save the config, in case it was modified
        self.saveConfig()

def main():
    #ugly commandline parsing
    import sys
    conf = "config.json"
    if len(sys.argv) > 1:
        conf = sys.argv[1]
    bot = IrcBot(conf)
    bot.start()

if __name__ == "__main__":
    main()
