from app.lab.news.bing_news import BingNews
from app.lab.news.google_news import GoogleNews
from app.lab.core.api.batch import batchQuote
from app.lab.core.functions import chunks, readTxtFile, is_date
import datetime
from dateutil.parser import parse
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
CURATED = 'app/lab/news/data/curated.txt'
PAYWALLED = 'app/lab/news/data/paywalled.txt'

class NewsFeed():
    def __init__(self, aggregator='bing'):
        self.aggregator = aggregator
        self.engine = self.callModule()

    def callModule(self):
        if (self.aggregator == 'bing'):
            return BingNews()
        if (self.aggregator == 'google'):
            return GoogleNews()

    def curated(self, limit=None):
        self.searchDomains(CURATED, limit=limit)

    def paywalled(self):
        self.searchDomains(PAYWALLED, search_stocks=False)
    
    def trending(self, limit=None):
        card_soup = []
        search_query = f"{self.engine.url}"
        card_soup = card_soup + self.engine.collectNewsCards(search_query, limit=limit)
        heap = self.engine.scanLinks(card_soup)
        results = self.findStocks(heap)
        self.save(results)
        return results

    def feed(self):
        self.trending()
        self.organicTop()
        self.searchDomains(CURATED)
        
        return

    def organicTop(self, limit=None):
        queries = ['Finance', 'Stocks', 'Business']

        card_soup = []
        for query in queries:
            search_query = f"{self.engine.url}search?q={query}"
            card_soup = card_soup + self.engine.collectNewsCards(search_query, limit=limit)
        heap = self.engine.scanLinks(card_soup)
        results = self.findStocks(heap)
        self.save(results)
        return results

    def searchDomains(self, lst_path, limit=None, search_stocks=True):
        domains = readTxtFile(lst_path)

        card_soup = []
        for domain in domains:
            url = f"{self.engine.url}search?q=site%3A{domain}"
            card_soup = card_soup + self.engine.collectNewsCards(url, limit=limit)
        results = self.engine.scanLinks(card_soup)
        if (search_stocks):
            results = self.findStocks(results)
        self.save(results)
        return results

    def apiSearch(self):
        # TODO Figure api search
        sys.exit()
    
    def cleanExchangeTicker(self, exchange):
        if (exchange != ''):
            if (':' in exchange):
                ticker = exchange.split(':')[1]
                return ticker.strip()
            return False


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
    
    def findStocks(self, heap):
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
        blacklist = self.blacklistWords()
        exchanges = readTxtFile(EXCHANGES)
        # A temporary vehicle to store strings that are likely tickers.
        plausible = []
        apiResults = {}  # A temp collection of all confirmed stocks.

        for h in heap:
            # Finding all strings that look like stocks.
            h['stocks'] = []
            exchange_tickers = []
            # Find all capital letter strings, ranging from 1 to 5 characters, with optional dollar
            # signs preceded and followed by space.
            tickerlike = re.findall(r'[\S][$][A-Z]{1,5}[\S]*', str(h['soup'].text))
            for exchange in exchanges:
                # exchangelike = re.findall(r''+exchange+'(?:\S+\s+)[A-Z]{1,5}', str(h['soup'].text))
                exchangelike = re.findall('(?<='+exchange+'[?:])[A-Z]{1,7}', str(h['soup'].text))
                if (len(exchangelike) > 0):
                    exchange_tickers = exchange_tickers + exchangelike

            del h['soup']  # Done with the soup.
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
                        h['stocks'].append(list(dict.fromkeys(cleaned)))

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

                    filteredinfo = {
                        key: stockinfo['quote'][key] for key in apiOnly
                    }
                    apiResults[ticker] = filteredinfo

        # Updating blacklist
        for un in unique_plausible:
            if (un not in apiResults.keys()):
                blacklist.append(un)

        # Updating main heap, removing bad tickers
        for h in heap:
            h['stockinfo'] = {}
            if (h['stocks']):
                for stock in h['stocks']:
                    if (stock not in apiResults.keys()):
                        h['stocks'].remove(stock)
                        continue
                    h['stockinfo'][stock] = apiResults[stock]

        self.updateBlacklist(blacklist)
        return heap
        
                
    def save(self, results):
        News = apps.get_model('database', 'News')
        Stock = apps.get_model('database', 'Stock')

        for r in results:
            article = News.objects.filter(url=r['url'])
            if (r.get('stockinfo', False)):
                for ticker, info in r['stockinfo'].items():
                    stock = Stock.objects.update_or_create(
                        ticker=ticker,
                        defaults={
                            'name': info.get('companyName', None),
                            'lastPrice': info.get('latestPrice', None),
                            'changePercent': info.get('changePercent', None),
                            'ytdChange': info.get('ytdChange', None),
                            'volume': info.get('volume', None),
                        }
                    )

                    News.stocknews_set.update_or_create(
                        article=article[0],
                        defaults = {
                            'stock': stock[0],
                            'ticker': ticker,
                            'companyName': info.get('companyName', None),
                        }
                    )
                    print(stylize(f"Saved {ticker} from article.", colored.fg("green")))