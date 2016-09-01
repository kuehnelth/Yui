#!/usr/bin/python

import imp
import os
import socket, ssl
import time
import optparse
from collections import namedtuple

IrcMsg = namedtuple('IrcMsg', ['channel', 'user', 'msg'])

IrcServerCmd = namedtuple('IrcServerCmd', ['prefix', 'cmd', 'args'])

onMsgEntry = namedtuple('onMsgEntry', ['match', 'func'])



class IrcBot(object):
    def __init__(self):
        self.server = ""
        self.port = 6667
        self.ssl = False
        self.nick = ""
        self.user = ""
        self.password = ""
        self.owner = ""
        self.onMsgHandlers = []
        self.socket = None
        self.quitting = False

    def __send(self,str):
        #TODO: limit length!
        print str
        self.socket.send(str+'\r\n')
        #TODO: error check

    def registerOnMsg(self, match, func):
        self.onMsgHandlers.append(onMsgEntry(match,func))

    def onMsg(self, msg):
        for handler in self.onMsgHandlers:
            if msg.msg.startswith(handler.match):
                handler.func(self,msg)

    def sendMsg(self, channel, msg):
        self.__send('PRIVMSG %s :%s' % (channel, msg))

    def setNick(self, nick):
        self.__send('NICK %s' % nick)
        self.nick = nick

    def join(self, channel):
        self.__send('JOIN %s' % channel)

    def part(self, channel):
        self.__send('PART %s' % channel)

    def quit(self, reason):
        self.__send('QUIT :%s' % reason)
        self.quitting = True

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
        if cmd.cmd == 'PING':
            self.__send('PONG :%s' % cmd.args[0])
        if cmd.cmd == 'PRIVMSG':
            msg = IrcMsg(channel = cmd.args[0], user = cmd.prefix.split('!')[0], msg = cmd.args[1])
            self.onMsg(msg)

    def connect(self):
        if not self.user:
            return False

        self.socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        if self.ssl:
            self.socket = ssl.wrap_socket(self.socket)

        self.socket.connect((self.server, self.port))
        #TODO: error check

        if self.password:
            self.__send('PASS %s' % self.password)

        if not self.nick:
            self.nick = self.user
        self.setNick(self.nick)
        self.__send('USER %s 8 * :teh bot' % self.user)

        return True

    def disconnect(self):
        if self.socket:
            self.socket.shutdown(socket.SHUT_RDWR)
            self.socket.close()
        else:
            print "asd"
            #TODO: log error

    def run(self):
        while not self.quitting:
            while not self.connect():
                time.sleep(30)

            recv = ''
            while not self.quitting:
                try:
                    recv += self.socket.recv(4098)
                except Exception:
                    print Exception.message
                    break

                while '\r\n' in recv:
                    line, recv = recv.split('\r\n', 1)
                    cmd = self.parseServerCmd(line)
                    if cmd:
                        self.handleCmd(cmd)



def loadPlugin(filepath):
    mod_name,file_ext = os.path.splitext(os.path.split(filepath)[-1])
    if file_ext.lower() == '.py':
        py_mod = imp.load_source(mod_name, filepath)
    return py_mod


optParser = optparse.OptionParser()
optParser.add_option('-s', '--server', dest='host', action="store", default='')
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

#load all *.py in plugins/
#and all .py files in subdirs of it, if they have the same name as the dir
#e.g. plugins/testplug/testplug.py
for f in os.listdir(rootDir):
    plugin = None
    fullPath = os.path.join(rootDir,f)
    if os.path.isdir(fullPath):
        module = os.path.join(fullPath,f) + ".py"
        if os.path.isfile(module):
            plugin = loadPlugin(module)
    elif fullPath.endswith('.py') and f != '__init__.py':
        plugin = loadPlugin(fullPath)
    if plugin:
        plugin.init(bot)


bot.run()
