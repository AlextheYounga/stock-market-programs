from iexfinance.stocks import Stock, get_historical_data
from datetime import datetime, time, timedelta
from dotenv import load_dotenv
import colored
from colored import stylize
import requests
import sys
import json
import os
load_dotenv()

class IEX():
    def __init__(self, endpoint, batch=False):
        self.endpoint = endpoint
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
            '3mUST':f"{base_url}/time-series/treasury/DGS3MO",
            'price-target': f"{base_url}/stock/{data}/price-target",
            'options:expirations': f"https://{domain}/stable/stock/{data}/options",
        }

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
