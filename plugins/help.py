import inspect


@yui.command('help', 'h')
def help(argv):
    """Returns doc for commands. Usage: help <command>"""
    if len(argv) < 2:
        return 'Usage: help <command>'
    hook = yui.hook_by_cmd(argv[1])
    if hook:
        doc = inspect.getdoc(hook.func)
        if doc:
            return doc

@yui.command('alias', 'al')
def alias(argv):
    """Returns all aliases for a command. Usage: alias <command>"""
    if len(argv) < 2:
        return
    hook = yui.hook_by_cmd(argv[1])
    if hook:
        return 'Aliases for %s: %s' % (hook, ', '.join(hook.cmd))
