import django
from iexfinance.stocks import Stock
from ...core.api.batch import batchQuote
from ...core.api.sync import syncStocks
from ...core.functions import chunks
from django.apps import apps
import json
import sys
import os
django.setup()


Stock = apps.get_model('database', 'Stock')

stocks = syncStocks()
tickers = [stock['symbol'] for stock in stocks]
chunked_tickers = chunks(tickers, 100)

for i, chunk in enumerate(chunked_tickers):
    batch = batchQuote(chunk)

    for i, info in batch.items():
        quote = info['quote'] if ('quote' in info) and info['quote'] else False
        # company = info['company'] if ('quote' in info) and info['company'] else False

        if (quote):
            if (quote.get('companyName', False)):
                Stock.objects.update_or_create(
                    ticker=quote['symbol'],
                    defaults={
                        'name': quote.get('companyName'),
                    }
                )
                print('saved {}'.format(quote['symbol']))
