from app.lab.scrape.scraper import Scraper
from app.lab.core.api.iex import IEX
# from app.database.redisdb.rdb import Rdb
from django.core.cache import cache
from app.lab.core.output import printFullTable
from app.lab.fintwit.tweet import Tweet
import xml.etree.ElementTree as ET
from app.functions import filterNone
from hashlib import sha256
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

logger = log('HouseWatcherAPI')
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


class HouseWatcher():
    def __init__(self):
        self.domain = 'https://house-stock-watcher-data.s3-us-west-2.amazonaws.com'
        self.settings = {'timeout': 5}

    def getLatest(self):
        latest = self.scanLastReport()
        results = self.parseData(latest)
        reps = []
        for result in results:
            rep, created = Congress().store(result)
            if (created):
                logger.info(f"Created new record for {result['first_name']} {result['last_name']}")
                reps.append(rep)
        return reps

    def priceAtDate(self, ticker, date):
        pad = iex.priceAtDate(ticker, date)
        if (pad):
            return pad
        return None

    def scanLastReport(self, print_results=False):
        # https://house-stock-watcher-data.s3-us-west-2.amazonaws.com/data/transaction_report_for_07_23_2021.json
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
            if (cache.get(f"housewatch-api-{f}")):
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
            cache.set(f"housewatch-api-{f}", 1)

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

    def parseData(self, data):
        results = {}
        for rep in data:
            for trade in rep['transactions']:
                first_name = rep.get('first_name', None),
                last_name = rep.get('last_name', None),
                name = ' '.join(first_name, last_name).title()
                sale_type = SALETYPES[trade['transaction_type']] if (trade.get('transaction_type', False)) else None
                transactionJSON = {'cap_gains_over_200': trade.get('cap_gains_over_200', None)}
                link = rep.get('source_ptr_link', None)
                link_id = self.getLinkId(link)
                transactionJSON.update({'link_id': link_id or None})

                # TODO: Finish reforming data
                # tdata = {
                #     'ticker': trade.get('ticker', None),
                #     'house': 'House',
                #     'office': rep.get('office', None),
                #     'link': rep.get('source_ptr_link', None),
                #     'district': rep.get('district', None),
                #     'date': self.parseDate(trade.get('transaction_date', None)),
                #     'filing_date': self.parseDate(rep.get('filing_date', None)),
                #     'owner': trade.get('owner', None),
                #     'sale_type': trade.get('transaction_type', None),
                #     'transaction': {
                #         "asset_description": trade.get('description', None),
                #         "cap_gains_over_200": trade.get('cap_gains_over_200', None),
                #     }
                # }
                
                # results[] How to keep these two together
                congress = {
                    'first_name': first_name,
                    'last_name': last_name,
                    'name': name,
                    'house': 'House',
                    'office': rep.get('office', None),
                    'district': rep.get('district', None),
                    'total_gain_dollars': None,
                    'total_gain_percent': None,
                    'trades': None,
                }

                transaction = {
                    'first_name': first_name,
                    'last_name': last_name,
                    'sale_type': sale_type,
                    'date': self.parseDate(trade.get('transaction_date', None)),
                    'filing_date': self.parseDate(rep.get('filing_date', None)),
                    'owner': trade.get('owner', None),
                    'link': rep.get('source_ptr_link', None),
                    'description': trade.get('description', None),
                    'comment': trade.get('comment', None),
                    'transaction': transactionJSON,
                }

                # Sorting amounts
                amount_range = trade.get('amount').split(' - ')
                if (len(amount_range) == 2):
                    transaction['amount_low'] = int(amount_range[0].replace('$', '').replace(',', ''))
                    transaction['amount_high'] = int(amount_range[1].replace('$', '').replace(',', ''))
                else:
                    amount_range = amount_range[0]
                    if ('+' in amount_range):
                        transaction['amount_low'] = int(amount_range.replace('$', '').replace('+', '').replace(',', ''))
                        transaction['amount_high'] = None
                    else:
                        transaction['amount_low'] = None
                        transaction['amount_high'] = int(amount_range.replace('$', '').replace('-', '').replace(',', ''))

                # Removing bad data
                transaction['ticker'] = None if (transaction['ticker'] == '--') else transaction['ticker']
                transaction['owner'] = None if (transaction['owner'] == '--') else transaction['owner']
                transaction['price_at_date'] = self.priceAtDate(transaction['ticker'], (transaction['date'] or transaction['filing_date']))

                # Generating hash for easy search/update
                transaction['hash_key'] = self.generateHash(transaction)

                congressData = congressData[:] + [congress]
                transactionData = transactionData[:] + [transaction]

        return congressData, transactionData

    def getLinkId(self, link):
        if link:
            return link.split('.pdf')[0].split('/')[-1]
        return None

    def generateHash(self, data):
        keys = [
            data['last_name'],
            (data['date'] or data['filing_date']),
            (data['ticker'] or data['description']),
            data['sale_type'],
            (data['transaction'].get('link_id', None) or 'nolink'),
            str(data['amount_low']),
            data['owner'] or 'Self',
            str(data['congress_id']),
        ]
        hashstring = ''.join(keys).replace(' ', '')
        hashkey = sha256(hashstring.encode('utf-8')).hexdigest()
        return hashkey

    def fileMap(self):
        # https://house-stock-watcher-data.s3-us-west-2.amazonaws.com/data/filemap.xml
        fmap = []
        url = f"{self.domain}/data/filemap.xml"
        try:
            response = requests.get(url, **self.settings)
        except:
            logger.error("Unexpected error:", sys.exc_info()[0])
            return None

        root = ET.fromstring(response.content)
        for child in root.iter('Key'):
            fmap.append(child.text)

        return fmap

    def tweet(self, reps, prompt=True):
        twit = Tweet()
        orders = {}

        for rep in reps:
            if (rep.ticker):
                relation = f" Owner: {rep.owner}" if (rep.owner and rep.owner != 'Self') else ''
                ticker = f"${rep.ticker}"
                saletype = rep.sale_type.replace('_', ' ').title()
                date = rep.date.strftime('%b %d')
                amount = f"${rep.amount_low} - ${rep.amount_high}" if (rep.amount_low and rep.amount_high) else f"${rep.amount_low or rep.amount_high}"

                bodyline = f"{saletype} {ticker} {amount} on {date}{relation}\n"

                if (rep.last_name not in orders):
                    orders[rep.last_name] = {
                        'headline': f"New market transaction for house rep: {rep.first_name} {rep.last_name}.\n",
                        'body': [],
                    }

                orders[rep.last_name]['body'].append(bodyline)

        for name, t in orders.items():
            headline = t['headline']
            body = ""
            for line in t['body']:
                if (len(headline + body + line) >= 280):
                    tweet = headline + body
                    twit.send(tweet, prompt=prompt)
                    body = ""
                body = (body + line)

            tweet = headline + body
            twit.send(tweet, prompt=prompt)
