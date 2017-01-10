import _thread
import os
import sqlite3

rules = {
    "n": "AND wordtype LIKE '%n.%'",
    "v": "AND wordtype LIKE '%v.%'",
    "adv": "AND wordtype LIKE '%adv.%'",
    "adj": "AND wordtype LIKE '%a.%'",
    "ing": "AND wordtype LIKE '%a.%' AND word LIKE '%ing'",
    "prep": "AND wordtype LIKE '%prep.%'",
    "pron": "AND wordtype LIKE '%pron.%'",
}


@yui.command('acr')
def acr(channel, argv):
    _thread.start_new_thread(acr_thread, (channel, argv))


def acr_thread(channel, argv):
    if len(argv) < 2 or len(argv) > 10:
        return

    arg = 1
    words = ''
    path = os.path.join(os.path.dirname(__file__), 'dict.sqlite')
    con = sqlite3.connect(path)
    with con:
        for c in argv[1]:
            rule = ""
            arg += 1
            if arg < len(argv) and len(argv[arg]) > 0:
                if argv[arg] in rules:
                    rule = rules[argv[arg]]
                else:
                    words += argv[arg] + ' '
                    continue;
            cur = con.cursor()
            cur.execute(
                "SELECT LOWER(word) FROM entries WHERE LOWER(word) LIKE '" + c + "%' " + rule + " ORDER BY RANDOM() LIMIT 1;")
            row = cur.fetchone()
            if row != None:
                words += (row[0] + ' ')
    yui.send_msg(channel, '"%s": %s' % (argv[1], words))
