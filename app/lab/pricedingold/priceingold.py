from dotenv import load_dotenv
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import pylab
from app.lab.core.imports import read_historical_gold_prices
import os
import sys
from app.lab.core.api.iex import IEX
load_dotenv()


class PriceInGold():
    def calculate(self, ticker, timeframe='5y', graph=True, sandbox=False):
        iex = IEX()
        asset_prices = iex.getChart(ticker, timeframe, sandbox=sandbox)
        gold_prices = read_historical_gold_prices()

        dates = []
        prices = []

        for day in asset_prices:
            price = float(day['close'] / gold_prices[day['date']]) if (day['date'] in gold_prices) else 0
            if (price == 0):
                continue
            dates.append(day['date'])
            prices.append(round(price, 3))

        x = dates
        y = prices
        
        if (graph):
            self.graph(ticker, x, y)

        return x, y
    
    def graph(self, ticker, x, y):
        # fig = plt.subplots(figsize=(12, 7))
        plt.plot(x, y, label='price/oz')
        plt.xlabel('x Date')
        plt.ylabel('y Price')
        plt.title("{} Priced in Gold".format(ticker))
        plt.xticks(np.arange(0, len(x)+1, 126))
        plt.xticks(rotation=45)

        # plt.show()
        plt.draw()
        plt.pause(1)
        input("<Hit Enter To Close>")
        plt.close()


    
