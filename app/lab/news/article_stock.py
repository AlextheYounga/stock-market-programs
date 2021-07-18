from app.lab.core.api.batch import batchQuote
from app.lab.core.functions import chunks, readTxtFile
from bs4 import BeautifulSoup
import redis
import re
import colored
from colored import stylize
import time
import sys
import json
import os
import django
from django.apps import apps
django.setup()

EXCHANGES = 'app/lab/news/data/exchanges.txt'
BLACKLISTWORDS = 'app/lab/news/data/blacklist_words.txt'
BLACKLISTPAGES = 'app/lab/news/data/blacklist_pages.txt'
CURATED = 'app/lab/news/data/curated_domains.txt'
PAYWALLED = 'app/lab/news/data/paywalled.txt'
r = redis.Redis(host='localhost', port=6379, db=0, charset="utf-8", decode_responses=True)

class ArticleStock():
    def __init__(self, articles):
        self.articles = articles
        self.news = apps.get_model('database', 'News')
        self.stock = apps.get_model('database', 'Stock')
        self.stocknews = apps.get_model('database', 'StockNews')
    
    def find(self):
        plausible = self.stockRegex()
        apiResults = self.apiConfirmStocks(plausible) #Confirms stocks via API
        self.save(apiResults)


    def stockRegex(self):
        """
        Scans for stocks amidst page soup.

        Returns
        -------
        plausible       :list
                        list of plausible stocks to be confirmed later.
        """
        plausible = [] # A temporary vehicle to store strings that are likely tickers.
        exchanges = readTxtFile(EXCHANGES) 
        blacklist = self.blacklistWords()

        for article in self.articles:
            # Finding all strings that look like stocks.
            article_stocks = []
            exchange_tickers = []
            soup_string = r.get('news-soup-'+str(article.id))
            if (soup_string):
                soup = BeautifulSoup(soup_string, 'html.parser')

                # Find all capital letter strings, ranging from 1 to 5 characters, with optional dollar
                # signs preceded and followed by space.
                tickerlike = re.findall(r'[\S][$][A-Z]{1,5}[\S]*', str(soup.text))
                for exchange in exchanges:
                    # exchangelike = re.findall(r''+exchange+'(?:\S+\s+)[A-Z]{1,5}', str(h['soup'].text))
                    exchangelike = re.findall('(?<='+exchange+'[?:])[A-Z]{1,7}', str(soup.text))
                    if (len(exchangelike) > 0):
                        exchange_tickers = exchange_tickers + exchangelike

                possible = tickerlike + exchange_tickers
                
                # Cleaning up strings that look like stocks.
                for tick in possible:
                    if (type(tick) != list):
                        if (':' in tick):
                            tick = self.cleanExchangeTicker(tick)
                        cleaned = self.removeBadCharacters(tick)

                        # Collecting strings that look like stocks.
                        if ((cleaned) and (cleaned not in blacklist)):
                            plausible.append(cleaned)
                            article_stocks.append(cleaned)  
                list_string = ','.join(article_stocks)                        
                r.set('stocknews-plausible-'+str(article.id), list_string, 600)

        return plausible

    
    def apiConfirmStocks(self, plausible):
        """
        Sends all plausible stocks from the stockRegex() to the API to determine if they're actually a stock.
        Saves stocks it finds and saves them in relation to their news article.

        Parameters
        ----------
        plausible     : list 
                        list of plausible stocks
        """
        # Specifying what I want from API
        apiOnly = [
            'symbol',
            'companyName',
            'latestPrice',
            'changePercent',
            'ytdChange',
            'volume'
        ]
        
        apiResults = {}
        blacklist = self.blacklistWords()
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

                    filteredinfo = {
                        key: stockinfo['quote'][key] for key in apiOnly
                    }
                    apiResults[ticker] = filteredinfo

        # Updating blacklist
        for un in unique_plausible:
            if (un not in apiResults.keys()):
                blacklist.append(un)
        self.updateBlacklist(blacklist)

        return apiResults

                
    def save(self, apiResults):
        for article in self.articles: 
            cached_stocks = r.get('stocknews-plausible-'+str(article.id))
            articlestocks = cached_stocks.split(',') if cached_stocks else False
            if (articlestocks):
                for ticker in articlestocks:
                    stockinfo = apiResults[ticker]                    
                    stock = self.stock.objects.update_or_create(
                        ticker=ticker,
                        defaults={
                            'name': stockinfo.get('companyName', None),
                            'lastPrice': stockinfo.get('latestPrice', None),
                            'changePercent': stockinfo.get('changePercent', None),
                            'ytdChange': stockinfo.get('ytdChange', None),
                            'volume': stockinfo.get('volume', None),
                        }
                    )

                    self.stocknews.objects.update_or_create(
                        article=article,
                        defaults = {
                            'stock': stock[0],
                            'ticker': stockinfo['symbol'],
                            'companyName': stockinfo.get('companyName', None),
                        }
                    )
                    print(stylize(f"Saved {stockinfo['symbol']} from article.", colored.fg("green")))

    
    def blacklistWords(self):
        txtfile = open(BLACKLISTWORDS, "r")

        blacklist = []
        for line in txtfile:
            stripped_line = line.strip()
            line_list = stripped_line.split()
            blacklist.append(str(line_list[0]))

        txtfile.close()

        return list(dict.fromkeys(blacklist))


    def updateBlacklist(self, lst):
        txtfile = BLACKLISTWORDS
        os.remove(txtfile)
        with open(txtfile, 'w') as f:
            for item in lst:
                f.write("%s\n" % item)

    def removeBadCharacters(self, word):
        if (isinstance(word, list)):
            word = str(word[0])

        regex = re.compile('[^A-Z]')
        word = regex.sub('', word)

        if (len(word) > 7):
            return False

        if any(c for c in word if c.islower()):
            return False

        return word

    def cleanExchangeTicker(self, exchange):
        if (exchange != ''):
            if (':' in exchange):
                ticker = exchange.split(':')[1]
                return ticker.strip()
            return False
