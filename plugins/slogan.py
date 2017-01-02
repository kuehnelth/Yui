import re
import random

slogans = [
    "Melts in {0}'s Mouth, Not in Your Hands",
    "Just Do {0}",
    "Shave Time. Shave {0}.",
    "Because {0}'s Worth It",
    "There are some things {0} can't buy. For everything else, there's MasterCard.",
    "The Ultimate {0}ing Machine",
    "Every {0} Helps",
    "A {0} is Forever",
    "Betcha Can't Eat Just {0}",
    "Vorsprung durch {0}",
    "{0} Runs on Dunkin",
    "America Runs on {0}",
    "I'm Lovin' {0}",
    "{0}'s Lovin' It",
    "All the {0} That's Fit to Print",
    "Maybe she's born with it. Maybe it's {0}.",
    "Don´t leave home without {0}",
    "Think {0}.",
    "I'd walk a mile for a {0}.",
    "Between {0} and madness lies obsession.",
    "Between love and madness lies {0}.",
    "Don't be {0}.",
    "Outwit. Outplay. {0}.",
    "Save {0}. Live Better.",
    "If you want to impress {0}, put him on your Black list.",
    "The {0} is always and completely {0}!",
    "The customer is always and completely {0}!",
    "When there is no {0}.",
    "At the heart of the {0}.",
    "The greatest tragedy is {0}.",
    "{0} is no substitute.",
    "Impossible is {0}.",
    "{0} is the path to joy.",
    "Pleasure is the path to {0}.",
    "Let your {0} do the walking.",
    "Because {0}'s complicated enough.",
    "Connecting {0}.",
    "{0}. It's a Mind Game.",
    "Power, beauty and {0}.",
    "{0}'s everywhere you want to be.",
    "Reach out and touch {0}.",
    "Get N or get {0}."
]

@yui.command('slogan','slg')
def slogan(argv,user):
    if len(argv) > 1:
        user = argv[1]
    response = random.choice(slogans)
    formatted = response.format(user)
    return '"%s"' % formatted
