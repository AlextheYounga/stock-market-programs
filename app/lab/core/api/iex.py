from iexfinance.stocks import Stock, get_historical_data
from datetime import time
from app.functions import chunks
from dotenv import load_dotenv
import redis
import colored
from colored import stylize
import requests
import sys
import json
import os
from django.apps import apps
load_dotenv()

class IEX():
    def __init__(self, endpoint, filters=[], batch=False):
        self.endpoint = endpoint
        self.filters = []
        self.batch = batch #'single', 'batch'
        self.domain = 'cloud.iexapis.com'
        self.key = os.environ.get("IEX_TOKEN")
        self.sandbox_key = os.environ.get("IEX_SANDBOX_TOKEN")
        self.sandbox_domain = 'sandbox.iexapis.com'

    def endpointUrl(self, domain, data, key):
        endpoint = self.endpoint        
        if (self.batch):
            base_url = f"https://{domain}/stable/stock/market/batch?symbols={data}&types="            
            urls = {
                'stats': f"{base_url}quote,stats",
                'quote': f"{base_url}quote",
                'price': f"{base_url}quote&filter=latestPrice",
                'company': f"{base_url}quote,company",
            }
            return f"{urls[endpoint]}&token={key}"

        base_url=f"https://{domain}/stable"
        urls = {                  
            'stats': f"{base_url}/stock/{data}/stats",    
            'advanced-stats': f"{base_url}/stock/{data}/advanced-stats",
            'financials': f"{base_url}/stock/{data}/financials",
            'cash-flow': f"{base_url}/stock/{data}/cash-flow",
            '3mUST': f"{base_url}/time-series/treasury/DGS3MO",
            'price-target': f"{base_url}/stock/{data}/price-target",
            'options:expirations': f"{base_url}/stock/{data}/options",
        }
        if (self.filters):
            filterResults = ",".join(self.filters) if (len(self.filters) > 1) else self.filters[0]
            return f"{urls[endpoint]}?filter={filterResults}&token={key}"

        return f"{urls[endpoint]}?token={key}"
    
    def request(self, data, sandbox=False):
        """
        Makes api call to IEX api

        Parameters
        ----------
        data        :string | :list
                    Either a ticker or a list of tickers if batch == True
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
            # Convert to comma-separated string
            batch = ",".join(data) if (self.batch) else False 
            url = self.endpointUrl(domain, (data or batch), key)
        try:
            response = requests.get(url).json()
        except:
            print("Unexpected error:", sys.exc_info()[0])
            return None

        return response
    
    def requestOptions(self, ticker, fdate=None, sandbox=False):
        key = self.key
        domain = self.domain
        if (sandbox):
            domain = self.sandbox_domain
            key = self.sandbox_key
        base_url=f"https://{domain}/stable" 
        urls = {                                   
            'chain': f"{base_url}/stock/{ticker}/options/{fdate}?token={key}",
            'expirations': f"{base_url}/stock/{ticker}/options",
        }
        url = urls[self.endpoint]

        try:
            response = requests.get(url).json()
        except:
            print("Unexpected error:", sys.exc_info()[0])
            return None

        return response

    def requestHistorical(self, data, timeframe, priceOnly=False, sandbox=False):
        key = self.key
        endpoint = self.endpoint
        if (sandbox):
            domain = self.sandbox_domain
            key = self.sandbox_key

        if (endpoint == 'chart'):
            batch = ",".join(data) if (self.batch) else False 
            base_url = f"https://{domain}/stable/stock/chart/batch?symbols={(data or batch)}&types=chart&range={timeframe}"     
            if (priceOnly):
                base_url = f"{base_url}&chartCloseOnly=true"
            url = f"{base_url}&token={key}"

        if (endpoint == 'earnings'):
            base_url = f"https://{domain}/stable/stock/{data}/earnings/4/"
            url = f"{base_url}?token={key}"

        try:
            historicalRequest = requests.get(url).json()
        except:
            print("Unexpected error:", sys.exc_info()[0])
            return {}

        return historicalRequest

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
                print("Unexpected error:", sys.exc_info()[0])
                return

            if (batch_request):
                for ticker, data in batch_request.items():                
                    quote = data['quote']
                    if ('latestPrice' in quote):
                        price = quote['latestPrice']
                        if (price):
                            r.set('stock-'+ticker+'-price', price)
                            print(stylize("Saved "+ticker, colored.fg("green")))