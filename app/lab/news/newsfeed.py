
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

EXCHANGES = 'app/lab/news/data/exchanges.txt'
BLACKLISTWORDS = 'app/lab/news/data/blacklist_words.txt'
BLACKLISTPAGES = 'app/lab/news/data/blacklist_words.txt'
DOMAINS = 'app/lab/news/data/whitelist_domains.txt'

class NewsFeed():


    def feed():
        sys.exit()

    def top(self):
        heap = []
        scrape = Scraper()
        domains = readTxtFile(DOMAINS)
        for domain in domains:            
            url = f"https://www.bing.com/news/search?q=site%3A{domain}"            
            response = scrape.search(url)
            print(stylize(f"Grabbing links {url}", colored.fg("yellow")))
            time.sleep(1)
            if (response.status_code == 200):
                soup = scrape.parseHTML(response)
                print(soup)
                link_soup = soup.find_all('div', attrs={'class': 'newsitem'})

                for item in link_soup:
                    title = item.find("a", {'class': 'title'})
                    link = title.attrs.get('href')
                    if (checkLink(link)):
                        headline = title.text
                        description = item.find("div", {'class': 'snippet'}).text
                        source = title.attrs.get('data-author', None)

                        print(stylize(f"Searching {scrape.stripParams(link)}", colored.fg("yellow")))
                        page = scrape.search(link)
                        if (page and page.status_code == 200):
                            page_soup = scrape.parseHTML(page)
                            result = {
                                'url': link,
                                'headline': headline,
                                'description': description,
                                'pubDate': findPubDate(page_soup),
                                'source': source,
                                'author': findAuthor(page_soup),
                                'soup': page_soup,
                            }
                            sys.exit()
                            heap.append(result)
                            time.sleep(1)
            else: 
                print(stylize(f"Response {response.status_code}", colored.fg("red")))

        results = findStocks(heap)
        self.save(results)
        return results


    def save(self, results):
        import django
        from django.apps import apps
        django.setup()

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
                for item in r['stockinfo'].items():
                    print(item)
                    sys.exit()
                    stock = Stock.objects.update_or_create(
                        ticker=item['ticker'],
                        defaults={
                            'name': item.get('companyName', None),
                            'lastPrice': item.get('latestPrice', None),
                            'changePercent': item.get('changePercent', None),
                            'ytdChange': item.get('ytdChange', None),
                            'volume': item.get('volume', None),
                        }
                    )

                    StockNews.objects.update_or_create(
                        article=article,
                        defaults = {
                            'stock': stock,
                            'ticker': item['ticker'],
                            'companyName': item.get('companyName', None),
                        }
                    )
                    print(stylize(f"Saved {item['ticker']} from article.", colored.fg("green")))



def findAuthor(soup):
    print(soup)
    for meta in soup.head.find_all('meta'):
        print(meta)
        for prop in ['property', 'name']:
            print(str(meta.attrs.get(prop)))
            if ('author' in str(meta.attrs.get(prop))):
                author = meta.attrs.get('content')
                return author
    for tag in soup.body.find_all(['span', 'div', 'a', 'p']):
        classes = tag.attrs.get('class')
        if (classes):  
            for clas in list(classes):
                if ('author' in clas):      
                    return tag.text
    return None



def findPubDate(soup):
    for meta in soup.head.find_all('meta'):
        for prop in ['property', 'name']:
            if ('publish' in str(meta.attrs.get(prop))):
                metaDate = meta.attrs.get('content')
                if (is_date(metaDate)):
                    pubDate = re.search(r'\d{4}-\d{2}-\d{2}([\s]\d{2}:\d{2}:\d{2})?', metaDate).group(0)
                    return pubDate


def findStocks(heap):
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
    # A temporary vehicle to store strings that are likely tickers.
    plausible = []
    apiResults = {}  # A temp collection of all confirmed stocks.

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

        del h['soup']  # Done with the soup.
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

    updateBlacklist(blacklist)
    return heap


def cleanExchangeTicker(exchange):
    if (exchange != ''):
        if (':' in exchange):
            ticker = exchange.split(':')[1]
            return ticker.strip()
        return False


def blacklistWords():
    txtfile = open(BLACKLISTWORDS, "r")

    blacklist = []
    for line in txtfile:
        stripped_line = line.strip()
        line_list = stripped_line.split()
        blacklist.append(str(line_list[0]))

    txtfile.close()

    return list(dict.fromkeys(blacklist))

def checkLink(link):
    blacklist_pgs = readTxtFile(BLACKLISTPAGES)
    for pg in blacklist_pgs:
        if (pg in link):
            return False
    return link

def updateBlacklist(lst):
    txtfile = BLACKLISTWORDS
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


