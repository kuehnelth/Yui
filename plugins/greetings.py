import re
import random

phrases = [
    ['hi', 'hello'],
    ['yo', 'sup'],
    ['hallo', 'tag', 'moin'],
    ['こんにちは', 'こんちわ'],
    ['よ', 'やぁ', 'おっす']
]

def getRandomExcept(arr, ex):
    if not ex in arr:
        return random.choice(arr)
    idx = arr.index(ex)
    arrEx = arr[:idx] + arr[idx+1:]
    return random.choice(arrEx)

@yui.event('msgRecv')
def greetings(msg,user,channel):
    global phrases

    answer = None
    lower = msg.lower()
    lower = re.sub('[!?\. ]', '', lower)
    for s in phrases:
        if lower in s:
            return getRandomExcept(s, lower)

    #responds to any message starting with the bot's nick
    #and otherwise only contains spaces or the caracters <>!?.o
    #which allows for some things like \o/ or >.< or !?!?!
    #if that's the case, the bot answers the same back to whomever mentioned him
    botnick = yui.getNick()
    if msg.lower().startswith(botnick):
        suffix = msg[len(botnick):]
        if not suffix or re.match(r'^[o<>/\\!\?\. ]+$',suffix) is not None:
            yui.sendMessage(channel, user + suffix)
