from app.lab.scrape.scraper import Scraper
import html
from app.lab.core.api.iex import IEX
import xml.etree.ElementTree as ET
from hashlib import sha256
import re
import datetime
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


class Senate():
    def parseApiData(self, data):
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
                    'date': self.handleDate(trade.get('transaction_date', None)),
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

                    obj['price_at_date'] = iex.priceAtDate(obj['ticker'], obj['date'])
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

    def handleDate(self, date):
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
