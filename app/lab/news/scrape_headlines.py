from app.database.models import StockNews
import django
from django.apps import apps
import requests
from bs4 import BeautifulSoup
from requests import api
from .functions import *
from ..core.api.batch import batchQuote
from ..core.functions import chunks, readTxtFile
from ..scrape.bing import bingSearch
import colored
from colored import stylize
import time
import sys
import json
import os
django.setup()

EXCHANGES = 'app/lab/news/data/exchanges.txt'


def save(results):
    # TODO: Get saving
    News = apps.get_model('database', 'News')
    Stock = apps.get_model('database', 'Stock')
    StockNews = apps.get_model('database', 'StockNews')
    for r in results:
        print(r)
        sys.exit()


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
    exchanges = readTxtFile(EXCHANGES)
    plausible = [] # A temporary vehicle to store strings that are likely tickers.
    stockfound = [] # A collection of all confirmed stocks.
    apiResults = {}

    for h in heap:
        # Finding all strings that look like stocks.
        h['stocks'] = []
        exchange_tickers = []
        # Find all capital letter strings, ranging from 1 to 5 characters, with optional dollar
        # signs preceded and followed by space.
        tickerlike = re.findall(r'[\S][$][A-Z]{1,5}[\S]*', str(h['soup']))
        for exchange in exchanges:
            exchangelike = re.findall(
                r''+exchange+'(?:\S+\s+)[A-Z]{1,5}', str(h['soup']))
            if (len(exchangelike) > 0):
                exchange_tickers = exchange_tickers + exchangelike
        
        del h['soup'] # Done with the soup.
        possible = tickerlike + exchange_tickers

        # Cleaning up strings that look like stocks.
        for tick in possible:
            if (type(tick) != list):
                if (':' in tick):
                    tick = cleanExchangeTicker(tick)
                cleaned = removeBadCharacters(tick)

                # Collecting strings that look like stocks.
                if ((cleaned) and (cleaned not in blacklist)):
                    plausible.append(cleaned)
                    h['stocks'].append(cleaned)
                
    # Specifying what I want from API
    apiOnly = [
        'symbol',
        'companyName',
        'latestPrice',
        'changePercent',
        'ytdChange',
        'volume'
    ]

    unique_plausible = list(dict.fromkeys(plausible))
    chunked_plausible = chunks(unique_plausible, 100)

    print(stylize("{} possibilities".format(len(unique_plausible)), colored.fg("yellow")))

    for i, chunk in enumerate(chunked_plausible):
        print(stylize("Sending heap to API", colored.fg("yellow")))
        batch = batchQuote(chunk)
        time.sleep(1)

        for ticker, stockinfo in batch.items():
            if (stockinfo.get('quote', False)):                
                print(stylize("{} stock found".format(ticker), colored.fg("green")))

                stockfound.append(ticker)
                filteredinfo = {key: stockinfo['quote'][key] for key in apiOnly}
                apiResults[ticker] = filteredinfo

    # Updating blacklist
    for un in unique_plausible:
        if (un not in stockfound):
            blacklist.append(un)

    # Updating main heap, removing bad tickers
    for h in heap:
        if (h['stocks']):
            for stock in h['stocks']:
                if (stock not in stockfound):
                    h['stocks'].remove(stock)                    

    updateBlacklist(blacklist)
    return heap


def top_news():
    heap = []
    queries = ['Finance']
    # queries = ['Top', 'Finance' 'Business', 'World']
    for q in queries:        
        url = f"https://www.bing.com/news/search?q={q}"
        response = bingSearch(url)
        time.sleep(3)

        if (response.status_code == 200):
            soup = BeautifulSoup(response.text, 'html.parser')
            links = soup.find_all("a", {"class": "title"})

            # Begin traversing links
            for link in cleanLinks(links):
                print(stylize("Searching... " +
                      link['href'], colored.fg("yellow")))
                page = bingSearch(link['href'])

                if (page and page.status_code == 200):
                    soup = BeautifulSoup(page.text, 'html.parser')

                    result = {
                        'url': link['href'],
                        'headline': link.contents,
                        'source': link.attrs.get('data-author', None),
                        'soup': soup,
                    }
                    heap.append(result)
                    time.sleep(1)

    results = scanHeap(heap)
    save(results)
    return results

