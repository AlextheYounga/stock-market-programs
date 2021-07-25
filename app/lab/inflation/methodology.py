from dotenv import load_dotenv
import pandas as pd
import numpy as np
import redis
import statistics
import progressbar
import json
import sys
from datetime import date
from ..redisdb.controller import update_prices
from app.functions import chunks
from app.lab.core.api.gold import syncGoldPrices
from app.lab.core.api.batch import quoteStatsBatchRequest
from app.lab.core.output import printFullTable, writeCSV
load_dotenv()

# TODO: Needs work fam

def sectors():
    return [
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


def trim_data(data):
    trimmed = {}
    COUNT = len(sectors())
    for date, prices in data.items():
        if (len(prices) != COUNT):
            continue
        trimmed[date] = prices

    return trimmed


def formula(data):
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


def calculate(update):
    r = redis.Redis(host='localhost', port=6379, db=0, charset="utf-8", decode_responses=True)
    data = {}

    for ticker in progressbar.progressbar(sectors(), prefix='Calculating: '):
        if (update):
            update_prices(ticker)

        prices = json.loads(r.get('stock-'+ticker+'-prices'))

        if (prices):

            for row in prices:
                if (row['date'] not in data):
                    data[row['date']] = []

                data[row['date']].append(float(row['close']))

    data = trim_data(data)

    return formula(data) if (data) else "Unexpected Error"
