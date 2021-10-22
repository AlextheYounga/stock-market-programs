from app.lab.scrape.scraper import Scraper
from app.lab.congress.house import House
from app.lab.congress.senate import Senate
from django.core.cache import cache
from app.lab.core.output import printFullTable
from app.lab.fintwit.tweet import Tweet
import xml.etree.ElementTree as ET
import requests
import datetime
import time
import sys
from hazlitt_log import log
import os
import json
import django
from dotenv import load_dotenv
load_dotenv()
django.setup()
from app.functions import compare_dicts, get_hazlitt_path, readTxtFile, writeTxtFile
from app.database.models import Congress, CongressTransaction

logger = log('CongressWatcherAPI')
scraper = Scraper()
DOMAINS = {
    'senate': 'https://senate-stock-watcher-data.s3-us-west-2.amazonaws.com',
    'house': 'https://house-stock-watcher-data.s3-us-west-2.amazonaws.com'
}
FILEMAP = {
    'senate': '/aggregate/filemap.xml',
    'house': '/data/filemap.xml'
}
SALETYPES = {
    'Sale (Partial)': 'partial-sell',
    'Sale (Full)': 'sell',
    'Purchase': 'buy',
    'Exchange': 'exchange',
    'sale_full': 'sell',
    'purchase': 'buy',
    'sale_partial': 'partial-sell',
    'exchange': 'exchange',
}


class CongressWatcher():
    def __init__(self, branch):
        self.branch = branch
        self.domain = DOMAINS[branch]
        self.cache_key = f"{branch}watch-api-"
        self.settings = {'timeout': 5}
        self.file_ledger = f"{get_hazlitt_path()}/app/lab/congress/filemaps/{branch}_filemap.txt"
        self.filemap = f"{self.domain}{FILEMAP[self.branch]}"
        self.congress = Senate() if (branch == 'senate') else House()

    def scanReports(self):
        unscanned = self.compareLedger()
        trades = []

        if (unscanned):
            for f in unscanned:
                report = self.readReport(f)
                parsed_data = self.parseData(report)
                for data in parsed_data:
                    trade, created = CongressTransaction().store(data)
                    trades.append(trade)
                    if (created):
                        logger.info(f"Created new record for {data['first_name']} {data['last_name']}")

                self.updateLedger(f)

            return trades

    def readReport(self, filepath, print_results=False):
        # https://senate-stock-watcher-data.s3-us-west-2.amazonaws.com/data/transaction_report_for_07_23_2021.json
        # https://house-stock-watcher-data.s3-us-west-2.amazonaws.com/data/transaction_report_for_07_23_2021.json
        url = f"{self.domain}/{filepath}"
        print(url)
        try:
            response = requests.get(url, **self.settings).json()
        except:
            logger.error("Unexpected error:", sys.exc_info()[0])
            return None

        if (print_results):
            printFullTable(response, struct='dictlist')

        return response

    def compareLedger(self):
        scanned = readTxtFile(self.file_ledger)
        latest = self.fileMap()

        unscanned = set(latest).difference(scanned)
        return unscanned

    def updateLedger(self, fil):
        ledger = readTxtFile(self.file_ledger)
        writeTxtFile(self.file_ledger, ledger + [fil])

    def scanAllReports(self):
        files = self.fileMap()
        for f in files:
            if (cache.get(f"{self.cache_key}{f}")):
                continue
            url = f"{self.domain}/{f}"
            print(url)

            time.sleep(1)  # Slow is smooth and smooth is fast.
            try:
                response = requests.get(url, **self.settings).json()

            except:
                logger.error("Unexpected error:", sys.exc_info()[0])
                return None

            results = self.parseData(response)
            for result in results:
                rep, created = Congress().store(result)
                if (created):
                    print(f"Created new record for {result['first_name']} {result['last_name']}")
            cache.set(f"{self.cache_key}{f}", 1)

    def fileMap(self):
        # https://senate-stock-watcher-data.s3-us-west-2.amazonaws.com/aggregate/filemap.xml
        # https://house-stock-watcher-data.s3-us-west-2.amazonaws.com/data/filemap.xml
        fmap = []
        try:
            response = requests.get(self.filemap, **self.settings)
        except:
            logger.error("Unexpected error:", sys.exc_info()[0])
            return None

        root = ET.fromstring(response.content)
        for child in root.iter('Key'):
            fmap.append(child.text)

        return fmap

    def parseData(self, data):
        return self.congress.parseApiData(data)

    def tweet(self, trades, prompt=True):
        """
        Builds tweets line by line and threads tweet by tweet.
        """

        def writeLine(trade):
            """
            Specifically building each line of tweet based on each trade.
            """
            relation = f" Owner: {trade.owner}" if (trade.owner and trade.owner != 'Self') else ''
            ticker = f"${trade.ticker}"
            saletype = trade.sale_type.replace('_', ' ').title()
            date = datetime.datetime.strptime(trade.date, '%Y-%m-%d').strftime('%b %d') if (isinstance(trade.date, str)) else trade.date.strftime('%b %d')
            amount = f"${trade.amount_low} - ${trade.amount_high}" if (trade.amount_low and trade.amount_high) else f"${trade.amount_low or trade.amount_high}"

            bodyline = f"{saletype} {ticker} {amount} on {date}{relation}\n"
            return bodyline

        def buildThreads(orders):
            """
            Incrimentally building each tweet by adding lines until it becomes longer than
            280 characters. Once the tweet reaches just below 280, it is appended to thread object.
            Returns dict of threads keyed by congress member name.
            """
            thread = {}               
            for name, order in orders.items():
                if (name not in thread):
                    thread[name] = []

                headline = order['headline']
                body = ""

                for line in order['body']:
                    if (len(headline + body + line) >= 280):  
                        tweet = headline + body
                        thread[name].append(tweet)
                        body = ""  # Resetting body

                    body = (body + line)

                tweet = headline + body  # Handles remaining lines.
                thread[name].append(tweet)

            return thread
        
        """Tweet building start"""
        twit = Tweet()
        orders = {}

        for trade in trades:
            rep = trade.congress  # Get representitive info
            if (trade.ticker):
                if (rep.last_name not in orders):
                    orders[rep.last_name] = {
                        'headline': f"New market transaction for house rep: {rep.name}.\n",
                        'body': [],
                    }

                bodyline = writeLine(trade)
                orders[rep.last_name]['body'].append(bodyline)  # Building tweet line by line.

        threads = buildThreads(orders)

        for rep, thread in threads.items():
            twit.send_thread(thread)
