#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import datetime

logDir = ''
logFile = None

def log(bot,level,msg):
    global logDir
    global logFile

    now = datetime.datetime.now()
    day = now.strftime('%Y-%m-%d')
    time = now.strftime('%Y-%m-%d %H:%M:%S')

    try:
        if logFile and not os.path.basename(logFile.name).startswith(day):
            logFile.close()
            logFile = None
        if not logFile:
            logFile = open(os.path.join(logDir,day + '.txt'), "a")
        logFile.writelines('%s [%s] %s\n' % (time,level,msg))
    except Exception as ex:
        pass


def init(bot):
    global logDir
    logDir = os.path.dirname(__file__)
    logDir = os.path.join(logDir, 'logs')
    if not os.path.exists(logDir):
        os.makedirs(logDir)
    bot.events.register('log',log,0) #highest priority

def close(bot):
    bot.events.unregister('log',log)
    if logFile:
        logFile.close()

