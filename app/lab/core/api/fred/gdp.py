from app.lab.core.output import printFullTable, printTable
from app.functions import compare_dicts, get_app_path, writeTxtFile, readJSONFile, compare_dicts
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
    'balance-sheet': f"{get_app_path()}/app/lab/fed/storage/balancesheet.json"
}

class GDP():
    def __init__(self):
        self.domain = 'https://api.stlouisfed.org/fred'
        self.key = os.environ.get("FRED_API_KEY")
        self.settings = {'timeout': 5}
    
    def new_value_tweet(self, last, new, prompt=True):        
        def preposition(number):
            if (number < 0):
                return 'Down'
            else:
                return 'Up'

        twit = Tweet()
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
        



