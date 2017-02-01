import re

import markovify

yui.db.execute("""\
CREATE TABLE IF NOT EXISTS markov(
    nick TEXT PRIMARY KEY,
    model TEXT);""")
yui.db.commit()

BUFFER_SIZE = 100  # messages to buffer before merging them into the models

nick_models = {}  # mapping nick -> markov model
msg_buffer = {}  # buffer for messages before they get merged
msg_count = 0


@yui.admin
@yui.command('markov_loadfile')
def load_file(argv):
    """Add a an IRC log file to the existing markov models. Messages in the file must be the same format as ZNC
    writes them, [NN:NN:NN] <NICK> MSG. Usage: markov_loadgile <path>"""

    if len(argv) < 2:
        return

    try:
        dict_file_name = argv[1]
        with open(dict_file_name, errors='replace') as f:
            text = f.read()
    except:
        return "Couldn't read file"

    msg_regex = re.compile(r'^\[..:..:..\] <(.*?)> (.*)$')

    # go through all lines and extract nick + messages
    num_lines = 0
    for line in text.splitlines():
        match = msg_regex.match(line)
        if not match:
            continue
        n = match.group(1)
        m = match.group(2)
        buffer_msg(n, m)
        num_lines += 1

    merge_buffers()
    save_models()
    return 'Loaded %d lines' % num_lines


# add a message to the buffer
def buffer_msg(nick, msg):
    global msg_buffer
    if nick not in msg_buffer:
        msg_buffer[nick] = []
    msg_buffer[nick].append(msg)


# merge buffered messages into the existing models
def merge_buffers():
    global msg_buffer
    for n, msgs in msg_buffer.items():
        n = n.lower()
        try:
            model = markovify.NewlineText('\n'.join(msgs), state_size=3)
        except:
            continue
        if n not in nick_models:
            nick_models[n] = model
        else:
            nick_models[n] = markovify.combine([nick_models[n], model])
    msg_buffer = {}


# save models to db
def save_models():
    for n, m in nick_models.items():
        json = m.to_json()
        yui.db.execute('REPLACE INTO markov(nick, model) VALUES(?, ?)', (n, json))
    yui.db.commit()


# load saved models from db
def load_models():
    c = yui.db.execute('SELECT nick, model FROM markov;')
    for row in c:
        nick_models[row[0]] = markovify.NewlineText.from_json(row[1])


# generate a sentence for a given nick
def generate_sentence(nick):
    ret = nick_models[nick.lower()].make_sentence(tries=500)
    if ret:
        return ret
    return None


# add new sentences as they come in
@yui.event('msgRecv')
def recv(channel, user, msg):
    global msg_count

    if channel == user.nick:  # ignore query
        return

    buffer_msg(user.nick, msg)
    msg_count += 1

    if msg_count > BUFFER_SIZE:
        merge_buffers()
        save_models()
        msg_count = 0


@yui.threaded
@yui.command('markov', 'mark')
def markov(argv, user):
    """Generate a random sentence for a given nick. Usage: markov [nick]"""
    name = user.nick
    if len(argv) > 1:
        name = argv[1]
    if name.lower() not in nick_models.keys():
        return "I don't have enough data for %s" % name
    sent = generate_sentence(name)
    if not sent:
        return "Couldn't generate a sentence :("
    return '<%s> %s' % (name, sent)


load_models()
