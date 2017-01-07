@yui.command('admin')
def admin():
    return 'Admins: [%s], Mods: [%s]' % (','.join(yui.config['admin']), ','.join(yui.config['moderator']))

@yui.command('source')
def source():
    return 'https://github.com/Rj48/Yui'

@yui.command('join')
@yui.perm('admin','moderator')
def join(argv):
    for ch in argv[1:]:
        yui.join(ch)

@yui.command('part')
@yui.perm('admin','moderator')
def join(argv, channel):
    if len(argv) < 2:
        yui.part(channel)
    else:
        for ch in argv[1:]:
            yui.part(ch)

@yui.command('quit')
@yui.perm('admin')
def quit(argv):
    if len(argv) < 2:
        yui.quit("")
    else:
        yui.quit(argv[1])

@yui.command('nick')
@yui.perm('admin','moderator')
def nick(argv):
    if len(argv) > 1:
        yui.set_nick(argv[1])

@yui.command('mode')
@yui.perm('admin','moderator')
def mode(argv):
    if len(argv) < 2:
        return
    if len(argv) < 3:
        yui.set_mode(yui.get_nick(), argv[1])
    else:
        yui.set_mode(argv[1], argv[2])
