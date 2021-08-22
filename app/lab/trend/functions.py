import django
from app.lab.core.api.iex import IEX
import colored
from colored import stylize
import redis
import json
import sys
from dotenv import load_dotenv
load_dotenv()
django.setup()
from app.database.models import Stock


def checkEarnings(earnings):
    actual = []
    consensus = []
    consistency = []

    if (len(earnings['earnings']) > 1):
        for i, report in enumerate(earnings['earnings']):
            actualEps = report['actualEPS'] if 'actualEPS' in report else 0
            surpriseEps = report['EPSSurpriseDollar'] if 'EPSSurpriseDollar' in report else 0
            if (i + 1 in range(-len(earnings['earnings']), len(earnings['earnings']))):
                previous = earnings['earnings'][i + 1]['actualEPS']
                greater = actualEps > previous
                consistency.append(greater)

            period = report['fiscalPeriod'] if 'fiscalPeriod' in report else i
            actual.append({period: actualEps})
            consensus.append({period: surpriseEps})

        improvement = False if False in consistency else True

        results = {
            'actual': actual,
            'consensus': consensus,
            'improvement': improvement,
        }

        return results


def getPennyStocks(tickersOnly=True, refresh_prices=False):
    iex = IEX()
    if (refresh_prices):
        print(stylize("Syncing prices...", colored.fg("yellow")))
        iex.syncPrices()

    stocks = Stock.objects.all()
    r = redis.Redis(host='localhost', port=6379, db=0, charset="utf-8", decode_responses=True)
    pennystocks = []

    for stock in stocks:
        price = r.get('stock-'+stock.ticker+'-price')
        if (price):
            if (float(price) < 4):
                if (tickersOnly):
                    pennystocks.append(stock.ticker)
                else:
                    pennystocks.append(stock)

    return pennystocks
