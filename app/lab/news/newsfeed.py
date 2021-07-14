
from app.lab.scrape.scraper import Scraper
from ..core.api.batch import batchQuote
from ..core.functions import chunks, readTxtFile, is_date
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
AGGREGATOR_INDEX = {
    'bing': {
        'url': 'https://www.bing.com/news/',
        'card': ('div', {'class': 'newsitem'}),
        'linkObj': ("a", {'class': 'linkTag'}),
        'sourceTag': ("div", {'class': 'source'}),
        'sourceAttr': 'data-author',
        'description': ("div", {'class': 'snippet'}),
    },
    'google': {
        'url': 'https://news.google.com/',
        'card': 'article',
        'linkObj': 'a',
        'source': 'div',
        'description': None,
    },
}
class NewsFeed():
    def __init__(self, aggregator='bing'):
        self.aggregator = aggregator
        
    def latestNews(self):
        News = apps.get_model('database', 'News')
        latest_news = News.objects.all().order_by('created_at')[:40]
        

        return latest_news
    
    def mentionedStocks(self):
        StockNews = apps.get_model('database', 'StockNews')
        recent_stocks = StockNews.objects.all().order_by('created_at')[:10]

        return recent_stocks


    def feed(self):
        self.organicTop()
        self.searchDomains(CURATED)
        self.searchDomains(PAYWALLED, search_stocks=False)
        
        return

    def organicTop(self):
        queries = ['Finance', 'Stocks', 'Business']
        aggregator = AGGREGATOR_INDEX[self.aggregator]['url']
        card_soup = []
        for query in queries:
            url = f"{aggregator}search?q={query}"
            card_soup = card_soup + self.collectNewsCards(url)
        heap = self.scanLinks(card_soup)
        results = self.findStocks(heap)
        self.save(results)
        return results

    def searchDomains(self, lst_path, search_stocks=True):
        domains = readTxtFile(lst_path)
        aggregator = AGGREGATOR_INDEX[self.aggregator]['url']
        card_soup = []
        for domain in domains:
            url = f"{aggregator}search?q=site%3A{domain}"
            card_soup = card_soup + self.collectNewsCards(url)
        results = self.scanLinks(card_soup)
        if (search_stocks):
            results = self.findStocks(results)
        self.save(results)
        return results

    def apiSearch(self):
        # TODO Figure api search
        sys.exit()

    def collectNewsCards(self, url):
        scrape = Scraper()                              
        response = scrape.search(url)        
        cardTag = AGGREGATOR_INDEX[self.aggregator]['card']
        print(stylize(f"Grabbing links {url}", colored.fg("yellow")))
        time.sleep(1)
        if (response.status_code == 200):
            soup = scrape.parseHTML(response)
            card_soup = soup.find_all(cardTag)
            print(stylize(f"{len(card_soup)} articles found.", colored.fg("yellow")))
            return card_soup

    def scanLinks(self, card_soup):
        heap = []
        scrape = Scraper()
        linkTag = AGGREGATOR_INDEX[self.aggregator]['linkObj']
        descripTag = AGGREGATOR_INDEX[self.aggregator].get('description', False)
        sourceTag = AGGREGATOR_INDEX[self.aggregator].get('source', False)
        sourceAttr = AGGREGATOR_INDEX[self.aggregator].get('sourceAttr', False)
        for card in card_soup:
            linkObj = card.find(linkTag)
            link = self.checkLink(linkObj.attrs.get('href'))
            
            if (link):
                headline = linkObj.text
                description = card.find(descripTag).text if (descripTag) else None
                if (sourceTag):
                    source = card.find(sourceTag).text
                else: 
                    source = linkObj.attrs.get(sourceAttr, None) if (sourceAttr) else None              

                print(stylize(f"Searching {scrape.stripParams(link)}", colored.fg("yellow")))
                page = scrape.search(link)
                if (page and page.status_code == 200):
                    page_soup = scrape.parseHTML(page)
                    result = {
                        'url': scrape.stripParams(link),
                        'headline': headline,
                        'description': description,
                        'pubDate': self.findPubDate(card, page_soup),
                        'source': source,
                        'author': self.findAuthor(page_soup),
                        'soup': page_soup
                    }
                    heap.append(result)
                    time.sleep(1)
        return heap
    
    def findAuthor(self, soup):

        def checkAuthor(author):
            badCharacters = ['facebook', '.']
            for bc in badCharacters:
                if (bc in author):
                    return None
            return author

        for meta in soup.head.find_all('meta'):
            for prop in ['property', 'name']:
                if ('author' in str(meta.attrs.get(prop))):
                    author = meta.attrs.get('content')
                    return checkAuthor(author)
        for tag in soup.body.find_all(['span', 'div', 'a', 'p']):
            classes = tag.attrs.get('class')
            if (classes):  
                for clas in list(classes):
                    if ('author' in clas):      
                        return checkAuthor(tag.text)
        return None

    
    def findPubDate(self, card=None, soup=None):
        if (card):
            for tag in card.find_all(['span', 'div', 'a', 'p']):
                if (tag.attrs.get('datetime', False)):
                    return tag.attrs.get('datetime', None)
        if (soup):
            for meta in soup.head.find_all('meta'):
                for prop in ['property', 'name']:
                    if ('publish' in str(meta.attrs.get(prop))):
                        metaDate = meta.attrs.get('content')
                        if (is_date(metaDate)):
                            # pubDate = re.search(r'\d{4}-\d{2}-\d{2}([\s]\d{2}:\d{2}:\d{2})?', metaDate)
                            if (metaDate):
                                # return pubDate.group(0)
                                return metaDate
        return None
    
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

    def checkLink(self, link):
        aggregator = AGGREGATOR_INDEX[self.aggregator]['url']
        blacklist_pgs = readTxtFile(BLACKLISTPAGES)
        for pg in blacklist_pgs:
            if (pg in link):
                return False
        if (link[0] == '.'):
            return f"{aggregator}{link.split('.')[1]}"
        return link

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
        StockNews = apps.get_model('database', 'StockNews')

        for r in results:
            article = News.objects.update_or_create(
                url=r['url'],
                defaults = {
                'headline': r.get('headline', None),
                'author': r.get('author', None),
                'source': r.get('source', None),
                'description': r.get('description', None),
                'pubDate': r.get('pubDate', None)}
            )
            print(stylize(f"Saved {r.get('source', '[Unsourced]')} article", colored.fg("green")))
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

                    StockNews.objects.update_or_create(
                        article=article[0],
                        defaults = {
                            'stock': stock[0],
                            'ticker': ticker,
                            'companyName': info.get('companyName', None),
                        }
                    )
                    print(stylize(f"Saved {ticker} from article.", colored.fg("green")))