from dotenv import load_dotenv
import json
import sys
from .methodology import calculate
from datetime import datetime
from lab.core.output import printTabs
import statistics
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib import pylab
import numpy as np
load_dotenv()


def annual(update=False):
    index = calculate(update)
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

    print("\n")
    printTabs(annualDelta)
    print("\n")
    print('Total Average: '+str(avg)+'%')
    print("\n")


def graph(update=False):
    index = calculate(update)

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
