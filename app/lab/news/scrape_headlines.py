import django
from django.apps import apps
import requests
from bs4 import BeautifulSoup
from datetime import datetime, date
from .functions import *
from ..core.api.batch import batchQuote
from ..core.functions import dataSanityCheck, frequencyInList, chunks
from ..core.output import printFullTable
from ..fintwit.tweet import send_tweet
import colored
from colored import stylize
import time
import sys
import json
import os
django.setup()


EXCHANGES = [
    'NYSE',
    'NASDAQ',
    'LSE',
    'TSX',
    'NSE',
    'ASX',
    'BSE',
    'TYO',
    'SSE',
    'OTC',
    'OTCMKTS'
]


def scanHeap(heap):
    """
    This function takes a list of text blobs and scans all words for potential stocks based on a regex formula. 
    The function will cross-reference every potential stock with IEX to determine whether or not it is an actual stock.
    Strings that do not pass the test will be sent to the blacklist to prevent future lookups.

    Parameters
    ----------
    heap     : list
               list of text blobs taken from reddit

    Returns
    -------
    dict
        list of results confirmed to be stocks
    """
    blacklist = blacklistWords()
    possible = []
    keyedByStock = {}
    stockfound = []
    results = []

    for h in heap:
        exchange_tickers = []
        # Find all capital letter strings, ranging from 1 to 5 characters, with optional dollar
        # signs preceded and followed by space.
        tickerlike = re.findall(r'[\S][$][A-Z]{1,5}[\S]*', str(h))
        for exchange in EXCHANGES:
            exchangelike = re.findall(
                r''+exchange+'(?:\S+\s+)[A-Z]{1,5}', str(h))
            if (len(exchangelike) > 0):
                exchange_tickers = exchange_tickers + exchangelike

        tickers = tickerlike + exchange_tickers

        target_strings = []
        for tick in tickers:
            if (type(tick) != list):
                if (':' in tick):
                    tick = cleanExchangeTicker(tick)

                target_strings.append(removeBadCharacters(tick))

        for string in target_strings:
            if ((string) and (string not in blacklist)):
                possible.append(string)
                if (string in keyedByStock):
                    keyedByStock[string].append(h['url'])
                    continue
                keyedByStock[string] = [h['url']]

    unique_possibles = list(dict.fromkeys(possible))
    chunked_strings = chunks(unique_possibles, 100)

    apiOnly = [
        'symbol',
        'companyName',
        'latestPrice',
        'changePercent',
        'ytdChange',
        'volume'
    ]

    print(stylize("{} possibilities".format(
        len(unique_possibles)), colored.fg("yellow")))

    for i, chunk in enumerate(chunked_strings):

        print(stylize("Sending heap to API", colored.fg("yellow")))
        batch = batchQuote(chunk)
        time.sleep(1)

        for ticker, stockinfo in batch.items():

            if (stockinfo.get('quote', False)):

                result = {
                    'ticker': ticker,
                    'urls': keyedByStock[ticker],
                }

                print(stylize("{} stock found".format(ticker), colored.fg("green")))

                filteredinfo = {
                    key: stockinfo['quote'][key] for key in apiOnly}
                result.update(filteredinfo)
                results.append(result)

    # Updating blacklist
    for un in unique_possibles:
        if (un not in stockfound):
            blacklist.append(un)

    updateBlacklist(blacklist)
    return results


def scrape_news(query):
    print(stylize("Searching {}".format(query), colored.fg("green")))
    headers = {
        'dnt': '1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'sec-fetch-site': 'none',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-user': '?1',
        'sec-fetch-dest': 'document',
        'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
    }
    heap = []

    try:
        url = 'https://www.bing.com/news/search?q={}'.format(query)
        response = requests.get(url, headers=headers, timeout=5)
    except:
        print(stylize("Unexpected error:", colored.fg("red")))
        print(stylize(sys.exc_info()[0], colored.fg("red")))

    if (response.status_code == 200):
        soup = BeautifulSoup(response.text, 'html.parser')
        links = soup.find_all("a", {"class": "title"})

        # Begin traversing links
        for link in cleanLinks(links):
            print(stylize("Searching... "+link, colored.fg("yellow")))
            try:
                page = requests.get(link, headers=headers, timeout=5)
            except:
                print(stylize("Unexpected error:", colored.fg("red")))
                print(stylize(sys.exc_info()[0], colored.fg("red")))

            if (page and page.status_code == 200):
                soup = BeautifulSoup(page.text, 'html.parser')
                heapMap = {
                    'url': link,
                    'soup': soup.text,
                }
                heap.append(heapMap)
                time.sleep(1)

    results = scanHeap(heap)
    

    # News = apps.get_model('database', 'News')
    # for key, value in results.items():
