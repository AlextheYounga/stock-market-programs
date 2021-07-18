from app.lab.news.article_stock import ArticleStock
import django
from django.apps import apps
django.setup()

News = apps.get_model('database', 'News')
articles = News.objects.all()

# TODO: Make seeder just for news stocks

for article in articles:
    nf = NewsFeed(aggregator='google')
    nf.feed()