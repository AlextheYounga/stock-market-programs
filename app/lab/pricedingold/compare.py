from dotenv import load_dotenv
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import pylab
from ..core.imports import read_historical_gold_prices
from ..core.functions import extract_data
import os
import sys
from ..core.api.historical import getHistoricalData
load_dotenv()


def price_in_gold(ticker, timeframe='5y', sandbox=False):
    if (sandbox):
        asset_prices = getHistoricalData(ticker, timeframe, sandbox=True)
    else:
        asset_prices = getHistoricalData(ticker, timeframe)

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

    fig = plt.subplots(figsize=(12, 7))

    plt.plot(x, prices, label='price/oz')
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
