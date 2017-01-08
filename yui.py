#!/usr/bin/env python3

import builtins  # setting yui as a builtin
import csv  # parsing commands
import imp
import inspect  # inspecting hook arguments
import json  # reading/writing config
import os
import re
import sqlite3
import threading
from collections import OrderedDict  # for more consistent settings saving

from ircclient import IRCClient


class Hook:
    def __init__(self, func):
        self.plugin = None  # plugin name, for unregistering hooks when needed
        self.func = func  # hook callable
        self.regex = []  # list of compiled regexes
        self.cmd = []  # list of commands to call this hook for
        self.perm = []  # list of people permitted to use the command
        self.event = []  # list of events to call this hook for
        self.threaded = False  # whether or not the hook should be called in a separate thread

    def __call__(self, **kwargs):
        """unpack kwargs, match their keys to the hook's normal args' names
        and pass them accordingly
        args not in the hook's signature are ignored, and args that are in the
        signature, but not in kwargs, are passed as None"""
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

        self.db = sqlite3.connect(self.config['sqlitePath'])

        self.loadingPlugin = None  # name of the currently loading plugin
        self.hooks = {}  # dict containing hook callable -> Hook object
        if not self.autoload_plugins():
            quit()

        self.server_ready = False

        # init SingleServerIRCBot
        IRCClient.__init__(self,
                           server=self.config['server'],
                           port=self.config['port'],
                           ssl=self.config['ssl'],
                           encoding=self.config['encoding'],
                           nick=self.config['nick'],
                           user=self.config['user'],
                           password=self.config['password'],
                           realname=self.config['realname'],
                           timeout=self.config['timeout'])

    ################################################################################
    # decorators for hooks in plugins
    ################################################################################

    def get_hook(self, func):
        """Return a Hook by its associated callable, or a new Hook,
        if no matching one exists"""
        if func in self.hooks:
            return self.hooks[func]
        h = Hook(func)
        self.hooks[func] = h
        return h

    def command(self, *names):
        """Register the decorated callable as a command"""
        def command_dec(f):
            h = self.get_hook(f)
            h.plugin = self.loadingPlugin
            h.cmd.extend(names)
            return f

        return command_dec

    def regex(self, *reg):
        """Register the decorated callable as a command triggered
        by any string matching a regex"""
        def regex_dec(f):
            h = self.get_hook(f)
            h.plugin = self.loadingPlugin
            # compile all regexs
            for r in reg:
                h.regex.append(re.compile(r))
            return f

        return regex_dec

    def perm(self, *perm):
        """Set the needed permission to use the hook associated with
        the decorated callable"""
        def perm_dec(f):
            h = self.get_hook(f)
            h.plugin = self.loadingPlugin
            h.perm.extend(perm)
            return f

        return perm_dec

    def event(self, *ev):
        """Register the decorated callable to any irc- or bot-internal event"""
        def event_dec(f):
            h = self.get_hook(f)
            h.plugin = self.loadingPlugin
            h.event.extend(ev)
            return f

        return event_dec

    def threaded(self, f):
        """Set the Hook associated with the decorated callable to
        be executed in a separate thread"""
        h = self.get_hook(f)
        h.threaded = True
        return f

    ################################################################################
    # irc functions
    ################################################################################

    def send_msg(self, channel, msg):
        """Send a PRIVMSG to a user or channel"""
        self.send_privmsg(channel, self.trim_to_max_len(msg, '...'))
        self.fire_event('msgSend', channel=channel, msg=msg)

    def get_nick(self):
        """Return the bot's current nickname"""
        return self.nick

    ################################################################################
    # other bot functions
    ################################################################################

    def fire_event(self, eventName, **kwargs):
        """Run Hooks registered to an event"""
        try:
            for f, h in self.hooks.items():
                if eventName in h.event:
                    h(**kwargs)
        except Exception as ex:
            if eventName != 'log':
                self.log('error', 'Exception occurred processing event "%s": %s' % (eventName, repr(ex)))

    def check_perm(self, user, perm):
        """Return True if the user has the specified permission"""
        if perm not in self.config:
            return False
        if user not in self.config[perm]:
            return False
        return True

    def check_perm_any(self, user, perm):
        """Return True if the user has any of the given permissions.
        Return False for an empty list"""
        if not perm:
            return True
        for p in perm:
            if self.check_perm(user, p):
                return True
        return False

    def log(self, level, msg):
        """Print to stdout and fire the 'log' event"""
        print('[%s] %s' % (level, msg))
        self.fire_event('log', level=level, msg=msg)

    def load_config(self):
        """(Re-)load the config JSON"""
        try:
            with open(self.configPath) as f:
                self.config = json.load(f, object_pairs_hook=OrderedDict)
        except Exception as ex:
            self.log('error', 'Exception occurred while loading config: %s' % repr(ex))
            return False
        return True

    def save_config(self):
        """Save the config to disk"""
        self.log('info', 'Saving config')
        try:
            with open(self.configPath, 'w') as f:
                jsonStr = json.dumps(self.config, ensure_ascii=False, indent=4, separators=(',', ': '))
                f.write(jsonStr.encode('utf-8'))
        except Exception as ex:
            self.log('error', 'Exception occurred while saving config: %s' % repr(ex))
            return False
        return True

    def load_plugin(self, name):
        """Load a plugin by its name."""
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
            self.unload_plugin(name)

            # set the currently loading plugin name
            self.loadingPlugin = name

            plugin = imp.load_source(name, filepath)

        except Exception as ex:
            self.log('fatal', "Exception occurred while loading plugin '%s': %s" % (name, repr(ex)))
            return False

        self.log('info', 'Loaded plugin %s' % name)
        return True

    def unload_plugin(self, name):
        """Unload a plugin by its name"""
        toDel = [f for f, h in self.hooks.items() if h.plugin == name]
        if len(toDel) < 1:
            return False
        for d in toDel:
            del self.hooks[d]
        return True

    def autoload_plugins(self):
        """Load all plugins specified in the pluginAutoLoad config"""
        for p in self.config['pluginAutoLoad']:
            if not self.load_plugin(p):
                return False
        return True

    def get_all_hooks(self):
        """Return a list containing all registered hooks"""
        return self.hooks.values()

    def hook_by_cmd(self, cmd):
        """Return a hook by registered command"""
        for f, h in self.hooks.items():
            if cmd in h.cmd:
                return h
        return None

    ################################################################################
    # IRCClient callbacks
    ################################################################################

    def on_privmsg(self, nick, target, msg):
        if target == self.get_nick():  # if we're in query
            target = nick  # send stuff back to the person

        # fire generic event
        self.fire_event('msgRecv', user=nick,
                        msg=msg,
                        channel=target)

        def call_hook(hook, target, **kwargs):
            """Call a hook either directly or in a thread"""
            def thread(hook, target, **kwargs):
                ret = hook(**kwargs)
                if ret:
                    self.send_msg(target, ret)
            if hook.threaded:
                t = threading.Thread(target=thread, args=(hook, target), kwargs=kwargs)
                t.start()
            else:
                thread(hook,target,**kwargs)

        hooks = self.hooks.copy()
        # parse command
        if msg.startswith(tuple(self.config['commandPrefixes'])):
            if len(msg) > 1:
                argv = list(csv.reader([msg[1:]], delimiter=' ', quotechar='"', skipinitialspace=True))[0]
                # look for a hook registered to this command
                for f, h in hooks.items():
                    if argv[0] in h.cmd and self.check_perm_any(nick, h.perm):
                        call_hook(h, target, user=nick, channel=target, msg=msg, argv=argv)
        # match regex
        for f, h in hooks.items():
            for reg in h.regex:
                match = reg.match(msg)
                if match:
                    call_hook(h, target, user=nick, channel=target, msg=msg, groups=match.groupdict())

    def on_join(self, nick, channel):
        self.fire_event('join', user=nick, channel=channel)

    def on_log(self, error):
        self.log('error', error)

    def on_disconnect(self):
        self.log('info', 'disconnected')
        self.fire_event('disconnect')

    # servers tend to not take joins etc. before they sent a welcome msg
    def on_serverready(self):
        self.log('info', 'connected!')
        self.fire_event('connect')
        self.server_ready = True

    def on_tick(self):
        if self.server_ready:
            self.fire_event('tick')

def main():
    import sys
    conf = "config.json"
    if len(sys.argv) > 1:
        conf = sys.argv[1]
    y = Yui(conf)
    y.run()


if __name__ == "__main__":
    main()
