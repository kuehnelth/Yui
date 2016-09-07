#!/usr/bin/python

import imp
import os
import socket, ssl
import time
import optparse
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

    def fire(self, eventName, *args, **kwargs):
        if not eventName in self.events:
            return

        #currently processing an event, so push the new one into the queue
        if len(self.__eventBuffer) > 0:
            self.__eventBuffer.append((eventName, args, kwargs))
            return

        #push current event onto queue and process it, and all further added events
        self.__eventBuffer.append((eventName, args, kwargs))
        while len(self.__eventBuffer) > 0:
            en, a, kwa = self.__eventBuffer.popleft()
            for prio, func in self.events[eventName]:
                func(*a, **kwa)

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
        for n, p in self.plugins:
            self.close(n, *args, **kwargs)



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

        self.pluginLoader = PluginLoader('plugins')

        self.events = EventManager()
        self.events.register('channelMessage');
        self.events.register('log');
        self.events.register('rawSend');
        self.events.register('rawReceive');
        self.events.register('ircCmd');
        self.events.register('preConnect');

    #send raw data to the server
    def sendRaw(self,str):
        #TODO: limit length!
        try:
            self.socket.send(str+'\r\n')
        except Exception as ex:
            self.log('error', 'exception occurred sending data: %s' % repr(ex))
        self.events.fire('rawSend',bot,str)

    def log(self, level, msg):
        self.events.fire('log',self,level,msg)

    def sendChannelMessage(self, channel, msg):
        self.sendRaw('PRIVMSG %s :%s' % (channel, msg))
        #fire channelMessage event for outgoing messages
        evMsg = IrcMsg(channel = channel,
                        user = self.nick,
                        msg = msg,
                        replyTo = channel)
        self.events.fire('channelMessage',self,evMsg)

    def setNick(self, nick):
        if not nick:
            self.log('warning','tried setting nick to empty string')
            return
        self.sendRaw('NICK %s' % nick)
        self.nick = nick

    def join(self, channel):
        if not channel:
            self.log('warning','tried joining channel without name')
            return
        self.sendRaw('JOIN %s' % channel)

    def part(self, channel):
        if not channel:
            self.log('warning','tried parting from channel without name')
            return
        self.sendRaw('PART %s' % channel)

    def quit(self, reason):
        self.sendRaw('QUIT :%s' % reason)
        self.quitting = True
        self.log('info', 'quit (%s)' % reason)

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

    def handleCmd(self, cmd):
        self.events.fire('ircCmd', self, cmd)
        if cmd.cmd == 'PING':
            self.sendRaw('PONG :%s' % cmd.args[0])
        if cmd.cmd == 'PRIVMSG':
            channel = cmd.args[0]
            reply = channel
            user = cmd.prefix.split('!')[0]
            if not reply.startswith('#'):
                reply = user
            msg = IrcMsg(channel = channel,
                         user = user,
                         msg = cmd.args[1],
                         replyTo = reply)
            self.events.fire('channelMessage',self,msg)

    def connect(self):
        if not self.user:
            return False

        self.socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        if self.ssl:
            self.socket = ssl.wrap_socket(self.socket)

        self.log('info', 'connecting to %s:%d' % (self.server, self.port))
        try:
            self.socket.connect((self.server, self.port))
        except Exception as ex:
            self.log('error','exception occured while trying to connect: %s' % repr(ex))
            return False

        self.log('info','connected!')

        if self.password:
            self.sendRaw('PASS %s' % self.password)

        if not self.nick:
            self.nick = self.user
        self.setNick(self.nick)
        self.sendRaw('USER %s 8 * :teh bot' % self.user)

        return True

    def disconnect(self):
        self.log('info', 'disconnecting')
        if self.socket:
            self.socket.shutdown(socket.SHUT_RDWR)
            self.socket.close()
        else:
            self.log('warning', 'tried disconnecting while socket wasn\'t open')

    def run(self):
        #load all plugins
        self.pluginLoader.loadAll(self)

        while not self.quitting:
            while not self.connect():
                time.sleep(30)

            recv = ''
            while not self.quitting:
                try:
                    recv += self.socket.recv(4098)
                except Exception as ex:
                    self.log('error', 'exception occurred receiving data: %s' % repr(ex))
                    break

                while '\r\n' in recv:
                    line, recv = recv.split('\r\n', 1)
                    self.events.fire('rawReceive', self, line)
                    cmd = self.parseServerCmd(line)
                    if cmd:
                        self.handleCmd(cmd)

        #unload all plugins before quitting
        self.pluginLoader.unloadAll(self)

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
bot.pluginLoader.rootDir = options.plugins

rootDir = os.path.dirname(__file__)
rootDir = os.path.join(rootDir, options.plugins)


bot.run()

