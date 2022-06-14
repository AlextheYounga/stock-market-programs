from app.lab.core.output import printFullTable, printTable
from app.functions import compare_dicts, get_hazlitt_path, writeTxtFile, readJSONFile, compare_dicts
from app.lab.fintwit.tweet import Tweet
import pytz
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
STORAGE = {
    'balance-sheet': f"{get_hazlitt_path()}/app/lab/fed/storage/balancesheet.json"
}

class FedBalanceSheet():
    def __init__(self):
        self.domain = 'https://api.stlouisfed.org/fred'
        self.key = os.environ.get("FRED_API_KEY")
        self.settings = {'timeout': 5}
    
    def checkLatest(self, endpoint, tweet=False):
        series = self.series(endpoint)
        fseries = self.format_data(series)
        storageJSON = readJSONFile(STORAGE[endpoint])
        diff = compare_dicts(storageJSON, fseries)
        print(diff)
        if (diff):
            if (len(diff) > 1):
                diff = diff[list(diff.keys())[-1]]
            
            lastK = list(reversed(list(storageJSON)))[0]        
            last = storageJSON[lastK]     

            if (tweet):
                self.new_value_tweet(last, diff[list(diff.keys())[0]])


    def series(self, endpoint, timeframe=None):        
        payload = {
            'series_id': CODES[endpoint],
            'file_type': 'json',            
            'api_key': self.key,
        }
        start_date, end_date = self.buildTimeFrame(timeframe)
        if (start_date and end_date):
            payload.update({
                'realtime_start': start_date,
                'realtime_end': end_date,
            })

        url = f"{self.domain}/series/observations"
        data = self.send(url, payload)
        return data


    def buildTimeFrame(self, timeframe):
        if (timeframe):
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
        return None, None

    def send(self, url, payload):
        try:
            response = requests.get(url, params=payload, **self.settings).json()
        except:
            print("Unexpected error:", sys.exc_info()[0])
            return None

        return response
    
    def format_data(self, series):
        databuild = {}
        if series.get('observations', False):
            for row in series['observations']:                   
                databuild[row['date']] = {
                    'date': row['date'],
                    'value': row['value']
                }                
        return databuild


    def store(self, endpoint, series):
            data = self.format_data(series)
            writeTxtFile(STORAGE[endpoint], data)

    def format_number(self, num):
        total = int(float(num)) * 1000000
        return "{:,}".format(total)
        

    def new_value_tweet(self, last, new, prompt=True):        
        def preposition(number):
            if (number < 0):
                return 'Down'
            else:
                return 'Up'

        twit = Tweet()
        print(new)
        print(new['date'])
        newdate = datetime.datetime.strptime(new['date'], '%Y-%m-%d').strftime('%b %d')
        lastdate = datetime.datetime.strptime(last['date'], '%Y-%m-%d').strftime('%b %d')
        diff = str(int(float(new['value']) - float(last['value'])))
        headline = f"LATEST FED BALANCE SHEET NUMBER {newdate}:"
        value = self.format_number(new['value'])
        body = f"{preposition(int(diff))} {self.format_number(diff)} compared to last number on {lastdate}"
        tweet_data = [
            headline,
            value,
            body
        ]

        tweet = "\n".join(tweet_data)
        twit.send(tweet, prompt=prompt)
        



