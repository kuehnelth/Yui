#!/usr/bin/python

import imp
import os
import socket, ssl
import time
import optparse
from collections import namedtuple

IrcMsg = namedtuple('IrcMsg', ['channel', 'user', 'msg', 'replyTo'])

IrcServerCmd = namedtuple('IrcServerCmd', ['prefix', 'cmd', 'args'])

class Event(list):
    def __call__(self, *args, **kwargs):
        for handler in self:
            handler(*args, **kwargs)

#loads all *.py in a given directory and calls their init() function
#also looks in subdirs for .py files with the same name as the subdir and loads those
#e.g. plugins/testplug/testplug.py if your plugin dir is "plugins"
class PluginLoader(object):
    def __init__(self, rootDir):
        self.rootDir = rootDir
        self.plugins = []

    def __loadModule(self,filepath):
        mod_name,file_ext = os.path.splitext(os.path.split(filepath)[-1])
        if file_ext.lower() == '.py':
            py_mod = imp.load_source(mod_name, filepath)
        return py_mod


    def load(self, *args, **kwargs):
        for f in os.listdir(rootDir):
            plugin = None
            fullPath = os.path.join(rootDir,f)

            #try to load plugins in subdirs
            if os.path.isdir(fullPath):
                module = os.path.join(fullPath,f) + ".py"
                if os.path.isfile(module):
                    plugin = self.__loadModule(module)
            #load single-file plugins
            elif fullPath.endswith('.py') and f != '__init__.py':
                plugin = self.__loadModule(fullPath)

            #check if the plugin contains an init() function
            if plugin and callable(getattr(plugin, "init", None)):
                plugin.init(*args,**kwargs)
                self.plugins.append(plugin)

    def close(self, *args, **kwargs):
        for p in self.plugins:
            if callable(getattr(p, "close", None)):
                p.close(args, **kwargs)


class IrcBot(object):
    def __init__(self):
        self.server = 'localhost'
        self.port = 6667
        self.ssl = False
        self.nick = ''
        self.user = ''
        self.password = ''
        self.owner = ''
        self.socket = None
        self.quitting = False

        self.events = {
                'channelMessage' : Event(),
                'log' : Event(),
                'rawSend' : Event(),
                'rawReceive' : Event(),
                'ircCmd' : Event()
                }

        #buffer outgoing channel message events
        self.sendMsgBuff = []

    def __send(self,str):
        #TODO: limit length!
        try:
            self.socket.send(str+'\r\n')
        except Exception as ex:
            self.__log('error', 'exception occurred sending data: %s' % repr(ex))
        self.events['rawSend'](str)

    def __log(self, level, msg):
        self.events['log'](bot,level,msg)

    def __outgoingChannelMessages(self):
        for m in self.sendMsgBuff:
            self.events['channelMessage'](self,m)
        self.sendMsgBuff[:] = [] #empty buffer

    def sendMsg(self, channel, msg):
        self.__send('PRIVMSG %s :%s' % (channel, msg))
        #fire channelMessage event for outgoing messages
        evMsg = IrcMsg(channel = channel,
                        user = self.nick,
                        msg = msg,
                        replyTo = channel)
        self.sendMsgBuff.append(evMsg)

    def setNick(self, nick):
        if not nick:
            self.__log('warning','tried setting nick to empty string')
            return
        self.__send('NICK %s' % nick)
        self.nick = nick

    def join(self, channel):
        if not channel:
            self.__log('warning','tried joining channel without name')
            return
        self.__send('JOIN %s' % channel)

    def part(self, channel):
        if not channel:
            self.__log('warning','tried parting from channel without name')
            return
        self.__send('PART %s' % channel)

    def quit(self, reason):
        self.__send('QUIT :%s' % reason)
        self.quitting = True
        self.__log('info', 'quit (%s)' % reason)

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
        self.events['ircCmd'](cmd)
        if cmd.cmd == 'PING':
            self.__send('PONG :%s' % cmd.args[0])
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
            self.events['channelMessage'](self,msg)
            self.__outgoingChannelMessages()

    def connect(self):
        if not self.user:
            return False

        self.socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        if self.ssl:
            self.socket = ssl.wrap_socket(self.socket)

        self.__log('info', 'connecting to %s:%d' % (self.server, self.port))
        try:
            self.socket.connect((self.server, self.port))
        except Exception as ex:
            self.__log('error','exception occured while trying to connect: %s' % repr(ex))
            return False

        self.__log('info','connected!')

        if self.password:
            self.__send('PASS %s' % self.password)

        if not self.nick:
            self.nick = self.user
        self.setNick(self.nick)
        self.__send('USER %s 8 * :teh bot' % self.user)

        return True

    def disconnect(self):
        self.__log('info', 'disconnecting')
        if self.socket:
            self.socket.shutdown(socket.SHUT_RDWR)
            self.socket.close()
        else:
            self.__log('warning', 'tried disconnecting while socket wasn\'t open')

    def run(self):
        while not self.quitting:
            while not self.connect():
                time.sleep(30)

            recv = ''
            while not self.quitting:
                try:
                    recv += self.socket.recv(4098)
                except Exception as ex:
                    self.__log('error', 'exception occurred receiving data: %s' % repr(ex))
                    break

                while '\r\n' in recv:
                    line, recv = recv.split('\r\n', 1)
                    self.events['rawReceive'](line)
                    cmd = self.parseServerCmd(line)
                    if cmd:
                        self.handleCmd(cmd)

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

rootDir = os.path.dirname(__file__)
rootDir = os.path.join(rootDir, options.plugins)

plug = PluginLoader(rootDir)
plug.load(bot)

bot.run()

plug.close(bot)
