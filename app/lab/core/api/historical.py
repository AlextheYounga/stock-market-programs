from datetime import datetime, time, timedelta
from dotenv import load_dotenv
import requests
import sys
import json
import os
load_dotenv()


def getHistoricalData(ticker, timeframe, priceOnly=False, sandbox=False):
    domain = 'cloud.iexapis.com'
    key = os.environ.get("IEX_TOKEN")
    if (sandbox):
        domain = 'sandbox.iexapis.com'
        key = os.environ.get("IEX_SANDBOX_TOKEN")
    try:
        url = 'https://{}/stable/stock/{}/chart/{}?token={}'.format(
            domain,
            ticker,
            timeframe,
            key
        )
        if (priceOnly):
            url = 'https://{}/stable/stock/{}/chart/{}?chartCloseOnly=true&token={}'.format(
                domain,
                ticker,
                timeframe,
                key
            )

        historicalData = requests.get(url).json()
    except:
        print("Unexpected error:", sys.exc_info()[0])
        return {}

    return historicalData


def batchHistoricalData(batch, timeframe, priceOnly=False, sandbox=False):
    domain = 'cloud.iexapis.com'
    key = os.environ.get("IEX_TOKEN")
    if (sandbox):
        domain = 'sandbox.iexapis.com'
        key = os.environ.get("IEX_SANDBOX_TOKEN")

    batch = ",".join(batch)  # Convert to comma-separated string
    try:
        url = 'https://{}/stable/stock/market/batch?symbols={}&types=chart&range={}&token={}'.format(
            domain,
            batch,
            timeframe,
            key
        )
        if (priceOnly):
            url = 'https://{}/stable/stock/market/batch?symbols={}&types=chart&range={}&chartCloseOnly=true&token={}'.format(
                domain,
                batch,
                timeframe,
                key
            )
        print(url)
        sys.exit()
        batchrequest = requests.get(url).json()
    except:
        # print("Unexpected error:", sys.exc_info()[0])
        return {}

    return batchrequest


def getHistoricalEarnings(ticker, quarters=4, sandbox=False):
    domain = 'cloud.iexapis.com'
    key = os.environ.get("IEX_TOKEN")
    if (sandbox):
        domain = 'sandbox.iexapis.com'
        key = os.environ.get("IEX_SANDBOX_TOKEN")
    try:
        url = 'https://{}/stable/stock/{}/earnings/{}/?token={}'.format(
            domain,
            ticker,
            quarters,
            key
        )
        earnings = requests.get(url).json()
    except:
        #print("Unexpected error:", sys.exc_info()[0])
        return None

    return earnings
