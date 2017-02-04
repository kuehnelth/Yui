# coding=utf-8

import re
import threading

import markovify

yui.db.execute("""\
CREATE TABLE IF NOT EXISTS markov(
    nick TEXT,
    sentence TEXT);""")
yui.db.commit()

BUFFER_SIZE = 100  # messages to buffer before merging them into the models
STATE_SIZE = 3

nick_models = {}  # mapping nick -> markov model
msg_buffer = {}  # buffer for messages before they get merged
msg_count = 0
lock = threading.Lock()


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

    def merge_thread(buffer):
        global msg_buffer
        for n, msgs in buffer.items():
            n = n.lower()
            try:
                model = markovify.NewlineText('\n'.join(msgs), state_size=STATE_SIZE)
            except:
                continue
            with lock:
                if n not in nick_models:
                    nick_models[n] = model
                else:
                    nick_models[n] = markovify.combine([nick_models[n], model])
    threading.Thread(target=merge_thread, args=(dict(msg_buffer),)).start()

    # save sentences to db
    for n, msgs in msg_buffer.items():
        yui.db.executemany('INSERT INTO markov(nick, sentence) VALUES(?, ?);', [(n, m) for m in msgs])
        yui.db.commit()

    msg_buffer = {}


# load saved sentences from db
def load_models():
    global nick_models
    c = yui.db.execute("SELECT lower(nick), group_concat(sentence, '\n') FROM markov GROUP BY nick;")
    for row in c:
        try:
            if row[0] and row[1]:
                nick_models[row[0]] = markovify.NewlineText(row[1], state_size=STATE_SIZE)
        except:
            continue


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
