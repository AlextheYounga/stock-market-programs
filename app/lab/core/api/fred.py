from app.lab.core.output import printFullTable, printTable
import requests
import sys
import json
import os
from dotenv import load_dotenv
load_dotenv()

CODES = {
    'balance-sheet': 'WALCL',
}

class Fred():    
    def __init__(self):
        self.domain = 'https://api.stlouisfed.org/fred'
        self.key = os.environ.get("FRED_API_KEY")
        self.settings = {'timeout': 5}
    

    def series(self, endpoint, timeframe='1m'):
        payload = {
            'series_id': CODES[endpoint],
            'api_key': self.key,
            'file_type': 'json'
        }

        url = f"{self.domain}/series"
        data = self.send(url, payload)
        return data
    
    def send(self, url, payload):
        try:
            response = requests.get(url, params=payload, **self.settings).json()            
        except:
            print("Unexpected error:", sys.exc_info()[0])
            return None
        
        return response



f = Fred()
print(json.dumps(f.updates('balance-sheet'), indent=1))