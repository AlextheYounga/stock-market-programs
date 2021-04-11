import json
import sys
import math
import statistics
import progressbar
from scipy import stats
import pandas as pd
import numpy as np


def log_returns(prices):
    """
    Calculates daily returns of prices in list

    Parameters
    ----------
    prices    :list
                total list of prices

    Returns
    -------
    list
        List of daily returns based on list of prices. 
        *Make sure prices are ordered in descending order*
    """
    pricesdf = pd.DataFrame(prices)
    returnsdf = pricesdf[:-1].values / pricesdf[1:] - 1
    return returnsdf.iloc[:, 0].tolist()


def rollingStDev(lst, ndays=30):
    print('Calculating Rolling StDevs')
    
    stdevs = []    
    with progressbar.ProgressBar(max_value=int(len(lst)), redirect_stdout=True) as bar:
        for i, p in enumerate(lst):
            if (len(lst[i:]) < ndays):
                break

            bar.update(i)
            roll = []

            for n, r in enumerate(lst[i:]):
                if (n > ndays):
                    break
                roll.append(r)

            stdev = statistics.stdev(roll)
            stdevs.append(stdev)
    
    return stdevs
