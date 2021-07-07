from ..core.functions import readTxtFile
import sys
import json
import os
import re


def cleanExchangeTicker(exchange):
    if (exchange != ''):
        if (':' in exchange):
            ticker = exchange.split(':')[1]
            return ticker.strip()
        return False


def blacklistWords():
    txtfile = open("app/lab/news/data/blacklist_words.txt", "r")

    blacklist = []
    for line in txtfile:
        stripped_line = line.strip()
        line_list = stripped_line.split()
        blacklist.append(str(line_list[0]))

    txtfile.close()

    return list(dict.fromkeys(blacklist))



def cleanLinks(links):
    whitelist = []
    blacklist_sites = readTxtFile('app/lab/news/data/blacklist_sites.txt', fmt=list)
    blacklist_urls = readTxtFile('app/lab/news/data/blacklist_urls.txt', fmt=list)

    for link in links:
        link_attrs = link.attrs
        if (link_attrs.get('href', False)):
            keep = True
            if (blacklist_urls):
                for bu in blacklist_urls:
                    if (bu in link_attrs['href']):
                        keep = False
            if (blacklist_sites):
                for bs in blacklist_sites:
                    if (link_attrs.get('data-author', False) and (bs in link_attrs['data-author'])):
                        
                        keep = False
            if (keep == True):
                whitelist.append(link)

    return whitelist


def updateBlacklist(lst):
    txtfile = "app/lab/news/data/blacklist_words.txt"
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
