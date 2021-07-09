
from app.lab.scrape.scraper import Scraper
from ..core.api.batch import batchQuote
from ..core.functions import chunks, readTxtFile
import re
import colored
from colored import stylize
import time
import sys
import json
import os

EXCHANGES = 'app/lab/news/data/exchanges.txt'


class NewsFeed():    
    # TODO: FInish switching to RSS
    def top():
        heap = []
        scrape = Scraper()
        queries = ['Finance' 'Business', 'World']
        for q in queries:
            url = f"https://www.bing.com/news/search?q={q}&format=rss"
            response = scrape.search(url)                        
            time.sleep(3)

            if (response.status_code == 200):
                news_items = scrape.parseXML(response, findtree='channel->item')

                for item in news_items():
                    link = item.attrib('link')
                    page = scrape.search(link)
                    if (page and page.status_code == 200):
                        soup = scrape.parseHTML(page)
                        result = {
                            'url': link,
                            'headline': item.attrib('title'),
                            'description': item.attrib('description'),
                            'pubDate': item.attrib('pubDate'),
                            'source': item.attrib('News:Source'),
                            'source': link.attrs.get('data-author', None),
                            'soup': soup,
                        }
                        heap.append(result)
                        time.sleep(1)


        results = scanHeap(heap)
        save(results)
        return results


    # def top():
    #     heap = []
    #     scrape = Scraper()
    #     queries = ['Finance' 'Business', 'World']
    #     for q in queries:
    #         url = f"https://www.bing.com/news/search?q={q}"
    #         response = scrape.search(url)
    #         time.sleep(3)

    #         if (response.status_code == 200):
    #             soup = BeautifulSoup(response.text, 'html.parser')
    #             links = soup.find_all("a", {"class": "title"})

    #             # Begin traversing links
    #             for link in cleanLinks(links):
    #                 print(stylize("Searching... " +
    #                       link['href'], colored.fg("yellow")))
    #                 page = scrape.search(link['href'])

    #                 if (page and page.status_code == 200):
    #                     soup = BeautifulSoup(page.text, 'html.parser')

    #                     result = {
    #                         'url': link['href'],
    #                         'headline': link.contents,
    #                         'source': link.attrs.get('data-author', None),
    #                         'soup': soup,
    #                     }
    #                     heap.append(result)
    #                     time.sleep(1)

    #     results = scanHeap(heap)
    #     save(results)
    #     return results


                    
def save(results):
    import django
    from django.apps import apps
    django.setup()

    # TODO: Get saving
    News = apps.get_model('database', 'News')
    Stock = apps.get_model('database', 'Stock')
    StockNews = apps.get_model('database', 'StockNews')

    for r in results:
        article = News.objects.create(
            url=r['url'],
            headline=r.get('headline', None),
            author=r.get('author', None),
            source=r.get('source', None),
        )
        # TODO: MAKe this work
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

                StockNews.objects.create(
                    article=article,
                    stock=stock,
                    ticker=item['ticker'],
                    companyName=item.get('companyName', None),
                    )

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
            exchangelike = re.findall(r''+exchange+'(?:\S+\s+)[A-Z]{1,5}', str(h['soup']))
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

    print(stylize("{} possibilities".format(
        len(unique_plausible)), colored.fg("yellow")))

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