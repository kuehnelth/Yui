@yui.event('connect')
def autoJoin(level):
    for c in yui.config['channels']:
        yui.join(c)
