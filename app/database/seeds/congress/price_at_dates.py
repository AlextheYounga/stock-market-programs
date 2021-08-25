from app.lab.core.api.senatewatcher import SenateWatcher
from app.lab.core.output import printFullTable
from app.lab.core.api.iex import IEX
import colored
from colored import stylize
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
        record.price_at_date = price
        record.save()
        print(stylize(f"Saved {record.ticker} at {record.date}", colored.fg("green")))

for date, stocks in datestocks.items():
    # https://cloud.iexapis.com/stable/stock/market/chart/date/20210730?chartByDay=true&filter=close,symbol&symbols=F%2CPINS%2CIFNNY%2CROK%2CDECK
    apistocks = []
    apifound = []
    fdate = datetime.datetime.strptime(date, '%Y%m%d').strftime('%Y-%m-%d')
    for stock in stocks:
        # If cached
        price = r.get(f"priceatdate{stock}-{date}")
        if (price == 'None'):
            continue        
        
        if (price):
            print(f"Cache priceatdate{stock}-{date}")
            savePriceAtDate(stock, fdate, price)
        else:
            apistocks.append(stock)

    # Fetch from API if not cached
    if (apistocks):
        pads = iex.priceAtDate(apistocks, date)
        for pad in pads:
            if (pad):                
                if (isinstance(pad, list)):
                    pad = pad[0]

                apifound.append(pad['symbol'])
                print(f"API {pad['symbol']} {date}")
                r.set(f"priceatdate{pad['symbol']}-{date}", pad.get('close', 'None'))                
                savePriceAtDate(pad['symbol'], fdate, pad['close'])
    
    # Set all the ones we didn't find
        for stock in stocks:
            if (stock not in apifound):            
                r.set(f"priceatdate{stock}-{date}", 'None')  
