from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
import time
import datetime
import requests
import colored
from colored import stylize
import sys


class Scraper():
    def __init__(self):
        self.timeout = 5
        self.storage = 'app/lab/scrape/storage'        
        self.headers = {
            'authority': 'www.bing.com',
            'dnt': '1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'sec-fetch-site': 'none',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-user': '?1',
            'sec-fetch-dest': 'document',
            'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
        }

    def search(self, url, useHeaders=True):
        params = {
            'timeout': self.timeout,
            'allow_redirects': True,
        }
        if (useHeaders):
            params['headers'] = self.headers

        try:
            response = requests.get(url, **params)
        except:
            print(stylize("Unexpected error:", colored.fg("red")))
            print(stylize(sys.exc_info()[0], colored.fg("red")))
            return False

        if (response.ok):
            time.sleep(2.3)
            return response
        return response.status_code

    def parseHTML(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')
        return (soup if (soup) else False)

    def stripParams(self, link):
        if ('?' in link):
            link = link.split('?')[0]
        if ('&' in link):
            link = link.split('&')[0]
        return link
