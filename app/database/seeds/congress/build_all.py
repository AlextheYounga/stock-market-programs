from app.lab.core.api.senatewatcher import SenateWatcher
from app.lab.core.api.housewatcher import HouseWatcher
from app.lab.core.output import printFullTable
from app.functions import readJSONFile, writeJSONFile, filterNone
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
from app.database.models import Congress, CongressTransaction, CongressPortfolio, Stock

congresspath = 'app/lab/congress/database_congress.json'
CONGRESSDATA = readJSONFile(congresspath)

# "id": 47,
# "hash_key": "f688543e4c6385de804bf20533056c4c3c924ccb0f9d887d9f8b1b3984ccf613",
# "house": "Senate",
# "first_name": "Thomas R",
# "last_name": "Carper",
# "owner": "Spouse",
# "office": "Carper, Thomas R. (Senator)",
# "district": null,
# "link": "https://efdsearch.senate.gov/search/view/ptr/ab4ef7b8-d7ac-48b4-860f-dd7033dbcdd7/",
# "date": "2021-07-26",
# "filing_date": null,
# "ticker": "LUBFX",
# "price_at_date": null,
# "amount_low": 1001,
# "amount_high": 15000,
# "sale_type": "Purchase",
# "transaction": {
#   "asset_description": "Lord Abbett Ultra Short Bond Fund - Class F",
#   "asset_type": "Other Securities",
#   "comment": null
# }

#     class Congress(models.Model):
#     id = models.AutoField(primary_key=True)
#     first_name = models.CharField(max_length=300, null=True)
#     last_name = models.CharField(max_length=300)
#     name = models.CharField(max_length=300, unique=True, default=last_name)
#     house = models.CharField(max_length=300)
#     office = models.CharField(max_length=300, null=True)
#     district = models.CharField(max_length=300, null=True)
#     total_gain_dollars = models.FloatField(null=True)
#     total_gain_percent = models.FloatField(null=True)
#     trades = models.IntegerField(null=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

# class CongressTransaction(models.Model):
#     id = models.AutoField(primary_key=True)
#     congress_id = models.ForeignKey(Congress, on_delete=CASCADE)
#     first_name = models.CharField(max_length=300, null=True)
#     last_name = models.CharField(max_length=300)
#     sale_type = models.CharField(max_length=500, null=True)
#     ticker = models.CharField(max_length=10, null=True)
#     price_at_date = models.FloatField(null=True)
#     amount_low = models.IntegerField(null=True)
#     amount_high = models.IntegerField(null=True)
#     date = models.DateField(auto_now=False, auto_now_add=False, null=True)
#     filing_date = models.DateField(auto_now=False, auto_now_add=False, null=True)
#     owner = models.CharField(max_length=300, null=True)
#     link = models.TextField(null=True)
#     transaction = models.JSONField(null=True)
#     hash_key = models.CharField(max_length=70, unique=True, default=None)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

# class CongressPortfolio(models.Model):
# id = models.AutoField(primary_key=True)
# congress_id = models.ForeignKey(Congress, on_delete=CASCADE)
# transaction_id = models.ForeignKey(CongressTransaction, on_delete=CASCADE)
# first_name = models.CharField(max_length=300, null=True)
# last_name = models.CharField(max_length=300)
# position = models.CharField(max_length=100, null=True)
# ticker = models.CharField(max_length=10, null=True)
# description = models.TextField(unique=True)
# shares = models.IntegerField(null=True)
# cost_share = models.FloatField(null=True)
# latest_price = models.FloatField(null=True)
# market_value = models.FloatField(null=True)
# gain_dollars = models.FloatField(null=True)
# gain_percent = models.FloatField(null=True)
# created_at = models.DateTimeField(auto_now_add=True)
# updated_at = models.DateTimeField(auto_now=True)


saletypes = {
    'Sale (Partial)': 'partial-sell',
    'Sale (Full)': 'sell',
    'Purchase': 'buy',
    'Exchange': 'exchange',
    'sale_full': 'sell',
    'purchase': 'buy',
    'sale_partial': 'partial-sell',
    'exchange': 'exchange',
}

def shares(pad, amount_low):
    if (pad and amount_low):
        return int(amount_low / pad)

    return None

def latest_price(ticker):
    if (ticker):
        return Stock.objects.filter(ticker=ticker).lastPrice
    return None


def gain_dollars(shares, cost, price):
    if (shares, cost, price):
        return float((shares * price) - (shares * cost))
    return 0

def gain_percent(amount_low, shares, cost, price):
    # TODO: Finish this equation
    if (amount_low, shares, cost, price):
        return float()
    return 0


CONGRESS = []
TRANSACTIONS = []
PORTFOLIO = []
for rep in CONGRESSDATA:
    sale_type = saletypes[CONGRESSDATA['sale_type']] if CONGRESSDATA.get('sale_type', False) else None
    pad = CONGRESSDATA.get('price_at_date', None)
    amount_low = CONGRESSDATA.get('amount_low', None)
    shares = shares(pad, amount_low)
    ticker = CONGRESSDATA.get('ticker', None)
    current_price = latest_price(ticker)

    congress = {
        'first_name': CONGRESSDATA.get('first_name', None),
        'last_name': CONGRESSDATA['last_name'],
        'name': ' '.join(CONGRESSDATA.get('first_name', None), CONGRESSDATA['last_name']),
        'house': CONGRESSDATA.get('house', None),
        'office': CONGRESSDATA.get('office', None),
        'district': CONGRESSDATA.get('district', None),
        'total_gain_dollars': 0,
        'total_gain_percent': 0,
        'trades': 0,
    }

    transaction = {
        'first_name': CONGRESSDATA.get('first_name', None),
        'last_name': CONGRESSDATA['last_name'],
        'sale_type': sale_type,
        'ticker': ticker,
        'price_at_date': pad,
        'amount_low': amount_low,
        'amount_high': CONGRESSDATA.get('amount_high', None),
        'date': CONGRESSDATA.get('date', None),
        'filing_date': CONGRESSDATA.get('filing_date', None),
        'owner': CONGRESSDATA.get('owner', None),
        'link': CONGRESSDATA.get('link', None),
        'transaction': CONGRESSDATA.get('transaction', None),
        'hash_key': CONGRESSDATA.get('hash_key', None),
    }

    portfolio = {
        'first_name': CONGRESSDATA.get('first_name', None),
        'last_name': CONGRESSDATA['last_name'],
        'position': 'long',
        'ticker': ticker,
        'description': CONGRESSDATA['transaction'].get('asset_description', None),
        'shares': shares,
        'cost_share': pad,
        'latest_price': current_price,
        'market_value': amount_low,
        'gain_dollars': gain_dollars(shares, pad, current_price)
        # gain_dollars = models.FloatField(null=True)
# gain_percent = models.FloatField(null=True)
    }
