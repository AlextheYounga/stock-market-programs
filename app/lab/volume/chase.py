import django
from django.apps import apps
from dotenv import load_dotenv
import json
import sys
import progressbar
import redis
import time
from datetime import date
from ..redisdb.controller import rdb_save_stock
from ..core.functions import chunks, dataSanityCheck
from ..core.api.batch import quoteStatsBatchRequest
from ..core.api.stats import getPriceTarget
from ..core.output import printFullTable, writeCSV
from ..fintwit.tweet import send_tweet
load_dotenv()
django.setup()

Stock = apps.get_model('database', 'Stock')
Watchlist = apps.get_model('database', 'Watchlist')

rdb = True
stocksaved = 0
wlsaved = 0


print('Running...')

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

                if ((price) and (isinstance(price, float)) and (price > 10)):

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

                    if ((fromHigh < 100) and (fromHigh > 80)):
                        if (changeToday > 5):
                            if ((volume / previousVolume) > 3):
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

                                stockData['volume'] = "{}K".format(round(volume / 1000, 2))
                                stockData['previousVolume'] = "{}K".format(round(previousVolume / 1000, 2))
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
    # writeCSV(results, 'lab/trend/output/volume/trend_chasing_{}.csv'.format(today))

    printFullTable(results, struct='dictlist')

    # Tweet
    tweet = ""
    for i, data in enumerate(results):
        ticker = '${}'.format(data['ticker'])
        previousVolume = data['previousVolume']
        volume = data['volume']
        tweet_data = "{} previous: {}, today: {} \n".format(ticker, previousVolume, volume)
        tweet = tweet + tweet_data

    send_tweet(tweet, True)
