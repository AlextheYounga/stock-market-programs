
from tabnanny import check
from app.lab.core.output import printFullTable
from app.lab.core.api.iex import IEX
from app.functions import chunks
from app.lab.core.output import writeCSV
import statistics
from datetime import date
import sys
import os
import json
import django
import colored
from colored import stylize
from dotenv import load_dotenv
load_dotenv()
django.setup()
from app.functions import filterNone
from app.database.models import Congress, CongressTransaction, CongressPortfolio, Stock


def calculateShares(pad, amount):
    if (pad and amount):
        return int(amount / pad)

    return None


def latest_price(ticker):
    if (ticker):
        stock = Stock.objects.filter(ticker=ticker).first()
        if (stock):
            return stock.latestPrice
    return None


def calculateGainDollars(shares, cost_share, price):
    if (shares and cost_share and price):
        return int((shares * price) - (shares * cost_share))
    return None


def calculateGainPercent(shares, cost, price):
    if (shares and cost and price):
        startval = (shares * cost)
        currentval = (shares * price)

        percentChange = ((currentval - startval) / startval) * 100
        return round(percentChange, 2)

    return None


def calculateMarketValue(amount, action, mkval=False):
    if (amount and mkval):
        if (action == 'sell'):
            new_mkval = (mkval - amount)
        if (action == 'buy'):
            new_mkval = (mkval + amount)

        if (new_mkval < 0):
            new_mkval = 0
        return new_mkval
    return amount or 0


def determineStatus(marketval):
    if (marketval == 0):
        return 'sold'
    elif (marketval < 0):
        return 'unknown'
    else:
        return 'holding'


"""
Generate Report Start
"""
members = Congress.objects.all()
iex = IEX()
member_orders = {}
for member in members:
    name = f"{member.first_name} {member.last_name}"
    member_orders[name] = {}
    transactions = member.congresstransaction_set.all().order_by('date')
    print(f"Analyzing {name}")

    for tr in transactions:
        if (tr.ticker):
            trx_date = (tr.date or tr.filing_date).strftime('%Y-%m-%d')
            ticker = tr.ticker
            description = tr.description
            amount_low = tr.amount_low
            amount_high = tr.amount_high
            amount = int(statistics.mean([amount_low, amount_high])) if (amount_low and amount_high) else (amount_low or amount_high)
            pad = tr.price_at_date
            sale_type = tr.sale_type
            shares = calculateShares(pad, amount)
            current_price = latest_price(ticker)
            gaindollars = calculateGainDollars(shares, pad, pad)
            gainPercent = calculateGainPercent(shares, pad, pad)

            if ((ticker) in member_orders[name]):
                pf = member_orders[name][ticker]
                if (sale_type == 'partial-sell'):
                    pf['market_value'] = calculateMarketValue(amount, 'sell', pf.get('market_value', False))
                    pf['shares'] = (pf['shares'] - shares) if (pf.get('shares', False) and shares) else pf['shares']
                    pf['status'] = determineStatus(pf['market_value'])

                if (sale_type == 'sell'):
                    pf['market_value'] = calculateMarketValue(amount, 'sell', pf.get('market_value', False))
                    pf['shares'] = (pf['shares'] - shares) if (pf.get('shares', False) and shares) else pf['shares']
                    pf['status'] = determineStatus(pf['market_value'])

                if (sale_type == 'buy'):
                    pf['market_value'] = calculateMarketValue(amount, 'buy', pf.get('market_value', False))
                    pf['cost_share'] = round(statistics.mean([pf['cost_share'], pad]), 2) if (pad and pf.get('cost_share', False)) else pf['cost_share']
                    pf['shares'] = (pf['shares'] + shares) if (pf.get('shares', False) and shares) else pf['shares']
                    pf['status'] = determineStatus(pf['market_value'])

                if (pf.get('shares', False) and pf['shares'] < 0):
                    pf['shares'] = 0

                if (pf['status'] == 'holding'):
                    pf['gain_dollars'] = calculateGainDollars(pf['shares'], pf['cost_share'], current_price)
                    pf['gain_dollars'] = calculateGainPercent(pf['shares'], pf['cost_share'], current_price)

                if (pf['status'] == 'sold'):
                    pf['gain_dollars'] = calculateGainDollars(pf['shares'], pf['cost_share'], pad)
                    pf['gain_dollars'] = calculateGainPercent(pf['shares'], pf['cost_share'], pad)

                if (pf['status'] == 'unknown'):
                    pf['gain_dollars'] = None
                    pf['gain_dollars'] = None

                pf['orders'].update({
                    trx_date: {
                        'sale_type': sale_type,
                        'amount_low': amount_low,
                        'amount_high': amount_high,
                    }
                })

                continue

            status = 'holding' if (sale_type == 'buy') else 'unknown'
            member_orders[name][ticker] = {
                'congress_id': tr.congress_id,
                'first_name': tr.first_name,
                'last_name': tr.last_name,
                'position': 'long',
                'ticker': ticker,
                'description': description,
                'shares': shares,
                'cost_share': pad,
                'latest_price': current_price,
                'market_value': amount,
                'gain_dollars': gaindollars,
                'gain_percent': gainPercent,
                'status': status,
                'orders': {
                    trx_date: {
                        'sale_type': sale_type,
                        'amount_low': amount_low,
                        'amount_high': amount_high,
                    }
                },
            }


