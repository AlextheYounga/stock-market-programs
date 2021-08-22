import redis
from app.lab.news.article_stock import ArticleStock
import django
from dotenv import load_dotenv
load_dotenv()
django.setup()
from app.database.models import News


articles = News.objects.all()
r = redis.Redis(host='localhost', port=6379, db=0, charset="utf-8", decode_responses=True)
heap = []

for article in articles:
    soup_string = r.get('news-soup-'+str(article.id))
    if (soup_string):
        heap.append(article)

ArticleStock(heap).find()
