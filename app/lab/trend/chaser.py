import django
from django.apps import apps
from dotenv import load_dotenv
import json
import sys
import progressbar
from datetime import date
import time
import redis
from ..redisdb.controller import rdb_save_stock
from app.lab.core.functions import chunks, dataSanityCheck
from app.lab.core.api.stats import getPriceTarget
from app.lab.core.api.batch import quoteStatsBatchRequest
from app.lab.core.output import printTable, printFullTable, writeCSV
from app.lab.fintwit.tweet import send_tweet
load_dotenv()
django.setup()


def chase_trends(pennies=False):
    print('Running...')

    Stock = apps.get_model('database', 'Stock')
    Watchlist = apps.get_model('database', 'Watchlist')
    rdb = True
    stocksaved = 0
    wlsaved = 0
    results = []
    tickers = Stock.objects.all().values_list('ticker', flat=True)

    chunked_tickers = chunks(tickers, 100)
    chunks_length = int(len(tickers) / 100)

    with progressbar.ProgressBar(max_value=chunks_length, prefix='Batch: ', redirect_stdout=True) as bar:
        for i, chunk in enumerate(chunked_tickers):

            bar.update(i)
            time.sleep(1)
            batch = quoteStatsBatchRequest(chunk)
            
            for ticker, stockinfo in batch.items():

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

                        if (rdb == True):
                            try:
                                rdb_save_stock(ticker, keyStats)
                                stocksaved += 1
                            except redis.exceptions.ConnectionError:
                                rdb = False
                                print('Redis not connected. Not saving.')

                        rnge = (price > 5)
                        if (pennies):
                            rnge = ((price > 0.5) and (price < 5))
                        if (rnge):
                            if ((fromHigh < 105) and (fromHigh > 95)):
                                if (changeToday > 15):
                                    if (volume > previousVolume):
                                        priceTargets = getPriceTarget(ticker)
                                        fromPriceTarget = round((price / priceTargets['priceTargetHigh']) * 100, 3) if (dataSanityCheck(priceTargets, 'priceTargetHigh')) else 0
                                        avgPricetarget = priceTargets['priceTargetAverage'] if (dataSanityCheck(priceTargets, 'priceTargetAverage')) else None
                                        highPriceTarget = priceTargets['priceTargetHigh'] if (dataSanityCheck(priceTargets, 'priceTargetHigh')) else None

                                        # Save Trends to DB
                                        trend_data = {
                                            'avgPricetarget': avgPricetarget,
                                            'highPriceTarget': highPriceTarget,
                                            'fromPriceTarget': fromPriceTarget,
                                        }

                                        if (rdb == True):
                                            rdb_save_stock(ticker, trend_data)

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

                                        # Save to Watchlist
                                        Watchlist.objects.update_or_create(
                                            ticker=ticker,
                                            defaults=stockData
                                        )

                                        wlsaved += 1

                                        stockData['changeToday'] = changeToday
                                        print('{} saved to Watchlist'.format(ticker))

                                        # Removing from terminal output
                                        del stockData['day50MovingAvg']
                                        del stockData['day200MovingAvg']

                                        results.append(stockData)

    if results:
        print('Total scanned: '+str(len(tickers)))
        print('Stocks saved: '+str(stocksaved))
        print('Saved to Watchlist: '+str(wlsaved))

        # today = date.today().strftime('%m-%d')
        # writeCSV(results, 'app/lab/trend/output/chase/trend_chasing_{}.csv'.format(today))

        printFullTable(results, struct='dictlist')

        # Tweet
        tweet = ""
        for i, data in enumerate(results):
            ticker = '${}'.format(data['ticker'])
            changeToday = data['changeToday']
            tweet_data = "{} +{}% \n".format(ticker, changeToday)
            tweet = tweet + tweet_data

        send_tweet(tweet, True)
