import xml.etree.ElementTree as ET
from app.lab.core.api.iex import IEX
from hashlib import sha256
import sys
from hazlitt_log import log
import datetime
import os
import json
import django
from dotenv import load_dotenv
load_dotenv()
django.setup()
from app.database.models import Congress

logger = log('HouseWatcherAPI')
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

# TODO: Remove hash key, probably useless

class House():
    def parseApiData(self, data):
        results = []
        for rep in data:
            first_name = rep.get('first_name', None)
            last_name = rep.get('last_name', None)
            name = ' '.join([first_name, last_name]).title()
            congress = Congress.objects.filter(name=name).first()
            if (not congress):
                congress, created = Congress().store({
                    'first_name': first_name,
                    'last_name': last_name,
                    'name': name,
                    'house': 'House',
                    'office': rep.get('office', None),
                    'district': rep.get('district', None),
                    'total_gain_dollars': None,
                    'total_gain_percent': None,
                    'trades': None,
                })

            for trade in rep['transactions']:
                sale_type = SALETYPES[trade['transaction_type']] if (trade.get('transaction_type', False)) else None
                transactionJSON = {'cap_gains_over_200': trade.get('cap_gains_over_200', None)}
                link = rep.get('source_ptr_link', None)
                link_id = self.getLinkId(link)
                transactionJSON.update({'link_id': link_id or None})

                transaction = {
                    'congress_id': congress.id,
                    'first_name': congress.first_name,
                    'last_name': congress.last_name,
                    'ticker': trade.get('ticker', None),
                    'sale_type': sale_type,
                    'date': self.handleDate(trade.get('transaction_date', None)),
                    'filing_date': self.handleDate(rep.get('filing_date', None)),
                    'owner': trade.get('owner', None),
                    'link': rep.get('source_ptr_link', None),
                    'description': trade.get('description', None) or trade.get('asset_description', None),
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
                transaction['price_at_date'] = iex.priceAtDate(transaction['ticker'], (transaction['date'] or transaction['filing_date']))

                # Generating hash for easy search/update
                transaction['hash_key'] = self.generateHash(transaction)

                results = results[:] + [transaction]

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
