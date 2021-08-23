from app.lab.scrape.scraper import Scraper
from app.lab.core.api.iex import IEX
import html
from app.lab.core.output import printFullTable
from app.lab.fintwit.tweet import Tweet
import xml.etree.ElementTree as ET
from app.functions import filterNone
from hashlib import sha256
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
iex = IEX()

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
        return senators

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
                uticker = transaction.get('ticker', None)
                tdata = {
                    'first_name': senator.get('first_name', None),
                    'last_name': senator.get('last_name', None),
                    'office': senator.get('office', None),
                    'link': senator.get('ptr_link', None),
                    'date': datetime.datetime.strptime(transaction['transaction_date'], '%m/%d/%Y').strftime('%Y-%m-%d') if (transaction.get('transaction_date', False)) else None,                    
                    'owner': transaction.get('owner', None),
                    'sale_type': transaction.get('type', None),
                    'transaction': {
                        'asset_description': transaction.get('asset_description', None),
                        "asset_type": transaction.get('asset_type', None),
                        "comment": transaction.get('comment', None)
                    }
                }

                def format_data(obj):                    
                    for k, v in obj.items():
                        if (v and isinstance(v, str)):
                            if ('--' in v):
                                obj[k] = None
                    for k, v in obj['transaction'].items():
                        if (v):
                            if ('--' in v):
                                obj['transaction'][k] = None
                            if ('<' in v):
                                strippedhtml = re.sub("<[^>]*>", "", v)
                                strippedLines = strippedhtml.replace('&nbsp;', '')
                                stripped = html.unescape(strippedLines)

                                obj['transaction'][k] = stripped
                    amount_range = transaction.get('amount').split(' - ')
                    obj['amount_low'] = int(amount_range[0].replace('$', '').replace(',', ''))
                    obj['amount_high'] = int(amount_range[1].replace('$', '').replace(',', ''))
                    obj['hash_key'] = self.generateHash(obj)
                    return obj            

                def format_ticker(ticker):
                    if (ticker):
                        if ('<a' in ticker):
                            h = scraper.parseHTML(ticker)
                            ticker = h.text
                        if ('--' in ticker):
                            ticker = None
                    return ticker
                ticker = format_ticker(uticker)

                if (ticker and (' ' in ticker)):
                    tickers = ticker.split(' ')
                    tickers.remove('')                    
                    for t in tickers:    
                        dupdata = tdata.copy()   
                        dupdata['ticker'] = t   
                        fdata = format_data(dupdata)    
                        results = results[:] + [fdata]                        
                else:                  
                    tdata['ticker'] = ticker                    
                    fdata = format_data(tdata)
                    results = results[:] + [fdata]    
        return results    

    def generateHash(self, data):
        keys = [
            data['last_name'],
            data['date'],
            (data['ticker'] or data['transaction']['asset_description']),
            data['sale_type'],
            data['owner'],
        ]
        hashstring = ''.join(keys).replace(' ', '')
        hashkey = sha256(hashstring.encode('utf-8')).hexdigest()
        return hashkey

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

    def tweet(self, senateObj, prompt=True):
        twit = Tweet()
        ticker = senateObj.ticker if senateObj.ticker else senateObj.transaction.get('asset_description', False)
        if (ticker):
            headline = f"New stock market transaction for senator: {senateObj.first_name} {senateObj.last_name}."
            relation = f"Relation: {senateObj.owner}" if (senateObj.owner != 'Self') else None
            saletype = senateObj.sale_type
            amount = f"${senateObj.amount_low} - ${senateObj.amount_high}"
            date = senateObj.date
            transaction = f"{saletype} ${ticker} {amount} on {date}"
            c = senateObj.transaction.get('comment', False)
            comment = f"Comment: {c}" if (c and (c not in ['--', 'R']) and (len(c) > 2)) else None

            tweet_data = filterNone([
                headline,
                relation,
                transaction,
                comment
            ])
            tweet = "\n".join(tweet_data)            
            twit.send(tweet, prompt=prompt)
