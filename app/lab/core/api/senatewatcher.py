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
from app.database.models import Congress, CongressTransaction


logger = log('SenateWatcherAPI')
scraper = Scraper()
iex = IEX()
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

class SenateWatcher():
    def __init__(self):
        self.domain = 'https://senate-stock-watcher-data.s3-us-west-2.amazonaws.com'
        self.settings = {'timeout': 5}

    def getLatest(self):
        latest = self.scanLastReport()
        results = self.parseData(latest)
        trades = []
        for result in results:
            trade, created = CongressTransaction().store(result)
            if (created):
                logger.info(f"Created new record for {result['first_name']} {result['last_name']}")
                trades.append(trade)
        return trades

    def priceAtDate(self, ticker, date):
        pad = iex.priceAtDate(ticker, date)
        if (pad):
            if (isinstance(pad, list)):
                return pad[0]['close']
            return pad['close']
        return None

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
            first_name = senator.get('first_name', None)
            last_name = senator.get('last_name', None)
            name = ' '.join([first_name, last_name]).title()
            congress = Congress.objects.filter(name=name).first()

            if (not congress):
                congress, created = Congress().store({
                    'first_name': first_name,
                    'last_name': last_name,
                    'name': name,
                    'house': 'Senate',
                    'office': senator.get('office', None),
                    'district': senator.get('district', None),
                    'total_gain_dollars': None,
                    'total_gain_percent': None,
                    'trades': None,
                })



            for trade in senator['transactions']:
                sale_type = SALETYPES[trade['type']] if (trade.get('type', False)) else None
                transactionJSON = {}
                link = senator.get('ptr_link', None)
                link_id = self.getLinkId(link)
                transactionJSON.update({'link_id': link_id or None})
                uticker = trade.get('ticker', None)

                transaction = {
                    'congress_id': congress.id,
                    'first_name': congress.first_name,
                    'last_name': congress.last_name,
                    'sale_type': sale_type,
                    'date': self.parseDate(trade.get('transaction_date', None)),
                    "asset_type": trade.get('asset_type', None),
                    'owner': trade.get('owner', None),
                    'link': link,
                    'description': trade.get('asset_description', None),
                    'comment': trade.get('comment', None),
                    'transaction': transactionJSON,
                }

                def format_data(obj):
                    for k, v in obj.items():
                        if (v and isinstance(v, str)):
                            if ('--' in v):
                                obj[k] = None
                            if ('<' in v):
                                strippedhtml = re.sub("<[^>]*>", "", v)
                                strippedLines = strippedhtml.replace('&nbsp;', '')
                                stripped = html.unescape(strippedLines)
                                obj[k] = stripped
                                
                    for k, v in obj['transaction'].items():
                        if (v):
                            if ('--' in v):
                                obj['transaction'][k] = None
                            if ('<' in v):
                                strippedhtml = re.sub("<[^>]*>", "", v)
                                strippedLines = strippedhtml.replace('&nbsp;', '')
                                stripped = html.unescape(strippedLines)

                                obj['transaction'][k] = stripped
                                
                    # Sorting amounts
                    amount_range = trade.get('amount').split(' - ')
                    if (len(amount_range) == 2):
                        obj['amount_low'] = int(amount_range[0].replace('$', '').replace(',', ''))
                        obj['amount_high'] = int(amount_range[1].replace('$', '').replace(',', ''))
                    else:
                        amount_range = amount_range[0]
                        if ('+' in amount_range):
                            obj['amount_low'] = int(amount_range.replace('$', '').replace('+', '').replace(',', ''))
                            obj['amount_high'] = None
                        else:
                            obj['amount_low'] = None
                            obj['amount_high'] = int(amount_range.replace('$', '').replace('-', '').replace(',', ''))

                    obj['price_at_date'] = self.priceAtDate(obj['ticker'], obj['date'])                    
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
                        dupdata = transaction.copy()
                        dupdata['ticker'] = t
                        fdata = format_data(dupdata)
                        results = results[:] + [fdata]
                else:
                    transaction['ticker'] = ticker
                    fdata = format_data(transaction)
                    results = results[:] + [fdata]
        return results

    def parseDate(self, date):
        if (date):
            try:
                fdate = datetime.datetime.strptime(date, '%m/%d/%Y')
            except ValueError:
                try:
                    fdate = datetime.datetime.strptime(date, '%Y-%m-%d')
                except ValueError:
                    return None
            if (fdate and len(str(fdate.year)) == 4):
                return fdate.strftime('%Y-%m-%d')
        return None
    
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
            (data['transaction'].get('link_id', None) or 'nolink'),
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

    def tweet(self, trades, prompt=True):
        # A bad way of doing this, I know. It's a product of how the models used to be structured.
        # Kept in the interest of saving time.
        twit = Tweet()
        orders = {}

        for trade in trades:      
            if (trade.ticker):
                senator = trade.congress
                relation = f" Owner: {trade.owner}" if (trade.owner and trade.owner != 'Self') else ''
                ticker = f"${trade.ticker}"
                saletype = trade.sale_type.replace('_', ' ').title()
                date = trade.date.strftime('%b %d')
                amount = f"${trade.amount_low} - ${trade.amount_high}" if (trade.amount_low and trade.amount_high) else f"${trade.amount_low or trade.amount_high}"

                bodyline = f"{saletype} {ticker} {amount} on {date}{relation}\n"

                if (senator.last_name not in orders):
                    orders[senator.last_name] = {
                        'headline': f"New market transaction for senator: {senator.name}.\n",
                        'body': [],
                    }

                orders[senator.last_name]['body'].append(bodyline)

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

            
