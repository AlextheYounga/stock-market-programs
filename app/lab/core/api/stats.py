from iexfinance.stocks import Stock, get_historical_data
from datetime import datetime, time, timedelta
from dotenv import load_dotenv
import requests
import sys
import json
import os
load_dotenv()


def getCurrentPrice(ticker, sandbox=False):
    """
    Fetches latest price

    Parameters
    ----------
    ticker      :string
    sandbox     :bool
                Sets the IEX environment to sandbox mode to make limitless API calls for testing.

    Returns
    -------
    latest price as float 
    """
    key = os.environ.get("IEX_TOKEN")
    if (sandbox):
        os.environ['IEX_API_VERSION'] = 'iexcloud-sandbox'
        key = os.environ.get("IEX_SANDBOX_TOKEN")
    try:
        stock = Stock(ticker, token=key)
        price = stock.get_price()[ticker].iloc[0]
    except:
        #print("Unexpected error:", sys.exc_info()[0])
        return {}

    if (sandbox):
        os.environ['IEX_API_VERSION'] = 'v1'
    return price


def getPriceTarget(ticker, sandbox=False):
    domain = 'cloud.iexapis.com'
    key = os.environ.get("IEX_TOKEN")
    if (sandbox):
        domain = 'sandbox.iexapis.com'
        key = os.environ.get("IEX_SANDBOX_TOKEN")
    try:
        url = 'https://{}/stable/stock/{}/price-target?token={}'.format(
            domain,
            ticker,
            key
        )
        priceTarget = requests.get(url).json()
    except:
        #print("Unexpected error:", sys.exc_info()[0])
        return None

    return priceTarget


def getQuoteData(ticker, sandbox=False):
    key = os.environ.get("IEX_TOKEN")
    if (sandbox):
        os.environ['IEX_API_VERSION'] = 'iexcloud-sandbox'
        key = os.environ.get("IEX_SANDBOX_TOKEN")
    try:
        stock = Stock(ticker, token=key)
        quote = stock.get_quote()
    except:
        #print("Unexpected error:", sys.exc_info()[0])
        return {}
    if (sandbox):
        os.environ['IEX_API_VERSION'] = 'v1'
    return quote


def getKeyStats(ticker, filterResults=[], sandbox=False):
    """
    Fetches company info from stock ticker.

    Parameters
    ----------
    ticker          :string
    filterResults   :list
    sandbox         :bool
                    Sets the IEX environment to sandbox mode to make limitless API calls for testing.

    Returns
    -------
    dict object of IEX results
    """
    domain = 'cloud.iexapis.com'
    key = os.environ.get("IEX_TOKEN")
    if (sandbox):
        domain = 'sandbox.iexapis.com'
        key = os.environ.get("IEX_SANDBOX_TOKEN")
    if (filterResults):
        filters = ",".join(filterResults) if (len(filterResults) > 1) else filterResults[0]
    try:
        url = 'https://{}/stable/stock/{}/stats?token={}'.format(
            domain,
            ticker,
            key
        )
        if (filterResults):
            url = 'https://{}/stable/stock/{}/stats?filter={}&token={}'.format(
                domain,
                ticker,
                filters,
                key
            )
        keyStats = requests.get(url).json()
    except:
        #print("Unexpected error:", sys.exc_info()[0])
        return None

    return keyStats


def getAdvancedStats(ticker, filterResults=[], sandbox=False):
    """
    Fetches company info from stock ticker.

    Parameters
    ----------
    ticker          :string
    filterResults   :list
    sandbox         :bool
                    Sets the IEX environment to sandbox mode to make limitless API calls for testing.

    Returns
    -------
    dict object of IEX results
    """
    domain = 'cloud.iexapis.com'
    key = os.environ.get("IEX_TOKEN")
    if (sandbox):
        domain = 'sandbox.iexapis.com'
        key = os.environ.get("IEX_SANDBOX_TOKEN")
    if (filterResults):
        filters = ",".join(filterResults) if (len(filterResults) > 1) else filterResults[0]
    try:
        url = 'https://{}/stable/stock/{}/advanced-stats?token={}'.format(
            domain,
            ticker,
            key
        )
        if (filterResults):
            url = 'https://{}/stable/stock/{}/advanced-stats?filter={}&token={}'.format(
                domain,
                ticker,
                filters,
                key
            )
        advancedStats = requests.get(url).json()
    except:
        #print("Unexpected error:", sys.exc_info()[0])
        return None

    return advancedStats


def getFinancials(ticker, sandbox=False):
    domain = 'cloud.iexapis.com'
    key = os.environ.get("IEX_TOKEN")
    if (sandbox):
        domain = 'sandbox.iexapis.com'
        key = os.environ.get("IEX_SANDBOX_TOKEN")
    try:
        url = 'https://{}/stable/stock/{}/financials?token={}'.format(
            domain,
            ticker,
            key
        )
        financials = requests.get(url).json()
    except:
        # print("Unexpected error:", sys.exc_info()[0])
        return None

    return financials


def getCashFlow(ticker, sandbox=False):
    domain = 'cloud.iexapis.com'
    key = os.environ.get("IEX_TOKEN")
    if (sandbox):
        domain = 'sandbox.iexapis.com'
        key = os.environ.get("IEX_SANDBOX_TOKEN")
    try:
        url = 'https://{}/stable/stock/{}/cash-flow?token={}'.format(
            domain,
            ticker,
            key
        )
        cashflow = requests.get(url).json()
    except:
        # print("Unexpected error:", sys.exc_info()[0])
        return None

    return cashflow
