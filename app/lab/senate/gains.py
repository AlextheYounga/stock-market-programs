
from app.lab.core.output import printFullTable
from app.functions import chunks
from app.lab.core.api.iex import IEX
import sys
import os
import json
import redis
import django
from dotenv import load_dotenv
load_dotenv()
django.setup()
from app.database.models import Senate


def senate_gains():
    senators = Senate.objects.all()
    iex = IEX()
    stocks = Senate.objects.all().values_list('tickers', flat=True)
    chunked_tickers = chunks(stocks, 100)
    for chunk in chunked_tickers:
        batch = iex.get('price', chunk)
        
    

