from app.lab.news.article_stock import ArticleStock
import redis
import sys
import django
from django.apps import apps
django.setup()

News = apps.get_model('database', 'News')
articles = News.objects.all()
r = redis.Redis(host='localhost', port=6379, db=0, charset="utf-8", decode_responses=True)
heap = []

for article in articles:
    soup_string = r.get('news-soup-'+str(article.id))
    if (soup_string):
        heap.append(article)

ArticleStock(heap).find()
