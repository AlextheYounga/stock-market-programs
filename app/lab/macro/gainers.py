from dotenv import load_dotenv
from .functions import getETFs
from app.lab.fintwit.tweet import send_tweet
from app.lab.core.functions import chunks
from app.lab.core.api.batch import quoteStatsBatchRequest
from app.lab.core.output import printFullTable
from ..redisdb.controller import rdb_save_stock
from ..redisdb.controller import rdb_save_output
import progressbar
import json
import time
import sys
from datetime import date
load_dotenv()



print('Scanning sectors...')
results = []
etfs = getETFs(True)
chunked_etfs = chunks(etfs, 100)
chunks_length = int(len(etfs) / 100)
saved = 0
failed = 0


with progressbar.ProgressBar(max_value=chunks_length, prefix='Batch: ', redirect_stdout=True) as bar:
    for i, chunk in enumerate(chunked_etfs):
        bar.update(i)
        time.sleep(1)
        batch = quoteStatsBatchRequest(chunk)

        for ticker, stockinfo in batch.items():

            if (stockinfo.get('quote', False) and stockinfo.get('stats', False)):
                quote = stockinfo.get('quote')
                stats = stockinfo.get('stats')
                price = quote.get('latestPrice', 0)

                if ((price) and (isinstance(price, float)) and (price > 10)):


                    day5ChangePercent = stats['day5ChangePercent'] * 100 if ('day5ChangePercent' in stats and stats['day5ChangePercent']) else None            
                    previousVolume = quote['previousVolume'] if ('previousVolume' in quote and quote['previousVolume']) else 0            
                    volume = quote['volume'] if ('volume' in quote and quote['volume']) else 0
                    avg30Volume = stats['avg30Volume'] if ('avg30Volume' in stats and stats['avg30Volume']) else None
                    week52high = stats['week52high'] if ('week52high' in stats and stats['week52high']) else 0
                    month3ChangePercent = stats['month3ChangePercent'] * 100 if ('month3ChangePercent' in stats and stats['month3ChangePercent']) else None
                    day50MovingAvg = stats['day50MovingAvg'] if ('day50MovingAvg' in stats and stats['day50MovingAvg']) else None            
                    ytdChangePercent = stats['ytdChangePercent'] * 100 if ('ytdChangePercent' in stats and stats['ytdChangePercent']) else 0
                    
                    # Critical
                    changeToday = quote['changePercent'] * 100 if ('changePercent' in quote and quote['changePercent']) else 0
                    month1ChangePercent = stats['month1ChangePercent'] * 100 if ('month1ChangePercent' in stats and stats['month1ChangePercent']) else 0
            
                    critical = [changeToday, month1ChangePercent]

                    if ((0 in critical)):
                        continue

                    fromHigh = round((price / week52high) * 100, 3)

                    if (changeToday > 5):
                        if (volume > avg30Volume):
                            keyStats = {
                                'name': quote['companyName'],
                                'price': price,
                                'week52': stats['week52high'],
                                'day5ChangePercent': stats['day5ChangePercent'],
                                'month3ChangePercent': stats['month3ChangePercent'],
                                'ytdChangePercent': ytdChangePercent,                            
                                'avg30Volume': "{}K".format(round(avg30Volume / 1000, 3)),
                                'month1ChangePercent': month1ChangePercent,
                                'month3ChangePercent': month3ChangePercent,
                                'day50MovingAvg': day50MovingAvg,
                                'day200MovingAvg': stats['day200MovingAvg'],
                                'fromHigh': fromHigh,
                            }
                            
                            try:
                                rdb_save_stock(ticker, keyStats)
                                saved = (saved + 1)
                            except:
                                failed = (failed + 1)

                            stockData = {
                                'ticker': ticker,                        
                            }
                            stockData.update(keyStats)

                            stockData['volume'] = "{}K".format(volume / 1000)
                            stockData['changeToday'] = changeToday
                            results.append(stockData)

if results:
    print('Saved: '+str(saved))
    print('Did not Save: '+str(failed))
    today = date.today().strftime('%m-%d')
    rdb_save_output(results)
    printFullTable(results, struct='dictlist')

    tweet = ""
    for etf in results:
        txt = "${} +{}%\n".format(etf['ticker'], round(etf['changeToday'], 2))
        tweet = tweet + txt
    send_tweet(tweet, True)
