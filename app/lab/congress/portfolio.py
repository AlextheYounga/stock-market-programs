
from app.lab.core.output import printFullTable
import statistics
import sys
import os
import json
import django
from dotenv import load_dotenv
load_dotenv()
django.setup()
from app.database.models import Congress, CongressTransaction, Stock
from app.lab.core.api.senatewatcher import SenateWatcher

class CongressPortfolio():

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
        return 0

    def calculateGainPercent(self, shares, cost, price):
        if (shares and cost and price):
            startval = (shares * cost)
            currentval = (shares * price)

            percentChange = ((currentval - startval) / startval) * 100
            return round(percentChange, 2)

        return 0

    def calculateAvgCostShare():
        """"""

    def calculate(self):
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
                    # gaindollars = self.calculateGainDollars(shares, pad, current_price)
                    # gainPercent = self.calculateGainPercent(shares, pad, current_price)

                    if ((ticker) in portfolio):
                        pf = portfolio[ticker]
                        if (sale_type == 'partial-sell'):
                            mkval = (pf['market_value'] - amount) if (pf['market_value'] and amount) else pf['market_value']
                            pf['market_value'] = mkval
                            pf['shares'] = (pf['shares'] - shares) if(pf['shares'] and shares) else pf['shares']
                            pf['status'] = 'holding'
                        if (sale_type == 'buy'):
                            mkval = (pf['market_value'] + amount) if (pf['market_value'] and amount) else pf['market_value']
                            pf['market_value'] = mkval
                            pf['shares'] = (pf['shares'] + shares) if (pf['shares'] and shares) else pf['shares']
                            pf['status'] = 'holding'
                        if (sale_type == 'sell'):
                            pf['market_value'] = 0
                            pf['shares'] = 0
                            pf['status'] = 'sold'

                        pf['orders'].update({
                            date: {
                                'sale_type': sale_type,
                                'amount_low': amount_low,
                                'amount_high': amount_high,
                            }
                        })

                        continue

                    status = 'holding' if (sale_type == 'buy') else 'sold'
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
                        # 'gain_dollars': gaindollars,
                        # 'gain_percent': gainPercent,
                        'status': status,
                        'orders': {
                            date: {
                                'sale_type': sale_type,
                                'amount_low': amount_low,
                                'amount_high': amount_high,
                            }
                        },
                    }            
            print(json.dumps(portfolio, indent=1))
            sys.exit()

cp = CongressPortfolio()
cp.calculate()
