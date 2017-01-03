@yui.command('plug')
@yui.perm('admin', 'moderator')
def plug(argv):
    if len(argv) < 2:
        return;

    # (re)load plugin
    try:
        if yui.load_plugin(argv[1]):
            return 'Loaded %s' % argv[1]
    except Exception as ex:
        pass

    # plugin couldn't be loaded
    return 'Couldn\'t load %s' % argv[1]


@yui.command('unplug')
@yui.perm('admin', 'moderator')
def unplug(argv):
    if len(argv) < 2:
        return;
    # unload plugin
    try:
        if yui.unload_plugin(argv[1]):
            return 'Unloaded %s' % argv[1]
    except Exception as ex:
        pass
    # plugin couldn't be properly unloaded
    return 'Couldn\'t unload %s' % argv[1]
