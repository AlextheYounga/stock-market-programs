import json
import sys
from app.functions import extract_data
from app.lab.core.api.historical import getHistoricalData
from app.lab.core.api.stats import getCurrentPrice
from app.lab.core.output import printTabs
from app.lab.fintwit.fintwit import Fintwit
import os
from datetime import datetime
import csv

class Donchian():
    
    def calculate(self, ticker, days=30, sendtweet=False):
        asset_data = getHistoricalData(ticker, '1m')
        highs = extract_data(asset_data, 'high')
        lows = extract_data(asset_data, 'low')

        donchian_range = {
            'donchianHigh': max(list(reversed(highs))[:days]),
            'currentPrice': getCurrentPrice(ticker),
            'donchianLow': min(list(reversed(lows))[:days])
        }

        printTabs(donchian_range)

        if (sendtweet):
            self.tweet(ticker, donchian_range)


    def tweet(self, ticker, donchian_range):
        twit = Fintwit()
        headline = "${} 3week Donchian Range:".format(ticker)
        tweet = headline + twit.translate_data(donchian_range)
        twit.send_tweet(tweet)
    
    def export(self, donchian_range, ticker):
        output_file = 'app/lab/donchian/output/donchianrange.csv'

        # If output file does not exist, create new.
        if (not os.path.exists(output_file)):
            with open(output_file, mode='w') as resultsfile:
                self.writeCSV(donchian_range, ticker, resultsfile, append=False)

        # If file already exists, append to file
        else:
            with open(output_file, mode='a') as resultsfile:
                write_results = csv.writer(resultsfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                self.writeCSV(donchian_range, ticker, resultsfile, append=True)
    

    def writeCSV(self, donchian_range, ticker, resultsfile, append):
        
        now = datetime.now()
        datenow = now.strftime("%m-%d-%Y %H:%M:%S")
        write_results = csv.writer(resultsfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        if (append == True):
            for x in range(2):
                write_results.writerow([''])

        write_results.writerow(['{} Range Generated {}'.format(ticker, datenow)])
        headers = list(donchian_range.keys())
        data = list(donchian_range.values())

        write_results.writerow(headers)
        write_results.writerow(data)


    

