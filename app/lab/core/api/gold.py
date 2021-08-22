from datetime import datetime, time, timedelta
import time
from dotenv import load_dotenv
import requests
from app.database.redisdb.rdb import Rdb
import sys
import json
import os
import http.client
import mimetypes
load_dotenv()


def goldForexPrice():
    """
    Real time forex gold price
    """
    url = 'https://forex-data-feed.swissquote.com/public-quotes/bboquotes/instrument/XAU/USD'
    futures = requests.get(url).json()
    price = futures[0]['spreadProfilePrices'][0]['bid']

    return price


def syncGoldPrices():
    print('Syncing gold prices... ')
    r = Rdb().setup()

    def goldapi_io_fetch(date):
        """
        Taken directly from goldapi.io
        """
        conn = http.client.HTTPSConnection("www.goldapi.io")
        payload = ''

        headers = {
            'x-access-token': os.environ.get("GOLDAPI_KEY"),
            'Content-Type': 'application/json'
        }

        conn.request("GET", "/api/XAU/USD/"+date, payload, headers)
        res = conn.getresponse()
        data = res.read().decode("utf-8")
        saveDate = datetime.strptime(date, '%Y%m%d').strftime('%Y-%m-%d')
        if ('price' in data):
            r.set('gold-'+saveDate+'-close', json.loads(data)['price'])
        else:
            print(data, "www.goldapi.io"+"/api/XAU/USD/"+date)

        return True

    today = datetime.today()
    i = 0
    while True:
        day = (today - timedelta(days=i))
        gprice = r.get('gold-'+day.strftime('%Y-%m-%d')+'-close')

        if (gprice):
            print('Gold prices up to date.')
            break

        goldapi_io_fetch(day.strftime('%Y%m%d'))

        time.sleep(0.5)
        i += 1


# def metalsApi():
    # Not sure about this one.
    # base_currency = 'USD'
    # symbol = 'XAU'
    # endpoint = '1999-12-24'
    # access_key = os.environ.get("METALS_API_KEY")

    # url = 'https://metals-api.com/api/'+endpoint+'?access_key='+access_key+'&base='+base_currency+'&symbols='+symbol
    # print(url)
    # sys.exit()

    # try:
    #     gold_price = requests.get(url).json()
    # except:
    #     print("Unexpected error:", sys.exc_info()[0])
    #     return None

    # return gold_price
