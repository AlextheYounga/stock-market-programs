import django
from django.apps import apps
import requests
from bs4 import BeautifulSoup
from datetime import datetime, date
from ..core.api.batch import quoteStatsBatchRequest
from ..core.functions import dataSanityCheck
from ..core.output import printStockResults
from ..fintwit.tweet import send_tweet
import colored
from colored import stylize
import time
import sys
import json
import os
django.setup()


def blacklist_urls(link):
    urls = ['www.nasdaq.com']
    skip = False
    for b in urls:
        if b in link:
            skip = True

    return skip


def blacklist_stocks(tickers):
    pruned = []
    blacklist = [
        'AAPL',
        'APPL',
        'AMZN',
        'MSFT',
        'DIS',
        'NFLX',
        'KO',
        'TSLA',
        'GOOG',
    ]
    for t in tickers:
        if (t in blacklist):
            continue
        pruned.append(t)

    return pruned


def exchanges():
    return [
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


def clean_tickers(tickers):
    Stock = apps.get_model('database', 'Stock')
    db_tickers = Stock.objects.all().values_list('ticker', flat=True)
    cleaned = []

    def checkLowerCase(t):
        for c in t: #Checking for lowercase letters
            if (c.islower()):
                return True
        return False
    
    for t in tickers:
        if(' ' not in t):
            if ('.' not in t):
                if (t != ''):      
                    if (checkLowerCase(t) == False):
                        if (t in db_tickers):
                            if (':' in t):
                                t = t.split(':')[1]
                            if (t not in cleaned):
                                cleaned.append(t)
    pruned = blacklist_stocks(cleaned)

    return pruned


def scrape_news(query="best+stocks+to+buy"):
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
    tickers = []

    try:
        url = 'https://www.bing.com/news/search?q={}'.format(query)
        results = requests.get(url, headers=headers)
    except:
        print(stylize("Unexpected error:", colored.fg("red")))
        print(stylize(sys.exc_info()[0], colored.fg("red")))        

    soup = BeautifulSoup(results.text, 'html.parser')
    links = soup.find_all("a", {"class": "title"})

    for link in links:
        if (blacklist_urls(link['href'])):
            continue

        print(stylize("Searching... "+link['href'], colored.fg("yellow")))

        page = requests.get(link['href'], headers=headers)
        soup = BeautifulSoup(page.text, 'html.parser')
        all_links = soup.find_all("a", href=True)

        for l in all_links:
            for exc in exchanges():
                searchstr = exc+':'
                if (searchstr in l.text):
                    tickers.append(l.text.split(':')[1])
                if ((l.get('href', False)) and ('quote' in l['href'])):
                    tickers.append(l.text)

        time.sleep(1)

    if (tickers):
        tickers = clean_tickers(tickers)
        printStockResults(tickers)
