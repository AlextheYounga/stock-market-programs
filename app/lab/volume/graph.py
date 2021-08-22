from dotenv import load_dotenv
import json
import sys
import redis
import time
from datetime import date
from app.functions import extract_data
from app.lab.core.api.iex import IEX
import matplotlib.pyplot as plt
import numpy as np
load_dotenv()

def graph_volume(ticker, timeframe='3m', sandbox=False):
    iex = IEX()
    hdata = iex.getChart(ticker, timeframe=timeframe, priceOnly=True, sandbox=sandbox)
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