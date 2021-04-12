import django
from django.apps import apps
from dotenv import load_dotenv
from ..functions import chunks
import colored
from colored import stylize
import requests
import redis
import sys
import time
import json
import os
load_dotenv()
django.setup()

def syncStocks():
    """
    Fetches all stocks from IEX 

    Returns
    -------
    object of all stocks 
    """
    try:
        url = 'https://cloud.iexapis.com/stable/ref-data/iex/symbols?token={}'.format(os.environ.get("IEX_TOKEN"))
        tickers = requests.get(url).json()
    except:
        #print("Unexpected error:", sys.exc_info()[0])
        return {}

    return tickers


def syncPrices():
    """
    Fetches company info for a batch of tickers. Max 100 tickers

    Parameters
    ----------
    batch       :list
                list of max 100 tickers
    sandbox     :bool
                Sets the IEX environment to sandbox mode to make limitless API calls for testing.

    Returns
    -------
    dict object of company info for 100 tickers
    """
    Stock = apps.get_model('database', 'Stock')
    tickers = Stock.objects.all().values_list('ticker', flat=True)
    r = redis.Redis(host='localhost', port=6379, db=0, charset="utf-8", decode_responses=True)
    domain = 'cloud.iexapis.com'
    key = os.environ.get("IEX_TOKEN")
    chunked_tickers = chunks(tickers, 100)

    for i, batch in enumerate(chunked_tickers):
        time.sleep(1)
        try:
            batch = ",".join(batch)  # Convert to comma-separated string
            url = 'https://{}/stable/stock/market/batch?symbols={}&types=quote&filter=latestPrice&token={}'.format(
                domain,
                batch,
                key
            )
            
            batch_request = requests.get(url).json()
        except:
            #print("Unexpected error:", sys.exc_info()[0])
            return

        if (batch_request):
            for ticker, data in batch_request.items():                
                quote = data['quote']
                if ('latestPrice' in quote):
                    price = quote['latestPrice']
                    if (price):
                        r.set('stock-'+ticker+'-price', price)
                        print(stylize("Saved "+ticker, colored.fg("green")))
