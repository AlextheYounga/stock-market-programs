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
hw = HouseWatcher()
sw = SenateWatcher()

Congress.objects.all().delete()
CongressTransaction.objects.all().delete()
Congress.objects.raw("DELETE FROM sqlite_sequence WHERE name ='database_congress';")
CongressTransaction.objects.raw("DELETE FROM sqlite_sequence WHERE name ='database_congresstransaction';")

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

stati = [
    'holding',
    'sold',
]

def calculateShares(pad, amount_low):
    if (pad and amount_low):
        return int(amount_low / pad)

    return None

def latest_price(ticker):
    if (ticker):
        stock = Stock.objects.filter(ticker=ticker).first()
        if (stock):
            return stock.latestPrice
    return None


def calculateGainDollars(shares, cost, price):
    if (shares and cost and price):
        return float((shares * price) - (shares * cost))
    return 0

def calculateGainPercent(amount_low, gaindollars):
    if (amount_low and gaindollars):
        return round(((gaindollars - amount_low) / amount_low) * 100, 2)

    return 0


CONGRESS = {}
TRANSACTIONS = []
PORTFOLIO = []
for rep in CONGRESSDATA:
    first_name = rep['first_name'].title() if rep.get('first_name', False) else None
    last_name = rep['last_name'].title() if rep.get('last_name', False) else None
    house = rep.get('house', None)
    sale_type = saletypes[rep['sale_type']] if rep.get('sale_type', False) else None
    pad = rep.get('price_at_date', None)
    amount_low = rep.get('amount_low', None)
    shares = calculateShares(pad, amount_low)
    ticker = rep.get('ticker', None)
    current_price = latest_price(ticker)
    gaindollars = calculateGainDollars(shares, pad, current_price)
    name = ' '.join([rep.get('first_name', None), rep['last_name']]).title()
    transactionDct = rep.get('transaction', {})
    link = rep.get('link', None)
    link_id = hw.getLinkId(link) if (house == 'House') else sw.getLinkId(link)
    transactionDct.update({'link_id': link_id or None})
    print(name)
    
    congress = {
        'first_name': first_name,
        'last_name': last_name,
        'name': name,
        'house': house,
        'office': rep.get('office', None),
        'district': rep.get('district', None),
        'total_gain_dollars': None,
        'total_gain_percent': None,
        'trades': None,
    }

    transaction = {
        'first_name': first_name,
        'last_name': last_name,
        'sale_type': sale_type,
        'ticker': ticker,
        'price_at_date': pad,
        'amount_low': amount_low,
        'amount_high': rep.get('amount_high', None),
        'date': rep.get('date', None),
        'filing_date': rep.get('filing_date', None),
        'owner': rep.get('owner', None),
        'link': link,
        'description': transactionDct.pop('asset_description') if ('asset_description' in transactionDct) else None,  
        'asset_type': transactionDct.pop('asset_type') if ('asset_type' in transactionDct) else None,  
        'comment': transactionDct.pop('comment') if ('comment' in transactionDct) else None,
        'transaction': transactionDct,  
    }

    portfolio = {
        'first_name': first_name,
        'last_name': last_name,
        'position': 'long',
        'ticker': ticker,
        'description': transaction['description'],
        'shares': shares,
        'cost_share': pad,
        'latest_price': current_price,
        'market_value': amount_low,
        'gain_dollars': gaindollars,
        'gain_percent': calculateGainPercent(amount_low, gaindollars),
        'status': '',
    }


    CONGRESS[name] = congress
    TRANSACTIONS.append(transaction)
    PORTFOLIO.append(portfolio)

for name, info in CONGRESS.items():
    record, created = Congress.objects.update_or_create(
        name=name,
        defaults=info
    )
    print(stylize(f"{name} saved", colored.fg("green")))

for t in TRANSACTIONS:
    crecord = Congress.objects.get(first_name=t['first_name'], last_name=t['last_name'])
    t['congress_id'] = crecord.id
    t['hash_key'] = hw.generateHash(t) if (crecord.house == 'House') else sw.generateHash(t)
    trecord = CongressTransaction(**t)
    trecord.save()
    print(stylize(f"{trecord.ticker} {trecord.date} {trecord.amount_low} saved", colored.fg("green")))

# print(len(TRANSACTIONS))
# print(len(PORTFOLIO))


