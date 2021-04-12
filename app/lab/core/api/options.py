import datetime
from dotenv import load_dotenv
import requests
import sys
import json
import os
load_dotenv()


def getExpirations(ticker, sandbox=False):
    """
    Fetches all options expiration dates from a ticker

    Parameters
    ----------
    ticker      :string
    sandbox     :bool
                Sets the IEX environment to sandbox mode to make limitless API calls for testing.

    Returns
    -------
    list of option expiration dates
    """
    domain = 'cloud.iexapis.com'
    key = os.environ.get("IEX_TOKEN")
    if (sandbox):
        domain = 'sandbox.iexapis.com'
        key = os.environ.get("IEX_SANDBOX_TOKEN")
    try:
        url = 'https://{}/stable/stock/{}/options?token={}'.format(
            domain,
            ticker,
            key
        )
        options = requests.get(url).json()
    except:
        #print("Unexpected error:", sys.exc_info()[0])
        return None

    return options


def getOptionChain(ticker, date, sandbox=False):
    """
    Fetches the option chain (calls and puts), for a ticker.

    Parameters
    ----------
    ticker      :string
    date        :datetime.datetime
    sandbox     :bool
                Sets the IEX environment to sandbox mode to make limitless API calls for testing.

    Returns
    -------
    list of option expiration dates
    """
    def formatDate(date):
        if (isinstance(date, datetime.datetime)):
            fdate = datetime.datetime.strftime(date, '%Y%m%d')
            return fdate
        else:
            print('Failure in getOptionChain(). Date param must be of type datetime.datetime. Closing program...')
            sys.exit()

    fdate = formatDate(date)
    domain = 'cloud.iexapis.com'
    key = os.environ.get("IEX_TOKEN")

    if (sandbox):
        domain = 'sandbox.iexapis.com'
        key = os.environ.get("IEX_SANDBOX_TOKEN")

    try:
        url = 'https://{}/stable/stock/{}/options/{}?token={}'.format(
            domain,
            ticker,
            fdate,
            key
        )
        print(url)
        sys.exit()
        chain = requests.get(url).json()
    except:
        #print("Unexpected error:", sys.exc_info()[0])
        return None

    return chain


def getOptionChainTD(ticker, timeRange):
    """
    Fetches the option chain (calls and puts), for a ticker from TD Ameritrade.

    Parameters
    ----------
    ticker      :string
    timeRange   :list
                List containing [fromDate, toDate], each as datetime.datetime 
    optionRange :str
                Sets the option range to 'In the money', 'Out of the money', etc.
                Example: OTM

    Returns
    -------
    list of option expiration dates
    """
    def formatDate(dates):
        results = []
        for date in dates:
            if (isinstance(date, datetime.datetime)):
                fdate = datetime.datetime.strftime(date, '%Y-%m-%d')
                results.append(fdate)
            else:
                print('Failure in getOptionChain(). Date param must be of type datetime.datetime. Closing program...')
                sys.exit()
        return tuple(results)

    fromDate, toDate = formatDate(timeRange)
    domain = 'api.tdameritrade.com/v1/marketdata'
    key = os.environ.get("TDAMER_KEY")
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML'
    }        
    url = 'https://{}/chains?apikey={}&symbol={}&fromDate={}&toDate={}'.format(
        domain,
        key,
        ticker,
        fromDate,
        toDate
    )
    chain = requests.get(url, headers=headers).json()
    if isinstance(chain, dict):
        return chain
    else:        
        print(chain)
        sys.exit()
