@yui.command('admin')
def admin():
    return 'Admins: [%s], Mods: [%s]' % (','.join(yui.config['admin']), ','.join(yui.config['moderator']))

@yui.command('source')
def source():
    return 'https://github.com/Rj48/ircbot'

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
            yui.join(ch)

@yui.command('quit')
@yui.perm('admin')
def quit(argv):
    if len(argv) < 2:
        yui.quit()
    else:
        yui.quit(argv[1])

@yui.command('nick')
@yui.perm('admin','moderator')
def nick(argv):
    if len(argv) > 1:
        yui.setNick(argv[1])
