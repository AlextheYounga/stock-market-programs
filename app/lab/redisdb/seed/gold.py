import django
from django.apps import apps
from ...core.imports import read_historical_gold_prices
import json
import redis
import sys
import os
from dotenv import load_dotenv
load_dotenv()
django.setup()

r = redis.Redis(host='localhost', port=6379, db=0, charset="utf-8", decode_responses=True)

gold_prices = read_historical_gold_prices(datepriceOnly=False)

for day, g in gold_prices.items():
    print('Saved {} - {}'.format(day, g['close']))
    r.set('gold-'+day+'-close', g['close'])
    r.set('gold-'+day+'-open',g['open'])
    r.set('gold-'+day+'-high', g['high'])
    r.set('gold-'+day+'-low', g['low'])
