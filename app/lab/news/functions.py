import django
from django.apps import apps
import sys
import json
import os
import re
django.setup()


def cleanExchangeTicker(exchange):    
    if (exchange != ''):
        if (':' in exchange):
            ticker = exchange.split(':')[1]
            return ticker.strip()
        return False


def blacklistWords():
    txtfile = open("app/lab/news/blacklist_words.txt", "r")

    blacklist = []
    for line in txtfile:
        stripped_line = line.strip()
        line_list = stripped_line.split()
        blacklist.append(str(line_list[0]))

    txtfile.close()

    return list(dict.fromkeys(blacklist))


def blacklistUrls():
    txtfile = open("app/lab/news/blacklist_urls.txt", "r")

    blacklist = []
    for line in txtfile:
        stripped_line = line.strip()
        line_list = stripped_line.split()
        blacklist.append(str(line_list[0]))

    txtfile.close()

    return blacklist


def cleanLinks(links):
    whitelist = []
    blacklist = blacklistUrls()
    if (blacklist):
        for bl in blacklist:
            for link in links:
                if (bl in link['href']):
                    continue
                whitelist.append(link['href'])
    else:
        for link in links:
            whitelist.append(link['href'])

    return whitelist


def updateBlacklist(lst):
    txtfile = "app/lab/news/blacklist_words.txt"
    os.remove(txtfile)
    with open(txtfile, 'w') as f:
        for item in lst:
            f.write("%s\n" % item)


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
