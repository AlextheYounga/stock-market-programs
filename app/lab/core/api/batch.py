from iexfinance.stocks import Stock, get_historical_data
from datetime import datetime, time, timedelta
from dotenv import load_dotenv
import colored
from colored import stylize
import requests
import sys
import json
import os
load_dotenv()


def companyBatchRequest(batch, sandbox=False):
    """
    Fetches company info for a batch of tickers. Max 100 tickers

    Parameters
    ----------
    batch       :list
                list of max 100 tickers
    sandbox     :bool
                Sets the IEX environment to sandbox mode to make limitless API calls for testing.

    Returns
    -------
    dict object of company info for 100 tickers
    """
    domain = 'cloud.iexapis.com'
    key = os.environ.get("IEX_TOKEN")
    if (sandbox):
        domain = 'sandbox.iexapis.com'
        key = os.environ.get("IEX_SANDBOX_TOKEN")
    try:
        batch = ",".join(batch)  # Convert to comma-separated string
        url = 'https://{}/stable/stock/market/batch?symbols={}&types=quote,company&token={}'.format(
            domain,
            batch,
            key
        )
        batch_request = requests.get(url).json()
    except:
        #print("Unexpected error:", sys.exc_info()[0])
        return {}

    return batch_request


def batchPrice(batch, sandbox=False):
    """
    Fetches company info for a batch of tickers. Max 100 tickers

    Parameters
    ----------
    batch       :list
                list of max 100 tickers
    sandbox     :bool
                Sets the IEX environment to sandbox mode to make limitless API calls for testing.

    Returns
    -------
    dict object of company info for 100 tickers
    """
    domain = 'cloud.iexapis.com'
    key = os.environ.get("IEX_TOKEN")
    if (sandbox):
        domain = 'sandbox.iexapis.com'
        key = os.environ.get("IEX_SANDBOX_TOKEN")
    try:
        batch = ",".join(batch)  # Convert to comma-separated string
        url = 'https://{}/stable/stock/market/batch?symbols={}&types=quote&filter=latestPrice&token={}'.format(
            domain,
            batch,
            key
        )
        batch_request = requests.get(url).json()
    except:
        #print("Unexpected error:", sys.exc_info()[0])
        return {}

    return batch_request


def batchQuote(batch, sandbox=False):
    """
    Fetches company info for a batch of tickers. Max 100 tickers

    Parameters
    ----------
    batch       :list
                list of max 100 tickers
    sandbox     :bool
                Sets the IEX environment to sandbox mode to make limitless API calls for testing.

    Returns
    -------
    dict object of company info for 100 tickers
    """
    domain = 'cloud.iexapis.com'
    key = os.environ.get("IEX_TOKEN")
    if (sandbox):
        domain = 'sandbox.iexapis.com'
        key = os.environ.get("IEX_SANDBOX_TOKEN")
    try:
        batch = ",".join(batch)  # Convert to comma-separated string
        url = 'https://{}/stable/stock/market/batch?symbols={}&types=quote&token={}'.format(
            domain,
            batch,
            key
        )
        batch_request = requests.get(url).json()
    except:
        #print("Unexpected error:", sys.exc_info()[0])
        return {}

    return batch_request


def quoteStatsBatchRequest(batch, sandbox=False):
    """
    Fetches quotes and key stats for a batch of tickers. Max 100 tickers

    Parameters
    ----------
    batch       :list
                list of max 100 tickers
    sandbox     :bool
                Sets the IEX environment to sandbox mode to make limitless API calls for testing.

    Returns
    -------
    dict object of quotes and key stats for 100 tickers
    """
    domain = 'cloud.iexapis.com'
    key = os.environ.get("IEX_TOKEN")
    if (sandbox):
        domain = 'sandbox.iexapis.com'
        key = os.environ.get("IEX_SANDBOX_TOKEN")    
    batch = ",".join(batch)  # Convert to comma-separated string
    try:
        url = 'https://{}/stable/stock/market/batch?symbols={}&types=quote,stats&token={}'.format(
            domain,
            batch,
            key
        )
        batch_request = requests.get(url).json()
    except:
        print(stylize("Unexpected error: "+sys.exc_info()[0], colored.fg("red")))
        return {}

    return batch_request
