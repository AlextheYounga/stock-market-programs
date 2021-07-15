from app.lab.scrape.scraper import Scraper
from app.lab.core.functions import readTxtFile, is_date
import datetime
from dateutil.parser import parse
import colored
from colored import stylize
import time
import sys
import json

BLACKLISTWORDS = 'app/lab/news/data/blacklist_words.txt'
BLACKLISTPAGES = 'app/lab/news/data/blacklist_pages.txt'
CURATED = 'app/lab/news/data/curated.txt'
PAYWALLED = 'app/lab/news/data/paywalled.txt'
URL = 'https://news.google.com/'

class GoogleNews():
    def __init__(self, url=URL):
        self.url = url

    def collectNewsCards(self, searchq):
        scrape = Scraper()                              
        response = scrape.search(searchq)        
        print(stylize(f"Grabbing links {searchq}", colored.fg("yellow")))
        time.sleep(1)
        if (response.status_code == 200):
            soup = scrape.parseHTML(response)
            card_soup = soup.find_all('article')
            print(stylize(f"{len(card_soup)} articles found.", colored.fg("yellow")))
            return card_soup

    def scanLinks(self, card_soup):
        heap = []
        scrape = Scraper()
        for card in card_soup:
            link = self.checkLink(card.find('a').attrs.get('href'))
            if (link):
                headline = card.find('h3').text
                source = card.find_all('a')[2].text if (card.find_all('a')) else None
                pubDate = self.findPubDate(card)
    
                print(stylize(f"Searching {scrape.stripParams(link)}", colored.fg("yellow")))
                page = scrape.search(link)
                if (page and page.status_code == 200):
                    page_soup = scrape.parseHTML(page)
                    #TODO: Find how to get redirect URL
                    print(page)
                    sys.exit()
                    result = {
                        'url': page.url,
                        'headline': headline,
                        'pubDate': pubDate,
                        'source': source,
                        'author': self.findAuthor(page_soup),
                        'soup': page_soup
                    }
                    print(result)
                    sys.exit()
                    heap.append(result)
                    time.sleep(1)
        return heap

    
    def checkLink(self, link):
        if (link):
            if (link[0] == '.'):
                return f"{self.url}{link.split('./')[1]}"
        return False
     

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

    
    def findPubDate(self, card):
        if (card):
            tag = card.find('time')
            if (tag and tag.attrs.get('datetime', False)):
                return tag.attrs.get('datetime', None)