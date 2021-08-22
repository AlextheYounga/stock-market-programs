import xml.etree.ElementTree as ET
from app.lab.core.output import printFullTable, printTable
from app.lab.scrape.scraper import Scraper
import requests
import datetime
import time
import sys
import json
import os
from logs.hazlittlog import log
import django
django.setup()

logger = log('SenateWatcherAPI')
scraper = Scraper()

class SenateWatcher():

    def __init__(self):
        self.domain = 'https://senate-stock-watcher-data.s3-us-west-2.amazonaws.com'
        self.settings = {'timeout': 5}

    def getLatest(self, save=True):
        latest = self.lastReport()
        results = self.parseData(latest)
        from app.database.models import Senate
        for result in results:
            senate, created = Senate().store(result)
            if (created):
                print(f"Created new record for {result['first_name']} {result['last_name']}")

    def lastReport(self, print_results=False):
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
        from app.database.models import Senate
        for f in files:
            url = f"{self.domain}/{f}"
            print(url)

            time.sleep(1) # Slow is smooth and smooth is fast.
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
                        "asset_description": "W.L. Gore &amp; Associates, Inc. <div class=\"text-muted\"> <em>Company:</em> W.L. Gore &amp; Associates, Inc. &nbsp;(Newark, DE) </div> <div class=\"text-muted\"><em>Description:</em>&nbsp;Advanced materials manufacturing</div>",
                        "asset_type": "Non-Public Stock",
                        "comment": "--"
                    }
                }
                for k, v in tinfo.items():
                    if (v == '--'):
                        tinfo[k] = None
                    if ('<a' in v):
                        html = scraper.parseHTML(v)
                        tinfo[k] = html.text
                
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