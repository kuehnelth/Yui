import wikipedia

MAX_LEN = 350

@yui.command('wiki', 'wk', 'w')
def wiki(argv):
    """wiki [-lang] <article>"""
    lang = 'en'
    if len(argv) < 2:
        return

    # check if a language is given
    argv = argv[1:]
    if len(argv) > 1 and argv[0].startswith('-'):
        lang = argv[0][1:]
        argv = argv[1:]

    article = ' '.join(argv)
    try:
        wikipedia.set_lang(lang)
        sum = wikipedia.summary(article)
    except Exception as ex:
        return "Couldn't find an article for '%s'" % article
    if len(sum) > MAX_LEN:
        sum = sum[:MAX_LEN-3] + '...'
    return sum
