import re

import markovify

# takes irc logs (as ZNC writes them, and in utf-8) and generates
# markov models for each nick in them
# put your concatenated logs in one file and set the markovLogFile
# variable in the config json

# for concatenations you can do something like
#   find ~/.znc -iname "*#*.log" -exec cat {} \; > mark.txt

nick_models = {}  # mapping nick -> markov model


# prepare the markov chains for users
def prepare():
    msg_regex = re.compile(r'^\[..:..:..\] <(.*?)> (.*)$')

    text = ''
    try:
        dict_file_name = yui.config_val('markovLogFile')
        with open(dict_file_name, errors='replace') as f:
            text = f.read()
    except Exception as ex:
        return

    # go through all lines and extract nick + messages
    nick_lines = {}
    for line in text.splitlines():
        match = msg_regex.match(line)
        if not match:
            continue
        u = match.group(1).lower()
        m = match.group(2)
        # omit any sentences shorter than 3 words
        if len(m.split()) < 3:
            continue
        if u not in nick_lines:
            nick_lines[u] = list()
        nick_lines[u].append(m)

    # generate markov models for each nick
    for u, m in nick_lines.items():
        try:
            mark = markovify.NewlineText('\n'.join(m), state_size=3)
            nick_models[u] = mark
        except Exception as ex:
            pass


# generate a sentence for a given nick
def generate_sentence(nick):
    for i in range(1, 100):
        ret = nick_models[nick.lower()].make_sentence()
        if ret:
            return ret
    return None


@yui.threaded
@yui.command('markov', 'mark')
def markov(argv, user):
    """Generate a random sentence for a given nick. Usage: markov [nick]"""
    name = user.nick
    if len(argv) > 1:
        name = argv[1]
    if name not in nick_models.keys():
        return "I don't have enough data for %s" % name
    sent = generate_sentence(name)
    if not sent:
        return 'Nope'
    return '<%s> %s' % (name, sent)


prepare()
