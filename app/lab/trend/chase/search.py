import django
from dotenv import load_dotenv
import json
import sys
from datetime import date
from app.functions import chunks, dataSanityCheck
from app.lab.core.api.iex import IEX
from app.lab.core.output import printFullTable, writeCSV
from ...fintwit.tweet import send
load_dotenv()
django.setup()
from app.database.models import Stock

iex = IEX()

print('Running...')


def search(string):
    print('Searching '+string)
    if (string):
        results = []
        stocks = Stock.objects.all()
        tickers = []

        for stock in stocks:
            if (string in stock.name):
                tickers.append(stock.ticker)

        chunked_tickers = chunks(tickers, 100)

        for i, chunk in enumerate(chunked_tickers):
            batch = iex.get('stats', chunk)

            for ticker, stockinfo in batch.items():
                if (stockinfo.get('quote', False) and stockinfo.get('stats', False)):
                    quote = stockinfo.get('quote')
                    stats = stockinfo.get('stats')
                    price = quote.get('latestPrice', 0)

                    if (price and isinstance(price, float)):
                        stock, created = Stock.objects.update_or_create(
                            ticker=ticker,
                            defaults={'lastPrice': price},
                        )
                    else:
                        continue

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

                    if (changeToday > 12):
                        if (volume > previousVolume):
                            priceTargets = iex.get('price-target', ticker)
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
                                'name': stock.name,
                                'lastPrice': price
                            }
                            stockData.update(keyStats)

                            stockData['changeToday'] = changeToday
                            print('{} saved to Watchlist'.format(ticker))
                            results.append(stockData)

        if results:
            today = date.today().strftime('%m-%d')
            writeCSV(results, 'app/lab/trend/output/chase/trend_chasing_{}.csv'.format(today))

            printFullTable(results, struct='dictlist')

            # Tweet
            tweet = ""
            for i, data in enumerate(results):
                ticker = '${}'.format(data['ticker'])
                changeToday = data['changeToday']
                tweet_data = "{} +{}% \n".format(ticker, changeToday)
                tweet = tweet + tweet_data

            send(tweet, True)
