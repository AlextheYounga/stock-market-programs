import os
import sys
import requests
import time
import datetime
from colored import stylize
import colored
from app.database.redisdb.rdb import Rdb
from app.functions import chunks
import django
from dotenv import load_dotenv
load_dotenv()
django.setup()
from app.database.models import Stock


# https://docs.python-requests.org/en/master/user/quickstart/#make-a-request


class IEX():
    def __init__(self):
        self.domain = 'cloud.iexapis.com'
        self.key = os.environ.get("IEX_TOKEN")
        self.sandbox_key = os.environ.get("IEX_SANDBOX_TOKEN")
        self.sandbox_domain = 'sandbox.iexapis.com'
        self.settings = {'timeout': 5}

    def endpointUrl(self, endpoint, data, domain, key, filters):
        payload = {}
        if (isinstance(data, list) and len(data) > 1):
            # For batch requests
            payload = {
                'symbols': ','.join(data),
                'token': key,
            }
            base_url = f"https://{domain}/stable/stock/market/batch"
            params = {
                'stats': {'types': 'quote,stats'},
                'quote': {'types': 'quote'},
                'price': {'types': 'quote', 'filter': 'latestPrice'},
                'company': {'types': 'quote,company'},
            }
            payload.update(params[endpoint])

            return base_url, payload

        base_url = f"https://{domain}/stable/stock/"
        urls = {
            'price': f"{base_url}{data}/quote",
            'quote': f"{base_url}{data}/quote",
            'stats': f"{base_url}{data}/stats",
            'company': f"{base_url}{data}/company",
            'advanced-stats': f"{base_url}{data}/advanced-stats",
            'financials': f"{base_url}{data}/financials",
            'cash-flow': f"{base_url}{data}/cash-flow",
            'price-target': f"{base_url}{data}/price-target",
        }
        params = {
            'price': {'filter': 'latestPrice'},
        }
        if (endpoint in params):
            payload.update(params[endpoint])

        if (filters):
            if (endpoint != 'price'):
                payload.update({'filter': filters})
            else:
                print('Cannot add filter to price endpoint.')

        return urls[endpoint], payload

    def get(self, endpoint, data, filters=[], sandbox=False):
        """
        Makes api call to IEX api

        Parameters
        ----------
        endpoint    :string
                    price | quote | stats | company | advanced-stats | financials | cash-flow | price-target
        data        :string | :list
                    Either a ticker or a list of tickers 
        filters     :string | :list
                    Filter results                    
        sandbox     :bool
                    Sets the IEX environment to sandbox mode to make limitless API calls for testing.

        Returns
        -------
        dict object from API
        """
        key = self.key
        domain = self.domain
        if (sandbox):
            domain = self.sandbox_domain
            key = self.sandbox_key

        url, payload = self.endpointUrl(endpoint, data, domain, key, filters)
        try:
            response = requests.get(url, params=payload, **self.settings).json()
        except:
            print("Unexpected error:", sys.exc_info()[0])
            return None

        if (endpoint == 'price' and ('quote' in response) and (response['quote'].get('latestPrice', False))):
            return response['quote']['latestPrice']

        return response

    def getTreasuries(self, endpoint='3m', sandbox=False):
        key = self.key
        domain = self.domain
        if (sandbox):
            domain = self.sandbox_domain
            key = self.sandbox_key

        base_url = f"https://{domain}/stable"
        urls = {
            '3m': f"{base_url}/time-series/treasury/DGS3MO",
        }

        url = f"{urls[endpoint]}"
        payload = {'token': key}

        try:
            response = requests.get(url, params=payload, **self.settings).json()
        except:
            print("Unexpected error:", sys.exc_info()[0])
            return None

        return response

    def getOptions(self, endpoint, ticker, fdate=None, sandbox=False):
        key = self.key
        domain = self.domain
        if (sandbox):
            domain = self.sandbox_domain
            key = self.sandbox_key

        base_url = f"https://{domain}/stable/stock/{ticker}/options"
        urls = {
            'chain': base_url,
            'expirations': f"{base_url}/{fdate}"
        }
        payload = {'token': key}
        url = f"{urls[endpoint]}"

        try:
            response = requests.get(url, params=payload, **self.settings).json()
        except:
            print("Unexpected error:", sys.exc_info()[0])
            return None

        return response

    def priceAtDate(self, data, date, sandbox=False):
        # https://cloud.iexapis.com/stable/stock/market/chart/date/20190109?&symbols=twtr,aapl&chartByDay=true&
        """
        Parameters
        ----------
        endpoint    :string
                    chart | earnings
        ticker      :string 
                    Either a ticker or a list of tickers 
        date        :string 
                    Date must be in %Y%m%d format                    
        sandbox     :bool
                    Sets the IEX environment to sandbox mode to make limitless API calls for testing.

        Returns
        -------
        dict object from API
        """
        # https://cloud.iexapis.com/stable/stock/AAPL/chart/date/20190520?chartByDay=true&
        key = self.key
        domain = self.domain
        if (sandbox):
            domain = self.sandbox_domain
            key = self.sandbox_key

        if (isinstance(data, list) and len(data) == 1):
            data = data.pop()

        payload = {
            'chartByDay': 'true',
            'filter': 'close,symbol',
            'token': key,
        }

        fdate = self.formatDate(date) #Format date
        url = f"https://{domain}/stable/stock/{data}/chart/date/{fdate}"

        if (isinstance(data, list)):
            url = f"https://{domain}/stable/stock/market/chart/date/{fdate}"
            payload.update({'symbols': ','.join(data)})

        time.sleep(0.5)
        try:
            response = requests.get(url, params=payload, **self.settings).json()
        except:
            print("Unexpected error:", sys.exc_info()[0])
            return {}

        if response:
            print(stylize(f"Fetching {payload.get('symbols', False) or data} price at {date}", colored.fg("yellow")))
            if (isinstance(response, list)):
                return response[0]['close']
            return response['close']
        return None



    def getChart(self, data, endpoint='chart', timeframe=None, priceOnly=False, sandbox=False):
        """
        Makes chart call to IEX api

        Parameters
        ----------
        endpoint    :string
                    chart | earnings
        data        :string | :list
                    Either a ticker or a list of tickers 
        filters     :string | :list
                    Filter results                    
        sandbox     :bool
                    Sets the IEX environment to sandbox mode to make limitless API calls for testing.

        Returns
        -------
        dict object from API
        """
        key = self.key
        domain = self.domain
        if (sandbox):
            domain = self.sandbox_domain
            key = self.sandbox_key

        payload = {'token': key}
        base_url = f"https://{domain}/stable/stock"

        urls = {
            'chart': f"{base_url}chart/batch",
            'earnings': f"{base_url}/{data}/earnings/4"
        }
        if (isinstance(data, list) and len(data) > 1):
            # Batch
            urls = {'chart': f"{base_url}chart/batch"}
            params = {
                'chart': {
                    'symbols': ','.join(data),
                    'types': 'chart',
                    'range': timeframe,
                }
            }
        else:
            # Single
            urls = {
                'chart': f"{base_url}/{data}/chart/{timeframe}",
                'earnings': f"{base_url}/{data}/earnings/4"
            }
            params = {}

        if (endpoint in params):
            payload.update(params[endpoint])
        if (priceOnly):
            payload.update({'chartCloseOnly': 'true'})

        url = urls[endpoint]

        try:
            response = requests.get(url, params=payload, **self.settings).json()
        except:
            print("Unexpected error:", sys.exc_info()[0])
            return {}

        return response

    def syncStocks(self):
        """
        Fetches all stocks from IEX 

        Returns
        -------
        object of all stocks 
        """
        payload = {'token': self.key}
        url = f"https://cloud.iexapis.com/stable/ref-data/iex/symbols"
        try:
            tickers = requests.get(url, params=payload, **self.settings).json()
        except:
            #print("Unexpected error:", sys.exc_info()[0])
            return {}

        return tickers

    def syncPrices(self):
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
        tickers = Stock.objects.all().values_list('ticker', flat=True)
        r = Rdb().setup()
        key = self.key
        domain = self.domain
        chunked_tickers = chunks(tickers, 100)

        for i, batch in enumerate(chunked_tickers):
            time.sleep(1)
            url = f"https://{domain}/stable/stock/market/batch"
            payload = {
                'symbols': ','.join(batch),
                'types': 'quote',
                'filter': 'latestPrice',
                'token': key
            }
            try:

                response = requests.get(url, params=payload, **self.settings).json()
            except:
                print("Unexpected error:", sys.exc_info()[0])
                return

            if (response):
                for ticker, data in response.items():
                    quote = data['quote']
                    if ('latestPrice' in quote):
                        price = quote['latestPrice']
                        if (price):
                            r.set('stock-' + ticker + '-price', price)
                            print(stylize("Saved " + ticker, colored.fg("green")))

    def formatDate(self, date, dateformat='%Y%m%d'):
        if (date):
            try:
                fdate = datetime.datetime.strptime(date, '%m/%d/%Y')
            except ValueError:
                try:
                    fdate = datetime.datetime.strptime(date, '%Y-%m-%d')
                except ValueError:
                    try:
                        fdate = datetime.datetime.strptime(date, '%Y/%m/%d')
                    except ValueError:
                        return None

            if (fdate and len(str(fdate.year)) == 4):
                return fdate.strftime(dateformat)
        return None