# print(json.dumps(member_orders, indent=1))
"""
Calculate Gains
"""

tickers_to_check = []  # Collect tickers to send to API to get a current price.
for name, tickers in member_orders.items():
    for ticker, trx in tickers.items():
        if (trx.get("cost_share", False)):
            if (Stock.objects.filter(ticker=ticker).exists()):
                stock = Stock.objects.get(ticker=ticker)
                date_difference = abs((stock.updated_at.date() - date.today()).days)
                if (date_difference > 1):
                    tickers_to_check.append(ticker)

# Get current prices for tickers
if (tickers_to_check):
    uniq_tickers = list(set(tickers_to_check))
    ticker_prices = {}
    chunked_tickers = chunks(uniq_tickers, 100)

    for i, chunk in enumerate(chunked_tickers):
        batch = iex.get('quote', chunk)
        if (batch):
            for i, info in batch.items():
                quote = info.get('quote', False)
                if (quote and quote.get('companyName', False) and quote.get('latestPrice', False)):
                    Stock.objects.update_or_create(
                        ticker=quote['symbol'],
                        defaults={
                            'name': quote.get('companyName'),
                            'latestPrice': quote.get('latestPrice')
                        }
                    )
                    print(f"Saved {quote['symbol']} quote")

# Returns
 # TODO: Currently only calculates holding positions
member_gains = []
for name, tickers in member_orders.items():
    print(f"Calculating {name} gains")
    for ticker, trx in tickers.items():
        if (Stock.objects.filter(ticker=ticker).exists()):
            stock = Stock.objects.get(ticker=ticker)
            if (trx.get("cost_share", False) and trx["status"] != "unknown"):
                if (trx["status"] == "holding"):
                    trx["gain_dollars"] = calculateGainDollars(trx["shares"], trx["cost_share"], stock.latestPrice)
                    trx["gain_percent"] = calculateGainPercent(trx["shares"], trx["cost_share"], stock.latestPrice)

                    if (trx["gain_dollars"] and trx["gain_percent"]):
                        gains = {
                            "name": name,
                            "ticker": ticker,
                            "dates_bought": [date for date, order in trx["orders"].items()],
                            "status": "holding",
                            "gain_dollars": trx["gain_dollars"],
                            "gain_percent": trx["gain_percent"],
                        }
                        member_gains.append(gains)

print("Writing CSV")
writeCSV(member_gains, output='storage/congress_gains.csv')