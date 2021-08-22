import django
from dotenv import load_dotenv
import json
import time
import sys
import progressbar
from ..functions import *
from app.functions import chunks, dataSanityCheck
from app.lab.core.api.iex import IEX
from app.lab.core.output import printFullTable
from app.lab.fintwit.tweet import Tweet
load_dotenv()
django.setup()
from app.database.models import Stock

iex = IEX()
tweet = Tweet()
"""
This function doesn't get much love anymore because nobody cares about earnings anymore.
"""
print('Running...')

results = []
tickers = Stock.objects.all().values_list('ticker', flat=True)
rdb = True
stocksaved = 0
wlsaved = 0

chunked_tickers = chunks(tickers, 100)
chunks_length = int(len(tickers) / 100)

with progressbar.ProgressBar(max_value=chunks_length, prefix='Batch: ', redirect_stdout=True) as bar:
    for i, chunk in enumerate(chunked_tickers):

        bar.update(i)
        time.sleep(1)
        batch = iex.get('stats', chunk)

        for ticker, stockinfo in batch.items():

            if (stockinfo.get('quote', False) and stockinfo.get('stats', False)):
                quote = stockinfo.get('quote')
                stats = stockinfo.get('stats')

                price = quote.get('latestPrice', 0)

                if (price and isinstance(price, float)):
                    month1ChangePercent = round(dataSanityCheck(stats, 'month1ChangePercent') * 100, 2)
                    ytdChangePercent = round(dataSanityCheck(stats, 'ytdChangePercent') * 100, 2)

                    # Critical
                    ttmEPS = dataSanityCheck(stats, 'ttmEPS')
                    week52high = dataSanityCheck(stats, 'week52high')
                    changeToday = round(dataSanityCheck(quote, 'changePercent') * 100, 2)
                    day5ChangePercent = round(dataSanityCheck(stats, 'day5ChangePercent') * 100, 2)
                    critical = [changeToday, week52high, ttmEPS, day5ChangePercent]

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
                        'ttmEPS': ttmEPS,
                    }

                    if ((fromHigh < 105) and (fromHigh > 95)):
                        if (changeToday > 10):
                            earningsData = iex.getChart(ticker, endpoint='earnings')
                            if (earningsData and isinstance(earningsData, dict)):
                                earningsChecked = checkEarnings(earningsData)
                                if (isinstance(earningsChecked, dict) and earningsChecked['actual'] and earningsChecked['consensus']):
                                    # Save Earnings to DB
                                    if (earningsChecked['improvement'] == True):

                                        keyStats.update({
                                            'reportedEPS': earningsChecked['actual'],
                                            'reportedConsensus': earningsChecked['consensus'],
                                        })
                                        stockData = {
                                            'ticker': ticker,
                                            'name': quote['companyName'],
                                            'lastPrice': price
                                        }
                                        stockData.update(keyStats)

                                        wlsaved += 1

                                        print('{} saved to Watchlist'.format(ticker))
                                        results.append(stockData)

if results:
    print('Total scanned: '+str(len(tickers)))
    print('Stocks saved: '+str(stocksaved))
    print('Saved to Watchlist: '+str(wlsaved))

    # today = date.today().strftime('%m-%d')
    # writeCSV(results, 'app/lab/trend/output/earnings/trend_chasing_{}.csv'.format(today))

    printFullTable(results, struct='dictlist')

    # Tweet
    tweet = ""
    for i, data in enumerate(results):
        ticker = '${}'.format(data['ticker'])
        ttmEPS = data['ttmEPS']
        day5ChangePercent = data['day5ChangePercent']
        tweet_data = "{} ttmEPS: {}, 5dayChange: {} \n".format(ticker, ttmEPS, day5ChangePercent)
        tweet = tweet + tweet_data

    tweet.send(tweet, True)
