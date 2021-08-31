
from app.lab.core.output import printFullTable
import statistics
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
from app.lab.core.api.senatewatcher import SenateWatcher


class PortfolioBuilder():

    def calculateShares(self, pad, amount):
        if (pad and amount):
            return int(amount / pad)

        return None

    def latest_price(self, ticker):
        if (ticker):
            stock = Stock.objects.filter(ticker=ticker).first()
            if (stock):
                return stock.latestPrice
        return None

    def calculateGainDollars(self, shares, cost, price):
        if (shares and cost and price):
            return int((shares * price) - (shares * cost))
        return None

    def calculateGainPercent(self, shares, cost, price):
        if (shares and cost and price):
            startval = (shares * cost)
            currentval = (shares * price)

            percentChange = ((currentval - startval) / startval) * 100
            return round(percentChange, 2)

        return None

    def determineStatus(self, marketval):
        if (marketval == 0):
            return 'sold'
        elif (marketval < 0):
            return 'unknown'
        else:
            return 'holding'


    def build(self):
        members = Congress.objects.all()
        for member in members:
            portfolio = {}
            transactions = member.congresstransaction_set.all().order_by('date')
            for tr in transactions:
                if (tr.ticker):
                    date = (tr.date or tr.filing_date).strftime('%Y-%m-%d')
                    ticker = tr.ticker
                    description = tr.description
                    amount_low = tr.amount_low
                    amount_high = tr.amount_high
                    amount = int(statistics.mean([amount_low, amount_high])) if (amount_low and amount_high) else (amount_low or amount_high)
                    pad = tr.price_at_date
                    sale_type = tr.sale_type
                    shares = self.calculateShares(pad, amount)
                    current_price = self.latest_price(ticker)
                    gaindollars = self.calculateGainDollars(shares, pad, pad)
                    gainPercent = self.calculateGainPercent(shares, pad, pad)

                    if ((ticker) in portfolio):
                        pf = portfolio[ticker]
                        if (sale_type == 'partial-sell'):
                            mkval = (pf['market_value'] - amount) if (pf.get('market_value', False) and amount) else pf['market_value']
                            pf['market_value'] = mkval
                            pf['shares'] = (pf['shares'] - shares) if (pf.get('shares', False) and shares) else pf['shares']
                            pf['status'] = self.determineStatus(mkval)

                        if (sale_type == 'sell'):
                            mkval = (pf['market_value'] - amount) if (pf.get('market_value', False) and amount) else pf['market_value']
                            pf['market_value'] = mkval
                            pf['shares'] = (pf['shares'] - shares) if (pf.get('shares', False) and shares) else pf['shares']
                            pf['status'] = self.determineStatus(mkval)
                            
                        if (sale_type == 'buy'):
                            mkval = (pf['market_value'] + amount) if (pf.get('market_value', False) and amount) else pf['market_value']
                            pf['market_value'] = mkval
                            pf['cost_share'] = round(statistics.mean([pf['cost_share'], pad]), 2) if (pad and pf.get('cost_share', False)) else pf['cost_share']
                            pf['shares'] = (pf['shares'] + shares) if (pf.get('shares', False) and shares) else pf['shares']
                            pf['status'] = self.determineStatus(mkval)

                        if (pf['market_value'] < 0):
                            pf['market_value'] = 0
                        
                        if (pf['status'] == 'holding'):
                            pf['gain_dollars'] = self.calculateGainDollars(pf['shares'], pf['cost_share'], current_price)
                            pf['gain_dollars'] = self.calculateGainPercent(pf['shares'], pf['cost_share'], current_price)
                        
                        if (pf['status'] == 'sold'):
                            pf['gain_dollars'] = self.calculateGainDollars(pf['shares'], pf['cost_share'], pad)
                            pf['gain_dollars'] = self.calculateGainPercent(pf['shares'], pf['cost_share'], pad)

                        if (pf['status'] == 'unknown'):
                            pf['gain_dollars'] = None
                            pf['gain_dollars'] = None                                            

                        pf['orders'].update({
                            date: {
                                'sale_type': sale_type,
                                'amount_low': amount_low,
                                'amount_high': amount_high,
                            }
                        })

                        continue

                    status = 'holding' if (sale_type == 'buy') else 'unknown'
                    portfolio[ticker] = {
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
                            date: {
                                'sale_type': sale_type,
                                'amount_low': amount_low,
                                'amount_high': amount_high,
                            }
                        },
                    }            
            self.store(portfolio)

    def calculateGains(self):
        members = Congress.objects.all()
        marketval = []
        gaindollars = []
        for member in members:
            trades = member.congressportfolio_set.all()
            for trade in trades:
                gaindollars.append(trade.gain_dollars)
                marketval.append(trade.market_value)

            total_gain_dollars = sum(filterNone(gaindollars))
            total_gain_pct = round((total_gain_dollars / sum(filterNone(marketval))) * 100, 2)
            member.total_gain_dollars = total_gain_dollars
            member.total_gain_percent = total_gain_pct
            member.trades = len(trades)
            member.save()
            print(stylize(f"saved {member.name} gains", colored.fg("green")))

    def store(self, portfolio):
        for ticker, data in portfolio.items():
            CongressPortfolio().store(data)
            print(stylize(f"saved {ticker} {data['last_name']}", colored.fg("green")))


# pb = PortfolioBuilder()
# pb.build()
