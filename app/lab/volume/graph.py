from dotenv import load_dotenv
import json
import sys
import redis
import time
from datetime import date
from ..redisdb.controller import rdb_save_stock
from ..core.functions import extract_data
from ..core.api.historical import getHistoricalData
from ..core.output import printFullTable, writeCSV
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib import pylab
import numpy as np
load_dotenv()

def graph_volume(ticker, timeframe='3m', sandbox=False):
    hdata = getHistoricalData(ticker, timeframe=timeframe, priceOnly=True, sandbox=sandbox)
    prices = extract_data(hdata, 'close')
    volumes = []
    for hd in hdata:
        volumes.append(hd['volume'] / 1000)

    dates = extract_data(hdata, 'date')

    fig = plt.subplots(figsize=(12, 7))

    x = dates
    y = volumes

    plt.plot(x, y, label='Volume')
    plt.xlabel('x Date')
    plt.title(ticker+" Volume")
    plt.xticks(np.arange(0, len(x)+1, int(len(x) / 10)))
    plt.xticks(rotation=45)

    plt.draw()
    plt.pause(1)
    input("<Hit Enter To Close>")    
    plt.close()