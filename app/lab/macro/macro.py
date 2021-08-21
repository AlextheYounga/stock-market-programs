import django
from dotenv import load_dotenv
from app.lab.core.api.iex import IEX
from app.lab.fintwit.fintwit import Fintwit
from app.functions import chunks
import progressbar
import redis
from app.lab.core.output import printTable
import progressbar
import json
import time
import sys
django.setup()
load_dotenv()

class Macro():        
    def scanETFs(self):
        from app.database.models import Stock
        results = {}
        iex = IEX()        
        etfs = Stock().getETFs()
        chunked_etfs = chunks(etfs, 100)
        chunks_length = int(len(etfs) / 100)

        with progressbar.ProgressBar(max_value=chunks_length, prefix='Batch: ', redirect_stdout=True) as bar:
            for i, chunk in enumerate(chunked_etfs):
                bar.update(i)
                time.sleep(1)
                batch = iex.get('quote', chunk)

                for ticker, fundInfo in batch.items():
                    Stock().store(fundInfo.get('quote'), ticker)
                    results.update({ticker: fundInfo})
        
        return results


    def gainers(self, print_results= False, tweet=False):
        results = []
        etfs = self.scanETFs()
        for ticker, etf in etfs.items():
           if (etf.get('quote', False) and etf.get('stats', False)):
                quote = etf.get('quote')
                stats = etf.get('stats')
                price = quote.get('latestPrice', 0)

                if ((price) and (isinstance(price, float)) and (price > 10)):
                    day5ChangePercent = stats.get('day5ChangePercent', 0) * 100                               
                    volume = quote.get('volume', 0)
                    avg30Volume = stats.get('avg30Volume', 0)
                    week52high = stats.get('week52high', 0)
                    month3ChangePercent = stats.get('ytdChangePercent', 0) * 100
                    day50MovingAvg = stats.get('day50MovingAvg', 0)
                    ytdChangePercent = stats.get('ytdChangePercent', 0) * 100
                    # previousVolume = quote.get('previousVolume', 0)
                    
                    # Critical
                    changeToday = quote.get('changePercent', 0) * 100
                    month1ChangePercent = stats.get('month1ChangePercent', 0) * 100

                    if ((0 in [changeToday, month1ChangePercent])):
                        continue

                    fromHigh = round((price / week52high) * 100, 3)

                    if ((changeToday > 5) and (volume > avg30Volume)):
                        keyStats = {
                            'name': quote['companyName'],
                            'price': price,
                            'week52': stats['week52high'],
                            'day5ChangePercent': day5ChangePercent,
                            'ytdChangePercent': ytdChangePercent,                            
                            'avg30Volume': "{}K".format(round(avg30Volume / 1000, 3)),
                            'month1ChangePercent': month1ChangePercent,
                            'month3ChangePercent': month3ChangePercent,
                            'day50MovingAvg': day50MovingAvg,
                            'day200MovingAvg': stats['day200MovingAvg'],
                            'fromHigh': fromHigh,
                        }

                        stockData = { 'ticker': ticker }
                        stockData.update(keyStats)

                        stockData['volume'] = "{}K".format(volume / 1000)
                        stockData['changeToday'] = changeToday
                        results.append(stockData)

        if (print_results):
            printTable(results, struct='dictlist')
        if (tweet):
            self.sendtweet(results)
        return
    

    def trends(self, timeframe='1m', gain=20, print_results=False, tweet=False):
        results = []
        etfs = self.scanETFs()
        for ticker, etf in etfs.items():
            if (etf.get('quote', False) and etf.get('stats', False)):
                quote = etf.get('quote')
                stats = etf.get('stats')
                price = quote.get('latestPrice', 0)

                if ((price) and (isinstance(price, float)) and (price > 10)):

                    changeToday = quote.get('changePercent', 0) * 100
                    volume = quote.get('volume', 0)
                    avg30Volume = stats.get('avg30Volume', 0)
                    day50MovingAvg = stats.get('day50MovingAvg', 0)

                    # Critical
                    week52high = stats.get('week52high', 0)
                    day5ChangePercent = stats.get('day5ChangePercent', 0) * 100
                    month3ChangePercent = stats.get('ytdChangePercent', 0) * 100
                    ytdChangePercent = stats.get('ytdChangePercent', 0) * 100
                    month1ChangePercent = stats.get('month1ChangePercent', 0) * 100

                    if (0 in [month3ChangePercent, ytdChangePercent, month1ChangePercent, week52high]):
                        continue

                    fromHigh = round((price / week52high) * 100, 3)

                    frames = {
                        '5d': day5ChangePercent,
                        '1m': month1ChangePercent,
                        '3m': month3ChangePercent,
                        '1y': ytdChangePercent,
                    }
                    deltaT = frames[timeframe]

                    if (float(deltaT) > float(gain)):
                        keyStats = {
                            'week52': week52high,
                            'day5ChangePercent': day5ChangePercent,
                            'ytdChangePercent': ytdChangePercent,
                            'avg30Volume': "{}K".format(round(avg30Volume / 1000, 3)),
                            'month1ChangePercent': month1ChangePercent,
                            'month3ChangePercent': month3ChangePercent,
                            'day50MovingAvg': day50MovingAvg,
                            'day200MovingAvg': stats.get('day200MovingAvg', None),
                            'fromHigh': fromHigh,
                        }

                        stockData = {
                            'ticker': ticker,
                            'name': quote['companyName'],
                            'lastPrice': price
                        }
                        stockData.update(keyStats)

                        stockData['volume'] = "{}K".format(volume / 1000)
                        stockData['changeToday'] = changeToday
                        results.append(stockData)

        if (print_results):
            printTable(results, struct='dictlist')
        if (tweet):
            self.sendtweet(results)
        return

    def sendtweet(self, results):
        twit = Fintwit()
        tweet = ""
        for etf in results:
            txt = "${} +{}%\n".format(etf['ticker'], round(etf['changeToday'], 2))
            tweet = tweet + txt
        twit.send_tweet(tweet, True)

m = Macro()
m.scanETFs()