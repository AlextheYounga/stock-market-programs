import matplotlib.pyplot as plt
from app.lab.core.api.iex import IEX
from app.functions import chunks, extract_data
from .functions import *


def calculateVol(ticker, ndays=30):
    iex = IEX()
    asset_data = iex.getChart(ticker, timeframe='5y', priceOnly=True)
    prices = list(reversed(extract_data(asset_data, 'close')))
    lreturns = log_returns(prices)
    stdevs = rollingStDev(lreturns)

    vol = []
    for sd in stdevs:
        v = math.sqrt(252) * sd
        vol.append(v)

    dates = list(reversed(extract_data(asset_data, 'date')))[:len(vol)]

    print("\n")
    print("Lifetime Vol: {}".format(statistics.mean(vol)))
    print("3y Vol: {}".format(statistics.mean(vol[:756])))
    print("2y Vol: {}".format(statistics.mean(vol[:504])))
    print("1y Vol: {}".format(statistics.mean(vol[:252])))
    print("3m Vol: {}".format(statistics.mean(vol[:64])))
    print("1m Vol: {}".format(statistics.mean(vol[:30])))
    print("\n")

    return [dates, vol]


def graphVol(ticker, ndays=30):
    graph_data = calculateVol(ticker, ndays=30)
    fig = plt.subplots(figsize=(12, 7))

    x = graph_data[0]
    y = graph_data[1]

    plt.plot(x, y, label='Value')
    plt.xlabel('x Date')
    plt.title(ticker+" Volatility")
    plt.xticks(np.arange(0, len(x)+1, 126))
    plt.xticks(rotation=45)

    plt.draw()
    plt.pause(1)
    input("<Hit Enter To Close>")    
    plt.close()

    
