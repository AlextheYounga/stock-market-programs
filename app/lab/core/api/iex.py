from datetime import time

from iexfinance.stocks import base
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
    def __init__(self):
        self.domain = 'cloud.iexapis.com'
        self.key = os.environ.get("IEX_TOKEN")
        self.sandbox_key = os.environ.get("IEX_SANDBOX_TOKEN")
        self.sandbox_domain = 'sandbox.iexapis.com'

    def endpointUrl(self, endpoint, data, domain, key, filters, batch):    
        if (batch):
            base_url = f"https://{domain}/stable/stock/market/batch?symbols={data}&types="            
            urls = {
                'stats': f"{base_url}quote,stats",
                'quote': f"{base_url}quote",
                'price': f"{base_url}quote&filter=latestPrice",
                'company': f"{base_url}quote,company",
            }
            return f"{urls[endpoint]}&token={key}"

        base_url=f"https://{domain}/stable/stock/"
        urls = {  
            'price': f"{base_url}{data}/quote?filter=latestPrice",
            'quote': f"{base_url}{data}/quote",         
            'stats': f"{base_url}{data}/stats",    
            'advanced-stats': f"{base_url}{data}/advanced-stats",
            'financials': f"{base_url}{data}/financials",
            'cash-flow': f"{base_url}{data}/cash-flow",            
            'price-target': f"{base_url}{data}/price-target",
        }
        if (filters):
            if (endpoint != 'price'):
                filterResults = ",".join(filters) if (len(filters) > 1) else filters[0]
                return f"{urls[endpoint]}?filter={filterResults}"
            else: 
                print('Cannot add filter to price endpoint.')
                
        sep = '?' if ('?' not in urls[endpoint]) else '&'
        return f"{urls[endpoint]}{sep}token={key}"
    
    def get(self, endpoint, data, filters=[], batch=False, sandbox=False):
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

        batch = ",".join(data) if (batch) else False # Convert to comma-separated string
        url = self.endpointUrl(endpoint, (data or batch), domain, key, filters, batch)
        try:
            response = requests.get(url).json()
        except:
            print("Unexpected error:", sys.exc_info()[0])
            return None

        if (endpoint == 'price' and batch == False):
            return response['latestPrice']
        return response
    
    def getTreasuries(self, endpoint='3m', sandbox=False):        
        key = self.key
        domain = self.domain
        if (sandbox):
            domain = self.sandbox_domain
            key = self.sandbox_key

        base_url=f"https://{domain}/stable"
        urls= {
            '3m': f"{base_url}/time-series/treasury/DGS3MO",
        }

        url = f"{urls[endpoint]}?token={key}"
        try:
            response = requests.get(url).json()
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

        base_url=f"https://{domain}/stable/stock/" 
        urls = {                                   
            'chain': f"{base_url}{ticker}/options/{fdate}",
            'expirations': f"{base_url}{ticker}/options",
        }
        url = f"{urls[endpoint]}?token={key}"

        try:
            response = requests.get(url).json()
        except:
            print("Unexpected error:", sys.exc_info()[0])
            return None

        return response

    def getHistorical(self, endpoint, data, timeframe=None, priceOnly=False, batch=False, sandbox=False):
        key = self.key
        if (sandbox):
            domain = self.sandbox_domain
            key = self.sandbox_key
        
        base_url = f"https://{domain}/stable/stock/"
        urls = {
            'chart': f"{base_url}chart/batch?symbols={(data or batch)}&types=chart&range={timeframe}",
            'earnings': f"{data}/earnings/4/"
        }

        batch = ",".join(data) if (batch) else False 
       
        if (priceOnly):
            url = f"{urls[endpoint]}&chartCloseOnly=true&token={key}"
        else:        
            url = f"{urls[endpoint]}&token={key}" 

        try:
            historicalRequest = requests.get(url).json()
        except:
            print("Unexpected error:", sys.exc_info()[0])
            return {}

        return historicalRequest


    def syncStocks(self):
        """
        Fetches all stocks from IEX 

        Returns
        -------
        object of all stocks 
        """
        try:
            url = f"https://cloud.iexapis.com/stable/ref-data/iex/symbols?token={self.key}"
            tickers = requests.get(url).json()
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
        Stock = apps.get_model('database', 'Stock')
        tickers = Stock.objects.all().values_list('ticker', flat=True)
        r = redis.Redis(host='localhost', port=6379, db=0, charset="utf-8", decode_responses=True)
        key = self.key
        domain = self.domain
        chunked_tickers = chunks(tickers, 100)

        for i, batch in enumerate(chunked_tickers):
            time.sleep(1)
            try:
                batch = ",".join(batch)  # Convert to comma-separated string
                url = f"https://{domain}/stable/stock/market/batch?symbols={batch}&types=quote&filter=latestPrice&token={key}"
                
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