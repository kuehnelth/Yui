#!/usr/bin/python
# -*- coding: utf-8 -*-

import imp
import os
import socket, ssl
import time
import optparse
import re
from collections import namedtuple
from collections import deque

IrcMsg = namedtuple('IrcMsg', ['channel', 'user', 'msg', 'replyTo'])

IrcServerCmd = namedtuple('IrcServerCmd', ['prefix', 'cmd', 'args'])

#register (eventName, function, prio = lowest)
#unregister (eventName, function)
#fire (eventName, params)
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
                try:
                    func(*a, **kwa)
                except Exception as ex:
                    exception = ex
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
        for f in os.listdir(rootDir):
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
        plugs = self.plugins.keys()
        for name in plugs:
            self.unload(name, *args, **kwargs)



class IrcBot(object):
    def __init__(self):
        #parameter defaults
        self.server = 'localhost'
        self.port = 6667
        self.ssl = False
        self.nick = ''
        self.user = ''
        self.password = ''
        self.owner = ''
        self.socket = None
        self.quitting = False

        self.plugins = PluginLoader('plugins')

        #register some events
        self.events = EventManager()
        self.events.register('channelMessageSend');
        self.events.register('channelMessageReceive');
        self.events.register('log');
        self.events.register('rawSend');
        self.events.register('rawReceive');
        self.events.register('ircCmd');
        self.events.register('preConnect');

    #send a raw line to the server
    def sendRaw(self,msg):
        try:
            #strip newlines
            badChars = u'\r\n'
            stripped = re.sub(u'['+badChars+']+', '', msg)

            utf8 = stripped.encode('utf-8')

            #clamp length
            if utf8 > 400:
                utf8 = utf8[:400]

            self.socket.send(utf8+'\r\n')
        except TypeError as ex:
            self.log(u'error', u'Exception occurred sending data: %s' % repr(ex))
            return False
        self.fireEvent('rawSend',bot,msg)
        return True

    #wrapper for EventManager.fire()
    #to handle any exceptions (i.e. crash-proofing plugins a bit)
    def fireEvent(self, eventName, *args, **kwargs):
        try:
            self.events.fire(eventName, *args, **kwargs)
        except Exception as ex:
            self.log(u'error', u'Exception occurred processing event "%s": %s' % (eventName, repr(ex)))

    #prints to stdout and fires the 'log' event
    def log(self, level, msg):
        print '[%s] %s' % (level, msg)
        self.fireEvent('log',self,level,msg)

    #send a message to a channel/user
    def sendChannelMessage(self, channel, msg):
        self.sendRaw(u'PRIVMSG %s :%s' % (channel, msg))
        #fire channelMessage event for outgoing messages
        evMsg = IrcMsg(channel = channel,
                        user = self.nick,
                        msg = msg,
                        replyTo = channel)
        self.fireEvent('channelMessageSend',self,evMsg)

    #set the nick
    def setNick(self, nick):
        if not nick:
            self.log(u'warning',u'Tried setting nick to empty string')
            return False
        self.sendRaw(u'NICK %s' % nick)
        self.nick = nick
        return True

    #join a channel
    def join(self, channel):
        if not channel:
            self.log(u'warning',u'Tried joining channel without name')
            return False
        self.sendRaw(u'JOIN %s' % channel)
        return True

    #leave a channel
    def part(self, channel):
        if not channel:
            self.log(u'warning',u'Tried parting from channel without name')
            return False
        self.sendRaw(u'PART %s' % channel)
        return True

    #quit from the server
    #also ends the main loop gracefully
    def quit(self, reason):
        self.sendRaw(u'QUIT :%s' % reason)
        self.quitting = True
        self.log(u'info', u'Quit (%s)' % reason)

    #parse a command received from the server and split it into manageable parts
    #*inspired by* twisted's irc implementation
    def parseServerCmd(self,cmd):
        prefix = ''
        trailing = []
        if not cmd:
           return None
        if cmd[0] == ':':
            prefix, cmd = cmd[1:].split(' ', 1)
        if cmd.find(' :') != -1:
            cmd, trailing = cmd.split(' :', 1)
            args = cmd.split()
            args.append(trailing)
        else:
            args = cmd.split()
        command = args.pop(0)
        return IrcServerCmd(prefix, command, args)

    #handle a received command (that has been parsed by parseServerCmd())
    def handleCmd(self, cmd):
        #fire an event with the parsed cmd
        self.fireEvent('ircCmd', self, cmd)

        #handle pings
        if cmd.cmd == u'PING':
            self.sendRaw(u'PONG :%s' % cmd.args[0])

        #handle chat messages
        if cmd.cmd == u'PRIVMSG':
            channel = cmd.args[0]
            reply = channel #the channel/user you'd typically reply to using sendChannelMessage
            user = cmd.prefix.split(u'!')[0]
            if not reply.startswith(u'#'):
                reply = user #we're not in a channel, reply to the user directly
            msg = IrcMsg(channel = channel,
                         user = user,
                         msg = cmd.args[1],
                         replyTo = reply)
            self.fireEvent('channelMessageReceive',self,msg)

    #try to connect to a server
    #TODO: handle failed self.sendRaw calls somehow?
    def connect(self):
        if not self.user:
            self.log(u'fatal', u'No username defined')
            return False

        self.socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)

        #enable ssl
        if self.ssl:
            self.socket = ssl.wrap_socket(self.socket)

        self.log(u'info', u'Connecting to %s:%d' % (self.server, self.port))

        try:
            self.socket.connect((self.server, self.port))
        except Exception as ex:
            self.log(u'error',u'Exception occured while trying to connect: %s' % repr(ex))
            return False

        self.log(u'info',u'Connected!')

        if self.password:
            self.sendRaw('PASS %s' % self.password)

        #set the nick = username, if we don't have one configured
        if not self.nick:
            self.nick = self.user
        self.setNick(self.nick)
        self.sendRaw('USER %s 0 * :teh bot' % self.user)

        return True

    #disconnect the socket
    def disconnect(self):
        self.log(u'info', u'Disconnecting')
        if self.socket:
            self.socket.shutdown(socket.SHUT_RDWR)
            self.socket.close()
        else:
            self.log(u'warning', u'Tried disconnecting while socket wasn\'t open')

    #main loop
    #
    def run(self):
        #load all plugins
        try:
            self.plugins.loadAll(self)
        except Exception as ex:
            self.log(u'fatal', u'Exception occurred while loading plugins: %s' % repr(ex))
            return False

        while not self.quitting:
            #try connecting indefinitely
            while not self.connect():
                time.sleep(30)

            recv = u''
            while not self.quitting:
                try:
                    recv += self.socket.recv(4098).decode('utf-8')
                except Exception as ex:
                    self.log(u'error', u'Exception occurred receiving data: %s' % repr(ex))
                    break #break inner loop, try to reconnect

                while u'\r\n' in recv:
                    line, recv = recv.split(u'\r\n', 1)
                    self.fireEvent('rawReceive', self, line)
                    cmd = self.parseServerCmd(line)
                    if cmd:
                        self.handleCmd(cmd)
            self.disconnect()

        #unload all plugins before quitting
        self.plugins.unloadAll(self)

        return True

#ugly commandline parsing
#TODO: replace this with a config file or something
optParser = optparse.OptionParser()
optParser.add_option('-s', '--server', dest='host', action="store", default='localhost')
optParser.add_option('-P', '--port', dest='port', action="store", type="int", default=6667)
optParser.add_option('-S', '--ssl', dest='ssl', action="store_true", default=False)
optParser.add_option('-u', '--user', dest='user', action="store", default='')
optParser.add_option('-n', '--nick', dest='nick', action="store", default='')
optParser.add_option('-p', '--password', dest='password', action="store", default='')
optParser.add_option('-o', '--owner', dest='owner', action="store", default='')
optParser.add_option('--plugin-dir', dest='plugins', action="store", default='plugins')
options, remainder = optParser.parse_args()

bot = IrcBot()
bot.server = options.host
bot.port = options.port
bot.ssl = options.ssl
bot.nick = options.nick
bot.user = options.user
bot.password = options.password
bot.owner = options.owner
bot.plugins.rootDir = options.plugins

rootDir = os.path.dirname(__file__)
rootDir = os.path.join(rootDir, options.plugins)

bot.run()
