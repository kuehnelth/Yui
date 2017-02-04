# coding=utf-8

import random

@yui.command('roll', 'random', 'rnd')
def rnd(argv, user):
    """Random roll. Usage: roll [max] | roll [min] [max]"""
    min_roll = 1
    max_roll = 100

    try:
        if len(argv) > 2:
            min_roll = int(argv[1])
            max_roll = int(argv[2])
        elif len(argv) > 1:
            max_roll = int(argv[1])

        roll = random.randint(min_roll, max_roll)
        if min_roll == 1:
            return '%s rolls %d out of %d!' % (user.nick, roll, max_roll)
        else:
            return '%s rolls %d between %d and %d!' % (user.nick, roll, min_roll, max_roll)
    except:
        pass

@yui.command('flip', 'coin')
def flip():
    """Flip a coin."""
    return random.choice(['Heads!', 'Tails!'])

@yui.command('choose')
def choose(argv):
    """Randomly choose one of multiple things. Usage: choose <thing1> <thing2> [thing3] ..."""
    if len(argv) > 2:
        return 'I choose ' + random.choice(argv[1:])
