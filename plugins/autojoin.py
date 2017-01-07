@yui.event('connect')
def autoJoin():
    #set user modes if any are configured
    if 'userModes' in yui.config:
        yui.set_mode(yui.get_nick(), yui.config['userModes'])

    #join all configured channels
    for c in yui.config['channels']:
        yui.join(c)
