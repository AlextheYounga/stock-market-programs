from app.lab.news.engines.bing_news import BingNews
from app.lab.news.engines.google_news import GoogleNews
from app.lab.news.article_stock import ArticleStock
from app.lab.core.functions import readTxtFile
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

class NewsFeed():
    def __init__(self, aggregator='bing'):
        self.aggregator = aggregator
        self.engine = self.callModule()

    def callModule(self):
        if (self.aggregator == 'bing'):
            return BingNews()
        if (self.aggregator == 'google'):
            return GoogleNews()
    
    def feed(self):
        self.trending()
        self.organicTop()
        self.searchDomains(CURATED)
        
        return

    def curated(self, limit=None):
        self.searchDomains(CURATED, limit=limit)
    

    def trending(self, limit=None):
        search_query = f"{self.engine.url}"
        articles = self.engine.scrapeNews(search_query, limit=limit)
        ArticleStock(articles).find()
        return


    def organicTop(self, limit=None):
        queries = ['Finance', 'Stocks', 'Business']
        for query in queries:
            search_query = f"{self.engine.url}search?q={query}"
            articles = self.engine.scrapeNews(search_query, limit=limit)
            ArticleStock(articles).find()


    def searchDomains(self, lst_path, limit=None, search_stocks=True):
        domains = readTxtFile(lst_path)
        for domain in domains:
            url = f"{self.engine.url}search?q=site%3A{domain}"
            articles = self.engine.scrapeNews(url, limit=limit)
            ArticleStock(articles).find()


    def apiSearch(self):
        # TODO Figure api search
        sys.exit()
    




