from app.lab.scrape.scraper import Scraper
from app.lab.core.functions import readTxtFile, is_date
import datetime
from dateutil.parser import parse
import colored
from colored import stylize
import time
import sys
import json
import django
from django.apps import apps

BLACKLISTPAGES = 'app/lab/news/data/blacklist_pages.txt'
CURATED = 'app/lab/news/data/curated_domains.txt'
PAYWALLED = 'app/lab/news/data/paywalled.txt'
URL = 'https://www.bing.com/news/'

class BingNews():
    def __init__(self, url=URL):
        self.url = url

    def collectNewsCards(self, search_query, limit):
        scrape = Scraper()                              
        response = scrape.search(search_query)        
        print(stylize(f"Grabbing links {search_query}", colored.fg("yellow")))
        if (response.ok):
            soup = scrape.parseHTML(response)
            card_soup = soup.find_all('div', {'class': 'newsitem'})[:limit] if (limit) else soup.find_all('div', {'class': 'newsitem'})
            print(stylize(f"{len(card_soup)} articles found.", colored.fg("yellow")))
            return card_soup

    def scanLinks(self, card_soup):
        heap = []
        scrape = Scraper()

        for card in card_soup:
            title = card.find("a", {'class': 'title'})
            link = title.attrs.get('href')
            if (self.checkLink(link)):
                headline = title.text
                description = (card.find("div", {'class': 'snippet'}).text or None)
                source = title.attrs.get('data-author', None)
    
                print(stylize(f"Searching {scrape.stripParams(link)}", colored.fg("yellow")))
                page = scrape.search(link)
                if (page and page.ok):
                    page_soup = scrape.parseHTML(page)
                    newsitem = {
                        'url': scrape.stripParams(link),
                        'headline': headline,
                        'description': description,
                        'pubDate': self.findPubDate(card, page_soup),
                        'source': source,
                        'author': self.findAuthor(page_soup),
                        'soup': page_soup
                    }
                    self.save(newsitem)
                    heap.append(newsitem)
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

    
    def findPubDate(self, page):
        if (page):
            for meta in page.head.find_all('meta'):
                for prop in ['property', 'name']:
                    if ('publish' in str(meta.attrs.get(prop))):
                        metaDate = meta.attrs.get('content')
                        if (is_date(metaDate)):
                            # pubDate = re.search(r'\d{4}-\d{2}-\d{2}([\s]\d{2}:\d{2}:\d{2})?', metaDate)
                            if (metaDate):
                                # return pubDate.group(0)
                                return metaDate
        return None
    
    def checkLink(self, link):
        blacklist_pgs = readTxtFile(BLACKLISTPAGES)
        for pg in blacklist_pgs:
            if (pg in link):
                return False

    def save(self, newsitem):
        News = apps.get_model('database', 'News')
        News.objects.update_or_create(
            url=newsitem['url'],
            defaults = {
            'headline': newsitem.get('headline', None),
            'author': newsitem.get('author', None),
            'source': newsitem.get('source', None),            
            'pubDate': newsitem.get('pubDate', None)}
        )
        print(stylize(f"Saved {(newsitem.get('source', False) or 'unsourced')} article", colored.fg("green")))