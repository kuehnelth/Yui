#!/usr/bin/python

import os
import datetime

logDir = 'logs'
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
    bot.events['log'].append(log)

def close(bot):
    if logFile:
        logFile.close()

