import time

buckets = {}
last_tick = time.time()
timeframe = float(yui.config_val('ratelimit', 'timeframe', default=60.0))
max_msg = float(yui.config_val('ratelimit', 'messages', default=6.0))
ignore_for = 60.0 * float(yui.config_val('ratelimit', 'ignoreMinutes', default=3.0))


@yui.event('postCmd')
def ratelimit(user, msg):
    if user not in buckets.keys():
        buckets[user] = 1.0
    else:
        buckets[user] += 1.0
    if buckets[user] > max_msg:
        yui.ignore(ignore_for, user.nick)


@yui.event('tick')
def tick():
    global last_tick
    now = time.time()
    diff = now - last_tick
    for user, n in buckets.items():
        n -= ((max_msg / timeframe) * diff)
        n = n if n > 0 else 0
        buckets[user] = n
    last_tick = now
