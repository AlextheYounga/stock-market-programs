from app.lab.scrape.scraper import Scraper
from app.lab.core.api.iex import IEX
from app.database.redisdb.rdb import Rdb
from app.lab.core.output import printFullTable
from app.lab.fintwit.tweet import Tweet
import xml.etree.ElementTree as ET
from app.functions import filterNone
from hashlib import sha256
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
from app.database.models import Congress

logger = log('HouseWatcherAPI')
scraper = Scraper()
iex = IEX()
r = Rdb().setup()


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
        return rep

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
            if (r.get(f"housewatch-api-{f}")):
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
            r.set(f"housewatch-api-{f}", 1)

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
        results = []
        for rep in data:
            for transaction in rep['transactions']:
                tdata = {
                    'first_name': rep.get('first_name', None),
                    'last_name': rep.get('last_name', None),
                    'ticker': transaction.get('ticker', None),
                    'house': 'House',
                    'office': rep.get('office', None),
                    'link': rep.get('source_ptr_link', None),
                    'district': rep.get('district', None),
                    'date': self.parseDate(transaction.get('transaction_date', None)),
                    'filing_date': self.parseDate(rep.get('filing_date', None)),
                    'owner': transaction.get('owner', None),
                    'sale_type': transaction.get('transaction_type', None),
                    'transaction': {
                        "asset_description": transaction.get('description', None),
                        "cap_gains_over_200": transaction.get('cap_gains_over_200', None),
                    }
                }
                
                amount_range = transaction.get('amount').split(' - ')
                if (len(amount_range) == 2):
                    tdata['amount_low'] = int(amount_range[0].replace('$', '').replace(',', ''))
                    tdata['amount_high'] = int(amount_range[1].replace('$', '').replace(',', ''))                
                else:
                    amount_range = amount_range[0]
                    if ('+' in amount_range):
                        tdata['amount_low'] = int(amount_range.replace('$', '').replace('+', '').replace(',', ''))
                        tdata['amount_high'] = None
                    else:
                        tdata['amount_low'] = None
                        tdata['amount_high'] = int(amount_range.replace('$', '').replace('-', '').replace(',', ''))

                tdata['hash_key'] = self.generateHash(tdata)

                results = results[:] + [tdata]

        return results

    def generateHash(self, data):
        keys = [
            data['last_name'],
            (data['date'] or data['filing_date']),
            data['house'],
            (data['ticker'] or data['transaction']['asset_description']),
            data['owner'] or 'None',
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

    def tweet(self, houseObj, prompt=True):
        twit = Tweet()
        ticker = houseObj.ticker if houseObj.ticker else houseObj.transaction.get('asset_description', False)
        if (ticker):
            headline = f"New market transaction for house rep: {houseObj.first_name} {houseObj.last_name}."
            relation = f"Relation: {houseObj.owner}" if (houseObj.owner != 'Self') else None
            saletype = houseObj.sale_type
            amount = f"${houseObj.amount_low} - ${houseObj.amount_high}"
            date = houseObj.date
            transaction = f"{saletype} ${ticker} {amount} on {date}"
            c = houseObj.transaction.get('comment', False)
            comment = f"Comment: {c}" if (c and (c not in ['--', 'R']) and (len(c) > 2)) else None

            tweet_data = filterNone([
                headline,
                relation,
                transaction,
                comment
            ])
            tweet = "\n".join(tweet_data)
            twit.send(tweet, prompt=prompt)
