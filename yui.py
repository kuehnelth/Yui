#!/usr/bin/env python3

from ircclient import IRCClient

import imp
import os
import re
import json  # reading/writing config
import csv  # parsing commands

import inspect  # inspecting hook arguments
import builtins  # setting yui as a builtin

from collections import OrderedDict  # for more consistent settings saving


class Hook:
    def __init__(self, func):
        self.plugin = None  # plugin name, for unregistering hooks when needed
        self.func = func  # hook callable
        self.regex = []  # list of compiled regexes
        self.cmd = []  # list of commands to call this hook for
        self.perm = []  # list of people permitted to use the command
        self.event = []  # list of events to call this hook for
        self.threaded = False  # whether or not the hook should be called in a separate thread

    # unpack kwargs, match their keys to the hook's normal args' names
    # and pass them accordingly
    # args not in the hook's signature are ignored, and args that are in the
    # signature, but not in kwargs, are passed as None
    def __call__(self, **kwargs):
        argNames = inspect.getargspec(self.func).args  # list of argument names
        args = []  # argument list to pass
        for name in argNames:
            if name in kwargs.keys():
                args.append(kwargs[name])
            else:
                args.append(None)
        return self.func(*args)


class Yui(IRCClient):
    def __init__(self, configPath):
        builtins.yui = self

        # load config
        self.configPath = configPath
        self.config = None
        if not self.load_config():
            quit()

        # load plugins
        self.plugins = []
        self.loadingPlugin = None
        self.hooks = {}  # dict containing hook callable -> Hook object
        if not self.autoload_plugins():
            quit()

        # init SingleServerIRCBot
        IRCClient.__init__(self,
                           server=self.config['server'],
                           port=self.config['port'],
                           ssl=self.config['ssl'],
                           encoding=self.config['encoding'],
                           nick=self.config['nick'],
                           user=self.config['user'],
                           password=self.config['password'],
                           realname=self.config['realname'])

    ################################################################################
    # decorators for hooks in plugins
    ################################################################################

    # return a hook by function
    # or create a new one and return that
    def get_hook(self, func):
        if func in self.hooks:
            return self.hooks[func]
        h = Hook(func)
        self.hooks[func] = h
        return h

    # decorator for simple commands
    def command(self, *names):
        def command_dec(f):
            h = self.get_hook(f)
            h.plugin = self.loadingPlugin
            h.cmd.extend(names)
            return f

        return command_dec

    # decorator for matching regex against messages
    def regex(self, *reg):
        def regex_dec(f):
            h = self.get_hook(f)
            h.plugin = self.loadingPlugin
            # compile all regexs
            for r in reg:
                h.regex.append(re.compile(r))
            return f

        return regex_dec

    # decorator for setting needed permissions on a command
    def perm(self, *perm):
        def perm_dec(f):
            h = self.get_hook(f)
            h.plugin = self.loadingPlugin
            h.perm.extend(perm)
            return f

        return perm_dec

    # decorator for other events
    def event(self, *ev):
        def event_dec(f):
            h = self.get_hook(f)
            h.plugin = self.loadingPlugin
            h.event.extend(ev)
            return f

        return event_dec

    def threaded(self, f):
        h = self.get_hook(f)
        h.threaded = True
        return f

    ################################################################################
    # irc functions
    ################################################################################

    # send a message to a channel/user
    def send_msg(self, channel, msg):
        self.send_privmsg(channel, msg)
        self.fire_event('msgSend', channel=channel, msg=msg)

    ################################################################################
    # other bot functions
    ################################################################################

    def fire_event(self, eventName, **kwargs):
        try:
            for f, h in self.hooks.items():
                if eventName in h.event:
                    h(**kwargs)
        except Exception as ex:
            if eventName != 'log':
                self.log('error', 'Exception occurred processing event "%s": %s' % (eventName, repr(ex)))

    # check if a user has a certain permission
    def check_perm(self, user, perm):
        if perm not in self.config:
            return False
        if user not in self.config[perm]:
            return False
        return True

    # check if a user has any of the given permissions
    # returns false for an empty list
    def check_perm_any(self, user, perm):
        if not perm:
            return True
        for p in perm:
            if self.check_perm(user, p):
                return True
        return False

    # prints to stdout and fires the 'log' event
    def log(self, level, msg):
        print('[%s] %s' % (level, msg))
        self.fire_event('log', level=level, msg=msg)

    def load_config(self):
        try:
            with open(self.configPath) as f:
                self.config = json.load(f, object_pairs_hook=OrderedDict)
        except Exception as ex:
            self.log('error', 'Exception occurred while loading config: %s' % repr(ex))
            return False
        return True

    def save_config(self):
        self.log('info', 'Saving config')
        try:
            with open(self.configPath, 'w') as f:
                jsonStr = json.dumps(self.config, ensure_ascii=False, indent=4, separators=(',', ': '))
                f.write(jsonStr.encode('utf-8'))
        except Exception as ex:
            self.log('error', 'Exception occurred while saving config: %s' % repr(ex))
            return False
        return True

    # loads a given .py file as a plugin
    # calls its init() function, if it has one
    # if a path to a directory is given, it tries to load a .py file in that,
    # if it has the same name as the dir
    def load_plugin(self, name):
        try:
            name = os.path.basename(name)
            filepath = os.path.join(self.config['pluginDir'], name)

            # try to load plugin in subdir
            if os.path.isdir(filepath):
                filepath = os.path.join(filepath, name)

            filepath += '.py'
            if not os.path.exists(filepath):
                self.log('error', "Plugin '%s' not found" % name)
                return False

            # unload and then re-load, if the plugin is already loaded
            if name in self.plugins:
                self.unload_plugin(name)

            # set the currently loading plugin name
            # TODO
            self.loadingPlugin = name

            plugin = imp.load_source(name, filepath)

        except Exception as ex:
            self.log('fatal', "Exception occurred while loading plugin '%s': %s" % (name, repr(ex)))
            return False

        self.log('info', 'Loaded plugin %s' % name)
        return True

    def unload_plugin(self, name):
        # TODO
        toDel = [f for f, h in self.hooks.items() if h.plugin == name]
        if len(toDel) < 1:
            return False
        print(toDel)
        for d in toDel:
            del self.hooks[d]
        return True

    # load all plugins specified in the pluginAutoLoad config
    def autoload_plugins(self):
        for p in self.config['pluginAutoLoad']:
            if not self.load_plugin(p):
                return False
        return True

    ################################################################################
    # SingleServerIRCBot callbacks
    ################################################################################

    # combines on_privmsg and on_pubmsg
    # TODO: threading
    def on_privmsg(self, nick, target, msg):
        # fire generic event
        self.fire_event('msgRecv', nick=nick,
                        msg=msg,
                        target=target)

        hooks = self.hooks.copy()
        # parse command
        if msg.startswith(tuple(self.config['commandPrefixes'])):
            argv = list(csv.reader([msg[1:]], delimiter=' ', quotechar='"', skipinitialspace=True))[0]
            # look for a hook registered to this command
            for f, h in hooks.items():
                if argv[0] in h.cmd and self.check_perm_any(nick, h.perm):
                    ret = h(nick=nick, target=target, msg=msg, argv=argv)
                    if ret:
                        self.send_msg(target, ret)
        # match regex
        for f, h in hooks.items():
            for reg in h.regex:
                match = reg.match(msg)
                if match:
                    ret = h(nick=nick, target=target, msg=msg, groups=match.groupdict())
                    if ret:
                        self.send_msg(target, ret)

    def on_connect(self):
        pass

    def on_quit(self):
        pass

    def on_log(self, error):
        self.log('error', error)

    def on_disconnect(self):
        self.log('info', 'disconnected')
        self.fire_event('disconnect')

    # servers tend to not take joins etc. before they sent a welcome msg
    def on_serverready(self):
        self.log('info', 'connected!')
        self.fire_event('connect')


def main():
    # ugly commandline parsing
    import sys
    conf = "config.json"
    if len(sys.argv) > 1:
        conf = sys.argv[1]
    y = Yui(conf)
    y.run()


if __name__ == "__main__":
    main()
