import re
import sys
import os
from ..core.functions import frequencyInList, wordVariator


def removeBadCharacters(word):
    if (isinstance(word, list)):
        word = str(word[0])

    regex = re.compile('[^A-Z]')
    word = regex.sub('', word)

    if (len(word) > 5):
        return False

    if any(c for c in word if c.islower()):
        return False

    return word


def blacklistWords():
    txtfile = open("app/lab/reddit/blacklist_words.txt", "r")

    blacklist = []
    for line in txtfile:
        stripped_line = line.strip()
        line_list = stripped_line.split()
        blacklist.append(str(line_list[0]))

    txtfile.close()

    return list(dict.fromkeys(blacklist))


def updateBlacklist(lst):
    txtfile = "app/lab/reddit/blacklist_words.txt"
    os.remove(txtfile)
    with open(txtfile, 'w') as f:
        for item in lst:
            f.write("%s\n" % item)


def sentimentScanner(thoughts):
    feels = {
        'bullish': [
            'buy',
            'hold',
            'hodl',
            'moon',
            'long',
            'calls'
            'bull',
            'bought',
            'positive',
        ],
        'bearish': [
            'short',
            'sell',
            'puts',
            'bear',
            'sold',
            'against',
            'negative',
        ]
    }

    for side, terms in feels.items():
        for term in wordVariator(terms):
            if (term in thoughts):
                return side

    return False


def sentimentCalculation(terms):
    count = len(terms)
    sides = ['bullish', 'bearish']
    feels = []

    for feel in sides:
        feels.append(frequencyInList(terms, feel))
    
    result = sides[feels.index(max(feels))]
    percent = round(max(feels) / count * 100)

    if (percent == 50):
        return 'neutral 50%'
    
    return "{} {}%".format(result, percent)


