from dotenv import load_dotenv
import json
import sys
import progressbar
import time
from datetime import date
from app.functions import chunks, dataSanityCheck
from app.lab.core.api.historical import batchHistoricalData
from app.lab.core.output import printFullTable, writeCSV
import django
load_dotenv()
django.setup()

Stock = apps.get_model('database', 'Stock')
Watchlist = apps.get_model('database', 'Watchlist')

print('Running...')

results = []
tickers = Stock.objects.all().values_list('ticker', flat=True)

chunked_tickers = chunks(tickers, 100)
chunks_length = int(len(tickers) / 100)
with progressbar.ProgressBar(max_value=chunks_length, prefix='Batch: ', redirect_stdout=True) as bar:
    for i, chunk in enumerate(chunked_tickers):
        bar.update(i)
        time.sleep(1)
        batch = batchHistoricalData(chunk, '5d', priceOnly=True)

        for ticker, info in batch.items():
            if (info.get('chart', False)):
                chart = info['chart']
                price = chart[-1].get('close', 0)
                priceFirst = chart[0].get('close', 0)
                volumeFirst = round(dataSanityCheck(chart[0], 'volume'), 2)
                volumeToday = round(dataSanityCheck(chart[-1], 'volume'), 2)
                changeToday = round(dataSanityCheck(chart[-1], 'changePercent'), 2)
                changePercent5d = round((priceFirst - price) / priceFirst)

                if ((price) and (isinstance(price, float))):

                    if (0 in [volumeFirst, volumeToday, changeToday]):
                        continue

                    for vol in [volumeFirst, volumeToday]:
                        if ((vol / 1000) < 1):
                            continue

                    if ((volumeToday / volumeFirst) > 50):
                        stockData = {
                            'ticker': ticker,
                            'lastPrice': price,
                            'volumeToday': "{}K".format(round(volumeToday / 1000, 4)),
                            'volume5dAgo': "{}K".format(round(volumeFirst / 1000, 4)),
                            'volumeIncrease': round(volumeToday / volumeFirst),
                            'changeToday': "{}%".format(round((changeToday * 100), 2)),
                            '5dPercentChange': "{}%".format(round(((price - priceFirst) / priceFirst) * 100, 2))
                        }
                        results.append(stockData)


if results:
    printFullTable(results, struct='dictlist')

    today = date.today().strftime('%m-%d')
    writeCSV(results, 'app/lab/volume/output/anomalies/anomalies{}.csv'.format(today))
