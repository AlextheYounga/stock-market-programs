import sys
import json
from app.functions import chunks
from app.lab.reddit.api_scraper import scrapeWSB
import django
from dotenv import load_dotenv
load_dotenv()
django.setup()
from app.database.models import Reddit, Stock


wsb = scrapeWSB(sendtweet=False)

for bet in wsb:
    sentiment = bet.get('sentiment').split(' ') if (bet.get('sentiment', False) and bet.get('sentiment') != 'unknown') else None
    sentimentTerm = sentiment[0] if sentiment else None
    sentimentPercent = sentiment[1] if sentiment else None

    stock = Stock.objects.update_or_create(
        ticker=bet.get('symbol'),
        defaults={
            'name': bet.get('companyName', None),
            'lastPrice': bet.get('latestPrice', None),
            'changePercent': bet.get('changePercent', None),
            'ytdChange': bet.get('ytdChange', None),
            'volume': bet.get('volume', None)
        }
    )

    Reddit.objects.update_or_create(
        stock=stock[0],
        defaults={
            'frequency': bet.get('frequency'),
            'sentiment': sentimentTerm,
            'sentimentPercent': (float(sentimentPercent.split('%')[0]) / 100) if sentimentPercent else None,
        }
    )

    print('saved {}'.format(bet['symbol']))
