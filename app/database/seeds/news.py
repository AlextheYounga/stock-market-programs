import django
from django.apps import apps
from ...lab.news.scrape_headlines import scrape_news
django.setup()


News = apps.get_model('database', 'News')
Stock = apps.get_model('database', 'Stock')

news = scrape_news(query='best+stocks+to+buy+right+now')

for n in news:
    stock = Stock.objects.update_or_create(
        ticker=n['ticker'],
        defaults = {
            'name': n['companyName'],
            'lastPrice': n['latestPrice'],
            'changePercent': n['changePercent'],
            'ytdChange': n['ytdChange'],
            'volume': n['volume'],
        }

    )
    News.objects.create(
        stock=stock[0],
        urls=n['urls']
    )