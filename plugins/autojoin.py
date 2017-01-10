@yui.event('connect')
def autoJoin():
    # set user modes if any are configured
    yui.set_mode(yui.get_nick(), yui.config_val('userModes', default='+B'))

    # join all configured channels
    for c in yui.config_val('autojoin', default=[]):
        yui.join(c)
