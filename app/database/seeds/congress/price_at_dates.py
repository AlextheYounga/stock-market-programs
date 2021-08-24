from app.lab.core.output import printFullTable
from app.lab.core.api.iex import IEX
import sys
import os
import json
import datetime
from app.database.redisdb.rdb import Rdb
import django
from dotenv import load_dotenv
load_dotenv()
django.setup()
from app.database.models import Congress, Stock
from app.lab.core.api.senatewatcher import SenateWatcher


iex = IEX()
r = Rdb().setup()
congress = Congress.objects.all()        
datestocks = {}
for rep in congress: 
    if (rep.ticker and rep.date):
        date = rep.date.strftime('%Y%m%d')
        if (date in datestocks):
            datestocks[date].append(rep.ticker)
            continue
        datestocks[date] = [rep.ticker] 

def savePriceAtDate(ticker, date, price):
    # Save all tickers at date
    records = Congress.objects.filter(date=date, ticker=ticker, price_at_date__isnull=True)
    for record in records:
        record.update(price_at_date=price)        
        print(f"Saved {record.ticker} at {record.date}")

for date, stocks in datestocks.items():
    print(date)
    TODO: Figure out discrepancy in date.
    # https://cloud.iexapis.com/stable/stock/market/chart/date/20210730?chartByDay=true&filter=close,symbol&symbols=F%2CPINS%2CIFNNY%2CROK%2CDECK
    apistocks = []
    for stock in stocks:        
        # If cached        
        rdate = datetime.datetime.strptime(date, '%Y%m%d').strftime('%Y-%m-%d')
        price = r.get(f"priceatdate{stock}-{rdate}")
        print(f"priceatdate{stock}-{rdate}")
        if (price):            
            savePriceAtDate(stock, date, price)
        else:
            apistocks.append(stock)
    
    # Fetch from API if not cached
    if (apistocks):
        pads = iex.priceAtDate(apistocks, date)
        for pad in pads:
            if (isinstance(pad, list)):
                pad = pad[0]
            print(f"priceatdate{pad['symbol']}-{pad['date']}")
            r.set(f"priceatdate{pad['symbol']}-{pad['date']}", pad['close'])
            savePriceAtDate(pad['symbol'], pad['date'], pad['close'])        