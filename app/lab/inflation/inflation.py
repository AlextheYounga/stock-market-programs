from dotenv import load_dotenv
import matplotlib.pyplot as plt
import numpy as np
import redis
import statistics
import progressbar
import json
import sys
from datetime import datetime
from app.functions import chunks
from lab.core.output import printTabs
from app.lab.core.api.gold import syncGoldPrices
load_dotenv()

SECTORS = [
        'XLY',
        'XLP',
        'XLE',
        'XLF',
        'XLV',
        'XLI',
        'XLB',
        'XLK',
        'IXP',
        'USRT',
        'XLU',
        'XME',
        'VNQ',
        'AMLP',
        'ITB',
        'OIH',
        'KRE',
        'XRT',
        'MOO',
        'FDN',
        'IBB',
        'SMH',
        'XOP',
        'PBW',
        'KIE',
        'PHO',
        'IGV'
        # 'XLC',
        # 'IYR',
        # 'XLRE',
    ]
class Inflation():
    def formula(self, data):
        """
        Take an average of each etf sector and divide that avg by the price of gold.
        Gold is used as the denominator here due to its relative stability throughout history, 
        though I certainly understand it's not perfect. The results are quite astounding.
        Theoretically, this should represent 'real' US asset inflation over the last 10 years.
        """
        avgs = {}
        index = {}
        r = redis.Redis(host='localhost', port=6379, db=0, charset="utf-8", decode_responses=True)

        for day, prices in data.items():
            avg = statistics.mean(prices)
            avgs[day] = avg
        
        syncGoldPrices()

        with progressbar.ProgressBar(max_value=len(list(avgs)), prefix='Indexing: ', redirect_stdout=True) as bar:
            i = 0
            for day, a in avgs.items():
                i += 1
                bar.update(i)
                gold_price = r.get('gold-'+day+'-close')        
                if (gold_price):
                    price = round(float(gold_price) / float(a), 3)
                    index[day] = price

        return index


    def calculate(self, update):
        r = redis.Redis(host='localhost', port=6379, db=0, charset="utf-8", decode_responses=True)
        data = {}

        for ticker in progressbar.progressbar(SECTORS, prefix='Calculating: '):
            if (update):
                update_prices(ticker)

            prices = json.loads(r.get('stock-'+ticker+'-prices'))

            if (prices):

                for row in prices:
                    if (row['date'] not in data):
                        data[row['date']] = []

                    data[row['date']].append(float(row['close']))

        data = self.trim_data(data)

        return self.formula(data) if (data) else "Unexpected Error"

    def annual(self, update=False):
        index = self.calculate(update)
        annualPrices = {}
        annualDelta = {}

        for day, price in index.items():
            year = datetime.strptime(day, '%Y-%m-%d').year

            if (year not in annualPrices):
                annualPrices[year] = []

            annualPrices[year].append(price)

        for yr, prices in annualPrices.items():
            annualDelta[yr] = ((prices[-1] - prices[0]) / prices[0] * 100)

        avg = round(statistics.mean(annualDelta.values()), 3)


        printTabs(annualDelta)
        print('Total Average: '+str(avg)+'%')
        return annualDelta
    
    def graph(self, update=False):
        index = self.calculate(update)

        x = index.keys()
        y = index.values()

        fig = plt.subplots(figsize=(12, 7))

        plt.plot(x, y, label='Index Value')
        plt.xlabel('x Date')
        plt.ylabel('y Value')
        plt.title("Inflation Index")
        plt.xticks(np.arange(0, len(x)+1, 126))
        plt.xticks(rotation=45)

        # plt.show()
        plt.draw()
        plt.pause(1)
        input("<Hit Enter To Close>")
        plt.close()

    def trim_data(self, data):
        trimmed = {}
        COUNT = len(SECTORS)
        for date, prices in data.items():
            if (len(prices) != COUNT):
                continue
            trimmed[date] = prices

        return trimmed
