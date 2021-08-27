from app.functions import chunks
from app.lab.core.api.iex import IEX
import django
from dotenv import load_dotenv
load_dotenv()
django.setup()
from app.database.models import Stock


iex = IEX()
stocks = iex.syncStocks()
tickers = [stock['symbol'] for stock in stocks]
chunked_tickers = chunks(tickers, 100)


for i, chunk in enumerate(chunked_tickers):
    batch = iex.get('quote', chunk)

    for i, info in batch.items():
        quote = info['quote'] if ('quote' in info) and info['quote'] else False

        if (quote):
            if (quote.get('companyName', False)):
                Stock.objects.update_or_create(
                    ticker=quote['symbol'],
                    defaults={
                        'name': quote.get('companyName'),
                        'latestPrice': quote.get('latestPrice')
                    }
                )
                print('saved {}'.format(quote['symbol']))
