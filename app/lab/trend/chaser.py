import django
from django.apps import apps
from dotenv import load_dotenv
import json
import sys
import progressbar
from datetime import date
import time
import redis
from app.functions import chunks, dataSanityCheck
from app.lab.core.api.iex import IEX
# from app.lab.core.api.stats import getPriceTarget
# from app.lab.core.api.batch import quoteStatsBatchRequest
from app.lab.core.output import printTable, printFullTable, writeCSV
from app.lab.fintwit.fintwit import Fintwit
load_dotenv()
django.setup()
class Chaser():
    def __init__(self):
        self.api = IEX()

    def scan(self):
        print('Scanning...')
        
        Stock = apps.get_model('database', 'Stock')
        tickers = Stock.objects.all().values_list('ticker', flat=True)
        results = {}        

        chunked_tickers = chunks(tickers, 100)
        chunks_length = int(len(tickers) / 100)

        with progressbar.ProgressBar(max_value=chunks_length, prefix='Batch: ', redirect_stdout=True) as bar:
            for i, chunk in enumerate(chunked_tickers):

                bar.update(i)
                time.sleep(1)
                batch = self.api.get('stats', chunk)
                for ticker, stockinfo in batch.items():
                    results.update({ticker: stockinfo})
        return results

    
    def run(self, pennyStocks=False, tweet=False, printResults=False):
        results = []
        stocks = self.scan()
        for ticker, stockinfo in stocks.items():
            if (stockinfo.get('quote', False) and stockinfo.get('stats', False)):
                quote = stockinfo.get('quote')
                stats = stockinfo.get('stats')
                price = quote.get('latestPrice', 0)

                if (price and isinstance(price, float)):
                    ttmEPS = stats.get('ttmEPS', None)
                    day5ChangePercent = round(dataSanityCheck(stats, 'day5ChangePercent') * 100, 2)
                    month1ChangePercent = round(dataSanityCheck(stats, 'month1ChangePercent') * 100, 2)
                    ytdChangePercent = round(dataSanityCheck(stats, 'ytdChangePercent') * 100, 2)

                    # Critical
                    week52high = dataSanityCheck(stats, 'week52high')
                    changeToday = round(dataSanityCheck(quote, 'changePercent') * 100, 2)
                    volume = dataSanityCheck(quote, 'volume')
                    previousVolume = dataSanityCheck(quote, 'previousVolume')

                    critical = [changeToday, week52high, volume, previousVolume]

                    if ((0 in critical)):
                        continue

                    fromHigh = round((price / week52high) * 100, 3)

                    # Save Data to DB
                    keyStats = {
                        'peRatio': stats.get('peRatio', None),
                        'week52': week52high,
                        'day5ChangePercent': day5ChangePercent if day5ChangePercent else None,
                        'month1ChangePercent': month1ChangePercent if month1ChangePercent else None,
                        'ytdChangePercent': ytdChangePercent if ytdChangePercent else None,
                        'day50MovingAvg': stats.get('day50MovingAvg', None),
                        'day200MovingAvg': stats.get('day200MovingAvg', None),
                        'fromHigh': fromHigh,
                        'ttmEPS': ttmEPS
                    }

                    rnge = (price > 5)
                    if (pennyStocks):
                        rnge = ((price > 0.5) and (price < 5))
                    if (rnge):
                        if ((fromHigh < 105) and (fromHigh > 95)):
                            if (changeToday > 15):
                                if (volume > previousVolume):
                                    priceTargets = self.api.get('price-target', ticker)
                                    fromPriceTarget = round((price / priceTargets['priceTargetHigh']) * 100, 3) if (dataSanityCheck(priceTargets, 'priceTargetHigh')) else 0
                                    avgPricetarget = priceTargets['priceTargetAverage'] if (dataSanityCheck(priceTargets, 'priceTargetAverage')) else None
                                    highPriceTarget = priceTargets['priceTargetHigh'] if (dataSanityCheck(priceTargets, 'priceTargetHigh')) else None

                                    # Save Trends to DB
                                    trend_data = {
                                        'avgPricetarget': avgPricetarget,
                                        'highPriceTarget': highPriceTarget,
                                        'fromPriceTarget': fromPriceTarget,
                                    }

                                    keyStats.update({
                                        'highPriceTarget': highPriceTarget,
                                        'fromPriceTarget': fromPriceTarget,
                                    })

                                    stockData = {
                                        'ticker': ticker,
                                        'name': quote['companyName'],
                                        'lastPrice': price
                                    }
                                    stockData.update(keyStats)


                                    stockData['changeToday'] = changeToday
                                    print('{} saved to Watchlist'.format(ticker))

                                    # Removing from terminal output
                                    del stockData['day50MovingAvg']
                                    del stockData['day200MovingAvg']

                                    results.append(stockData)
        if (tweet):
            # Tweet
            twit = Fintwit()
            tweet = ""
            for i, data in enumerate(results):
                ticker = '${}'.format(data['ticker'])
                changeToday = data['changeToday']
                tweet_data = "{} +{}% \n".format(ticker, changeToday)
                tweet = tweet + tweet_data

            twit.send_tweet(tweet, True)

        if (printResults):
            printFullTable(results, struct='dictlist')

        return results
