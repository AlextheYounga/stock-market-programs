from app.lab.scrape.scraper import Scraper
import html
from app.lab.core.output import printFullTable
from app.lab.fintwit.tweet import Tweet
import xml.etree.ElementTree as ET
from app.functions import filterNone
import re
import requests
import datetime
import time
import sys
from logs.hazlittlog import log
import os
import json
import django
from dotenv import load_dotenv
load_dotenv()
django.setup()
from app.database.models import Senate

logger = log('SenateWatcherAPI')
scraper = Scraper()


class SenateWatcher():
    def __init__(self):
        self.domain = 'https://senate-stock-watcher-data.s3-us-west-2.amazonaws.com'
        self.settings = {'timeout': 5}

    def getLatest(self):
        latest = self.scanLastReport()
        results = self.parseData(latest)
        senators = []
        for result in results:
            senate, created = Senate().store(result)
            if (created):
                logger.info(f"Created new record for {result['first_name']} {result['last_name']}")
                senators.append(senate)
            return senate, created # temp
        # return senators
        

    def scanLastReport(self, print_results=False):
        # https://senate-stock-watcher-data.s3-us-west-2.amazonaws.com/data/transaction_report_for_07_23_2021.json
        latest = self.fileMap()[0]
        url = f"{self.domain}/{latest}"
        print(url)
        try:
            response = requests.get(url, **self.settings).json()
        except:
            logger.error("Unexpected error:", sys.exc_info()[0])
            return None

        if (print_results):
            printFullTable(response, struct='dictlist')

        return response

    def scanAllReports(self):
        files = self.fileMap()
        for f in files:
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
                senate, created = Senate().store(result)
                if (created):
                    print(f"Created new record for {result['first_name']} {result['last_name']}")

    def parseData(self, data):
        results = []
        for senator in data:
            for transaction in senator['transactions']:
                tinfo = {
                    'first_name': senator.get('first_name', None),
                    'last_name': senator.get('last_name', None),
                    'office': senator.get('office', None),
                    'link': senator.get('ptr_link', None),
                    'date': datetime.datetime.strptime(transaction['transaction_date'], '%m/%d/%Y').strftime('%Y-%m-%d') if (transaction.get('transaction_date', False)) else None,
                    'ticker': transaction.get('ticker', None),
                    'owner': transaction.get('owner', None),
                    'sale_type': transaction.get('type', None),
                    'transaction': {
                        'asset_description': transaction.get('asset_description', ''),
                        "asset_type": transaction.get('asset_type', ''),
                        "comment": transaction.get('comment', '')
                    }
                }
                for k, v in tinfo.items():
                    if (v == '--'):
                        tinfo[k] = None
                    if ('<a' in v):
                        h = scraper.parseHTML(v)
                        tinfo[k] = h.text
                for k, v in tinfo['transaction'].items():
                    if ('<' in v):
                        strippedhtml = re.sub("<[^>]*>", "", v)
                        strippedLines = strippedhtml.replace('&nbsp;', '')
                        stripped = html.unescape(strippedLines)

                        tinfo['transaction'][k] = stripped


                amount_range = transaction.get('amount').split(' - ')
                tinfo['amount_low'] = int(amount_range[0].replace('$', '').replace(',', ''))
                tinfo['amount_high'] = int(amount_range[1].replace('$', '').replace(',', ''))

                results.append(tinfo)
        return results

    def fileMap(self):
        # https://senate-stock-watcher-data.s3-us-west-2.amazonaws.com/aggregate/filemap.xml
        fmap = []
        url = f"{self.domain}/aggregate/filemap.xml"
        try:
            response = requests.get(url, **self.settings)
        except:
            logger.error("Unexpected error:", sys.exc_info()[0])
            return None

        root = ET.fromstring(response.content)
        for child in root.iter('Key'):
            fmap.append(child.text)

        return fmap

    def tweet(self, senateObj, prompt):
        twit = Tweet()
        ticker = senateObj.ticker if senateObj.ticker else senateObj.transaction.get('asset_description', False)        
        if (ticker):
            headline = f"New stock market transaction for senator: {senateObj.first_name} {senateObj.last_name}."        
            relation = f"Relation: {senateObj.owner}" if (senateObj.owner != 'Self') else None
            saletype = senateObj.sale_type
            amount = f"${senateObj.amount_low} - ${senateObj.amount_high}"
            date = senateObj.date
            transaction = f"{saletype} {ticker} {amount} on {date}"
            c = senateObj.transaction.get('comment', False)
            comment = f"Comment: {c}" if (c and (c not in ['--', 'R']) and (len(c) > 2)) else None

            tweet_data = filterNone([
                headline, 
                relation,
                transaction,
                comment
            ])
            tweet = "\n".join(tweet_data),
            print(tweet)
            twit.send(tweet, prompt=prompt)