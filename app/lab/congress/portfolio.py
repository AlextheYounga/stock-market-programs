
from app.lab.core.output import printFullTable
from app.functions import chunks, filterNone
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
from app.database.models import Senate, Stock
from app.lab.core.api.senatewatcher import SenateWatcher

# TODO: Finish the portfolio
class SenatorPortfolio():
    def getPriceAtDate(self):
        iex = IEX()
        senators = Senate.objects.all()
        # stocks = filterNone(list(Senate.objects.all().values_list('ticker', flat=True)))
        datestocks = {}
        for senator in senators: 
            if (senator.ticker):
                date = senator.date.strftime('%Y%m%d')
                if (date in datestocks):
                    datestocks[date].append(senator.ticker)
                    continue
                datestocks[date] = [senator.ticker] 

        for date, stocks in datestocks.items():
            pads = iex.priceAtDate(stocks, date)            
            if (isinstance(pads, list) and len(pads) > 1):
                for pad in pads[0]:
                    print(pad)

            # for pad in pads:
            #     records = Senate.objects.filter(date=date, ticker=pad, price_at_date__isnull=True)
            #     for record in records:
            #         record.price_at_date = pad

# sp = SenatorPortfolio()
# sp.getPriceAtDate()

