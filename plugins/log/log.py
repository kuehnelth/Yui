import os
import datetime

logDir = ''
logFile = None

logDir = os.path.dirname(__file__)
logDir = os.path.join(logDir, 'logs')
if not os.path.exists(logDir):
    os.makedirs(logDir)

@yui.event('log')
def log(level,msg):
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
