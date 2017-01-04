@yui.event('connect')
def autoJoin():
    for c in yui.config['channels']:
        yui.join(c)
