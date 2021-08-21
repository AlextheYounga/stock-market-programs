from app.lab.core.output import printFullTable, printTable
import datetime
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
        start_date, end_date = self.buildTimeFrame(timeframe)
        payload = {
            'series_id': CODES[endpoint],
            'file_type': 'json',
            'realtime_start': start_date,
            'realtime_end': end_date,
            'api_key': self.key,
        }

        url = f"{self.domain}/series/observations"
        data = self.send(url, payload)
        return data

    def buildTimeFrame(self, timeframe):
        today = datetime.datetime.today()
        frames = {
            '1w': ((today - datetime.timedelta(weeks=1)).strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d')),
            '3w': ((today - datetime.timedelta(weeks=3)).strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d')),
            '1m': ((today - datetime.timedelta(days=30)).strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d')),
            '3m': ((today - datetime.timedelta(days=90)).strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d')),
            '6m': ((today - datetime.timedelta(days=180)).strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d')),
            '1y': ((today - datetime.timedelta(days=365)).strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d')),
            '3y': ((today - datetime.timedelta(days=1095)).strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d')),
            '5y': ((today - datetime.timedelta(days=1825)).strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d')),
            '10y': ((today - datetime.timedelta(days=3650)).strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d')),
        }
        return frames[timeframe]

    def send(self, url, payload):
        try:
            response = requests.get(url, params=payload, **self.settings).json()
        except:
            print("Unexpected error:", sys.exc_info()[0])
            return None

        return response
