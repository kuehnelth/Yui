import os
import random
import csv

quoteDir = ''
quoteList = {}

#list tags and quotes in them
@yui.command('qtags', 'qt')
def qtags():
    l = []
    for t, i in quoteList.items():
        l.append('%s(%d)' % (t, len(i)))
    return 'Tags: ' + ', '.join(l)

@yui.command('qadd','qa')
@yui.perm('admin','moderator')
def quote(argv,channel):
    global quoteList
    global quoteDir

    #store a quote
    #figure out parameters
    tag = channel #default tag to channel name
    content = argv[1]

    if len(argv) > 2:
        tag = argv[1]
        content = argv[2]
        #don't let people store quotes in some channel's specific tag
        if tag.startswith('#'):
            return 'No.'

    storeQuote(tag, content)
    return 'Stored quote in [%s]' % tag

#recall quote
@yui.command('quote','q')
def quote(argv,channel):
    tag = channel #default tag to channel name

    if len(argv) > 1:
        tag = argv[1]
    if tag not in quoteList or len(quoteList[tag]) < 1:
        return 'No tag named "%s" :(' % tag
    else:
        l = len(quoteList[tag])
        rnd = random.randint(0,l-1)
        rcl = quoteList[tag][rnd]
        return 'Quote for [%s] (%d/%d): %s' % (tag,rnd+1,l,rcl)

#load existing quotes
def loadQuotes():
    global quoteDir
    global quoteList

    for f in os.listdir(quoteDir):
        path = os.path.join(quoteDir, f)
        tag, ext = os.path.splitext(f)
        if ext == '.txt':
            quoteList[tag] = []
            try:
                file = open(path,'r')
                for line in file:
                    line = line.rstrip('\r\n')
                    quoteList[tag].append(line)
                file.close()
            except Exception as ex:
                pass

#store a message to a specified tag
def storeQuote(tag, msg):
    global quoteList
    global quoteDir

    try:
        file = open(os.path.join(quoteDir, tag) + '.txt', 'a')
        file.writelines(msg+'\n')
        file.close()
    except Exception as ex:
        pass
    else:
        if tag not in quoteList:
            quoteList[tag] = []
        quoteList[tag].append(msg)

quoteDir = os.path.dirname(__file__)
quoteDir = os.path.join(quoteDir, 'quotes')
if not os.path.exists(quoteDir):
    os.makedirs(quoteDir)
loadQuotes()
