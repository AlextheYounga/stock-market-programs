from app.lab.scrape.scraper import Scraper
from app.lab.core.functions import readTxtFile, is_date
import requests
import redis
import colored
from colored import stylize
from datetime import datetime
import dateutil.parser as parser
import time
import sys
import json


CURATED_SRCS = 'app/lab/news/data/curated_sources.txt'
URL = 'https://news.google.com/'
r = redis.Redis(host='localhost', port=6379, db=0, charset="utf-8", decode_responses=True)

class GoogleNews():
    def __init__(self, url=URL):
        self.url = url

    def scrapeNews(self, search_query, limit):
        from app.database.models import News
        scrape = Scraper()        
        articles = []            
        # Google News search 
        response = scrape.search(search_query)
        time.sleep(10)
        print(stylize(f"Grabbing links {search_query}", colored.fg("yellow")))
        soup = scrape.parseHTML(response)
        # Grab news cards
        cards = soup.find_all('article')[:limit] if (limit) else soup.find_all('article')
        print(stylize(f"{len(cards)} articles found.", colored.fg("yellow")))
        # Scan cards
        for card in cards:
            link = card.find('a').attrs.get('href', False)
            source = card.find_all('a')[2].text if (card.find_all('a')) else None
            #Check if newsitem is from a source we like
            if (link and self.checkLinkCache(link) and self.checkSource(source)):                
                headline = self.findHeadline(card)
                pubDate = self.findPubDate(card)                          
                if (pubDate): # Do not capture articles more than a day old.       
                    self.cacheLink(link) # Cache this link, we don't need to be here again.   
                    google_url = f"{self.url}{link.split('./')[1]}"
                    
                    print(stylize(f"Searching {google_url}", colored.fg("yellow")))
                    page = scrape.search(google_url, useHeaders=False)
                    time.sleep(3)
                    if (page and (isinstance(page, requests.models.Response)) and (page.ok)):       
                        if (News.objects.filter(url=link).exists() == False):                                 
                            page_soup = scrape.parseHTML(page)
                            newsitem = {
                                'url': page.url, # Get redirect link, not Google's fake link
                                'headline': headline,
                                'pubDate': pubDate,
                                'source': source,
                                'author': self.findAuthor(page_soup),
                                'soup': page_soup
                            }
                            article, created = News().store(newsitem)                            
                            r.set('news-soup-'+str(article.id), str(newsitem['soup']), 86400) # Caching the soup
                            articles.append(article)
                            print(stylize(f"Saved - {(newsitem.get('source', False) or '[Unsourced]')} - {newsitem.get('headline', None)}", colored.fg("green")))

        return articles

    def checkLinkCache(self, link):
        key = Scraper().stripParams(link).split('articles/')[1]
        checkCache = r.get('googlenews-'+key)
        if (checkCache and checkCache == link):
            return False #We've been here before.
        return True

    def cacheLink(self, link):        
        key = Scraper().stripParams(link).split('articles/')[1]
        r.set('googlenews-'+key, link, 86400)
        

    def checkSource(self, source):
        curated_srcs = readTxtFile(CURATED_SRCS)     
        for src in curated_srcs:            
            if (src in source):
                return True
        return False
     
    def findHeadline(self, card):
        if (card.find('h3')):
            return card.find('h3').text
        if (card.find('h4')):
            return card.find('h4').text
        return False


    def findAuthor(self, soup):
        # Correcting any anomalies.
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
        now = datetime.now()
        if (card):
            tag = card.find('time')
            if (tag and tag.attrs.get('datetime', False)):
                pubDate = tag.attrs.get('datetime', None)
                if(is_date(pubDate)):
                    if (('T' in pubDate) or ('Z' in pubDate)):                        
                        pubDateObj = parser.parse(pubDate).replace(tzinfo=None)
                    else:
                        pubDateObj = parser.parse(pubDate)
                    if ((now - pubDateObj).days == 0):
                        return pubDate                
        return False