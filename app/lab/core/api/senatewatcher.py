from app.lab.scrape.scraper import Scraper
from app.lab.core.api.iex import IEX
from django.core.cache import cache
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
from hazlitt_log import log
import os
import json
import django
from dotenv import load_dotenv
load_dotenv()
django.setup()
from app.database.models import Congress


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
            senator, created = Congress().store(result)
            if (created):
                logger.info(f"Created new record for {result['first_name']} {result['last_name']}")
                senators.append(senator)
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
            if (cache.get(f"senatewatch-api-{f}")):
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
                senate, created = Congress().store(result)
                if (created):
                    print(f"Created new record for {result['first_name']} {result['last_name']}")
            cache.set(f"senatewatch-api-{f}", 1)

    def parseData(self, data):
        results = []
        for senator in data:
            for transaction in senator['transactions']:
                uticker = transaction.get('ticker', None)
                tdata = {
                    'first_name': senator.get('first_name', None),
                    'last_name': senator.get('last_name', None),
                    'house': 'Senate',
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
    
    def getLinkId(self, link):
        if link:
            if ('ptr/' in link):                
                return link.split('ptr/')[1].split('/')[0]
            else:
                return link.split('paper/')[1].split('/')[0]
        return None

    def generateHash(self, data):
        keys = [     
            data['last_name'],       
            data['date'],
            (data['ticker'] or data['description']),
            (data['transaction']['link_id'] or 'nolink'),
            data['sale_type'],
            str(data['amount_low']),
            data['owner'] or 'Self',
            str(data['congress_id']),
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

    def tweet(self, senators, prompt=True):
        twit = Tweet()
        orders = {}

        for sen in senators:            
            if (sen.ticker):
                print(sen.last_name, sen.ticker)
                relation = f" Owner: {sen.owner}" if (sen.owner and sen.owner != 'Self') else ''
                ticker = f"${sen.ticker}"
                saletype = sen.sale_type.replace('_', ' ').title()
                date = sen.date.strftime('%b %d')
                amount = f"${sen.amount_low} - ${sen.amount_high}" if (sen.amount_low and sen.amount_high) else f"${sen.amount_low or sen.amount_high}"

                bodyline = f"{saletype} {ticker} {amount} on {date}{relation}\n"

                if (sen.last_name not in orders):
                    orders[sen.last_name] = {
                        'headline': f"New market transaction for senator: {sen.first_name} {sen.last_name}.\n",
                        'body': [],
                    }

                orders[sen.last_name]['body'].append(bodyline)

        for name, t in orders.items():
            headline = t['headline']
            body = ""
            for line in t['body']:
                if (len(headline + body + line) > 280):                
                    tweet = headline + body
                    twit.send(tweet, prompt=prompt)                    
                    body = ""
                body = (body + line)
            
            tweet = headline + body
            twit.send(tweet, prompt=prompt)        

            
