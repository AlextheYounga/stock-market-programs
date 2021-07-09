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
            'dnt': '1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'sec-fetch-site': 'none',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-user': '?1',
            'sec-fetch-dest': 'document',
            'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
        }

    def search(self, url):
        try:
            response = requests.get(
                url, headers=self.headers, timeout=self.timeout)
        except:
            print(stylize("Unexpected error:", colored.fg("red")))
            print(stylize(sys.exc_info()[0], colored.fg("red")))
            return False

        if (response.status_code == 200):
            time.sleep(1.3)
            return response
        return response.status_code

    def parseXML(self, response, findtree=''):
        """
        findtree items must follow item->item->item format!
        """
        tree = ET.parse(response)  # create element tree object
        root = tree.getroot()  # get root element

        if (findtree):
            collect = []
            path = './'

            # build path
            for branch in findtree.split('->'):
                path = path + f"{branch}/"

            # iterate items
            for item in root.findall(path):
                collect.append(item)

            return collect

        if (root):
            return root
        return False

    def parseHTML(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')
        if (soup):
            return soup
        return False

    def stripParams(self, link):
        if ('?' in link):
            link = link.split('?')[0]
        if ('&' in link):
            link = link.split('&')[0]
        return link
