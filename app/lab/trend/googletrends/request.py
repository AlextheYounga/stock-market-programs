from pytrends.request import TrendReq
from datetime import datetime
from ..functions import getPennyStocks
from app.lab.core.output import printStockResults
import colored
from colored import stylize
import time
from app.database.redisdb.rdb import Rdb
import json
import sys


def stock_search_trends(rescan=False):
    """
    This function will request search query data from Google for all stocks listed on IEX. 
    It is purposely slow. I have added a 5 second wait limit between each request due to the size of the requests we're 
    going to make and the unpredictability of Google's rate limits. To ensure we keep Google happy. 
    """
    tickers = getPennyStocks()
    r = Rdb().setup()

    if (rescan):
        pytrends = TrendReq(hl='en-US', tz=360)
        for i, ticker in enumerate(tickers):
            query = ticker+' stock'
            pytrends.build_payload([query], cat=0, timeframe='today 12-m', geo='', gprop='')
            interest = pytrends.interest_over_time().to_dict()

            data = {}
            if (interest):
                for date, value in interest[query].items():
                    data[date.strftime('%Y-%m-%d')] = value

                r.set('trends-'+ticker+'-interest', json.dumps(data))
                print(stylize("Request {} Saved {}".format(i, ticker), colored.fg("green")))
            time.sleep(10)

    recent_interest = []
    for t in tickers:
        rdb_data = r.get('trends-'+t+'-interest')
        price = r.get('stock-'+t+'-price')
        if (rdb_data):
            searches = json.loads(rdb_data)
            if (list(searches.values())[-1] == 100):
                if (float(price) > 0.5):
                    recent_interest.append(t)

    printStockResults(recent_interest)
