import time
from collections import deque

last_tick = time.time()
timeframe = yui.config_val('ratelimit', 'timeframe', default=60.0)
max_msg = yui.config_val('ratelimit', 'messages', default=6.0) + 1
ignore_for = 60.0 * yui.config_val('ratelimit', 'ignoreMinutes', default=3.0)


buffers = {}


@yui.event('preCmd')
def ratelimit(user, msg):
    now = time.time()
    if user not in buffers.keys():
        buffers[user] = deque([], maxlen=max_msg)
    if len(buffers[user]) < max_msg:
        buffers[user].append(now)
        return True
    if now - buffers[user][0] > timeframe:
        buffers[user].append(now)
        return True
    else:
        yui.ignore(ignore_for, user.nick)
        return False
