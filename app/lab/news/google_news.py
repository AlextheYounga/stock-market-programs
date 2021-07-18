from app.lab.scrape.scraper import Scraper
from app.lab.core.functions import readTxtFile
import requests
import redis
import colored
from colored import stylize
import time
import sys
import json
from django.apps import apps


CURATED_SRCS = 'app/lab/news/data/curated_sources.txt'
URL = 'https://news.google.com/'
r = redis.Redis(host='localhost', port=6379, db=0, charset="utf-8", decode_responses=True)

class GoogleNews():
    def __init__(self, url=URL):
        self.url = url

    def scrapeNews(self, search_query, limit):
        scrape = Scraper()        
        articles = []            
        # Google News search 
        response = scrape.search(search_query) 
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
            if (link and self.checkSource(source)):
                headline = self.findHeadline(card)
                pubDate = self.findPubDate(card)                    
                google_url = f"{self.url}{link.split('./')[1]}"
                
                print(stylize(f"Searching {google_url}", colored.fg("yellow")))
                page = scrape.search(google_url, useHeaders=False)
                if (page and (isinstance(page, requests.models.Response)) and (page.ok)):                    
                    page_soup = scrape.parseHTML(page)
                    newsitem = {
                        'url': page.url, # Get redirect link, not Google's fake link
                        'headline': headline,
                        'pubDate': pubDate,
                        'source': source,
                        'author': self.findAuthor(page_soup),
                        'soup': page_soup
                    }
                    article = self.save(newsitem)
                    articles.append(article)

        return articles

    def checkSource(self, source):
        curated_srcs = readTxtFile(CURATED_SRCS)     
        for src in curated_srcs:
            if ((src in source) or (src == source)):                
                return True
        return False
     
    def findHeadline(self, card):
        if (card.find('h3')):
            return card.find('h3').text
        if (card.find('h4')):
            return card.find('h4').text
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

    def save(self, newsitem):        
        News = apps.get_model('database', 'News')
        article = News.objects.update_or_create(
            url=newsitem['url'],
            defaults = {
            'headline': newsitem.get('headline', None),
            'author': newsitem.get('author', None),
            'source': newsitem.get('source', None),
            'description': newsitem.get('description', None),
            'pubDate': newsitem.get('pubDate', None)}
        )
        # Caching the soup
        r.set('news-soup-'+str(article[0].id), str(newsitem['soup']), 86400)
        print(stylize(f"Saved - {(newsitem.get('source', False) or '[Unsourced]')} - {newsitem.get('headline', None)}", colored.fg("green")))
        return article[0]