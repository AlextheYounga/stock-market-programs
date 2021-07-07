import json
import redis
from datetime import datetime, date, timedelta
from ..core.api.historical import getHistoricalData
import sys
import os


def allowed_key(typecast, key):
    """
    A way of standardizing keys and preventing bad inserts.

    Parameters
    ----------
    key      :string
             key to be compared with array.

    Returns
    -------
    bool
    """

    if (typecast == 'stock'):
        allowed = [
            # Stocks
            'name',
            'industry',
            'employees',
            'price',
            'sector',
            'description',
            # Earnings
            'ttmEPS',
            # Financials
            'reportDate',
            'netIncome',
            'netWorth',
            'shortTermDebt',
            'longTermDebt',
            'totalCash',
            'totalDebt',
            'debtToEquity',
            'priceToSales',
            'EBITDA',
            'freeCashFlow',
            'freeCashFlowPerShare',
            'freeCashFlowYield',
            'longTermDebtToEquity',
            # Trend
            'week52',
            'day5ChangePercent',
            'month1ChangePercent',
            'ytdChangePercent',
            'day50MovingAvg',
            'day200MovingAvg',
            'avgPricetarget',
            'highPriceTarget',
            'fromPriceTarget',
            'fromHigh',
            # Valuation
            'peRatio'
        ]

    if (typecast == 'historicalprices'):
        allowed = [
            # HistoricalPrices
            'prices',
            'prices-datapoints'
        ]

    if (typecast == 'correlations'):
        # Correlations
        allowed = [
            'rvalue',
            'datapoints'
        ]

    if (key in allowed):
        return True
    else:
        return False


def rdb_save_stock(ticker, data):
    """
    Dynamically saves data to the redis db under the typecast 'stock-'.
    Refer to redisdb/schema.py to see standard schema.
    Make sure not to include ticker in the data object. Ticker should be pass separately.

    Parameters
    ----------
    ticker    :string
    data      :dict
               dict object of stock data

    Returns
    -------
    bool
    """

    r = redis.Redis(host='localhost', port=6379, db=0, charset="utf-8", decode_responses=True)
    keys = data.keys()

    for key in keys:
        if (key == ticker):
            # Prevent bad data insert
            continue
        if (allowed_key('stock', key) and data.get(key, False)):
            r.set('stock-{}-{}'.format(ticker, key), data[key])
            return True
        else:
            return False


def rdb_save_prices(ticker, prices):
    """
    Dynamically saves data to the redis db under the typecast 'stock-'.
    Refer to redisdb/schema.py to see standard schema.
    Make sure not to include ticker in the data object. Ticker should be pass separately.

    Parameters
    ----------
    ticker    :string
    data      :list
               list of dicts containing historical prices

    Returns
    -------
    bool
    """
    r = redis.Redis(host='localhost', port=6379, db=0, charset="utf-8", decode_responses=True)
    r.set('stock-'+ticker+'-prices', json.dumps(prices))
    r.set('stock-'+ticker+'-prices-datapoints', len(prices))
    return True


def update_prices(ticker):

    def calculate_range(diff):
        if (diff < 5):
            return '5d'
        if (diff < 21):
            return '1m'
        if (diff < 64):
            return '3m'
        if (diff < 126):
            return '6m'
        if (diff < 253):
            return '1y'
        if (diff < 506):
            return '2y'
        if (diff < 1260):
            return '5y'

        return 'max'

    r = redis.Redis(host='localhost', port=6379, db=0, charset="utf-8", decode_responses=True)
    prices = json.loads(r.get('stock-'+ticker+'-prices'))

    lastdate = datetime.strptime(prices[-1]['date'], '%Y-%m-%d')
    today = datetime.now()

    diff = abs((today - lastdate).days)

    if (diff <= 3):
        return

    latest_prices = getHistoricalData(ticker, calculate_range(diff), priceOnly=True)

    for i, day in enumerate(list(reversed(latest_prices))):
        prices.append(day)
        if (day['date'] == prices[-1]['date']):
            break

    rdb_save_prices(ticker, prices)


def rdb_save_output(output):
    r = redis.Redis(host='localhost', port=6379, db=0, charset="utf-8", decode_responses=True)
    r.set('lab-last-output', json.dumps(output))
    return True


def fetch_last_output():
    r = redis.Redis(host='localhost', port=6379, db=0, charset="utf-8", decode_responses=True)
    op = r.get('lab-last-output')
    if (op):
        return json.loads(op)

    return False
