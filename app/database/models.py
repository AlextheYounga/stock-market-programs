from django.db import models
from django.db.models.deletion import CASCADE, DO_NOTHING
from jsonfield import JSONField
from ..lab.core.functions import frequencyInList


# Create your models here.
class Stock(models.Model):
    id = models.AutoField(primary_key=True)
    ticker = models.CharField(db_index=True, max_length=30, unique=True)
    name = models.CharField(max_length=1000)
    lastPrice = models.CharField(max_length=300, null=True)
    changePercent = models.FloatField(null=True)
    ytdChange = models.FloatField(null=True)
    volume = models.FloatField(null=True)    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Hurst(models.Model):
    id = models.AutoField(primary_key=True)
    stock = models.ForeignKey(Stock, on_delete = models.CASCADE)
    values = models.JSONField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "hurst"

class Gold(models.Model):
    id = models.AutoField(primary_key=True)
    date = models.DateField(auto_now=False, auto_now_add=False)
    close = models.FloatField(null=True)
    low = models.FloatField(null=True)
    high = models.FloatField(null=True)    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "gold"

class Vix(models.Model):
    id = models.AutoField(primary_key=True)
    ticker = models.CharField(db_index=True, max_length=30, unique=True)
    value = models.FloatField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        verbose_name_plural = "vix"

class News(models.Model):
    id = models.AutoField(primary_key=True)
    url = models.TextField(unique=True)
    headline = models.CharField(null=True, max_length=2000)
    author = models.CharField(null=True, max_length=200)
    source = models.CharField(null=True, max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        verbose_name_plural = "news"


class StockNews(models.Model):
    id = models.AutoField(primary_key=True)
    article = models.ForeignKey(News, on_delete=CASCADE)
    stock = models.ForeignKey(Stock, on_delete=CASCADE)
    companyName = models.CharField(max_length=500, null=True)
    ticker = models.CharField(db_index=True, max_length=30)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        verbose_name_plural = "stocknews"
    
    @property
    def frequency(ticker):
        stocks = StockNews.objects.all().values_list('ticker')
        return frequencyInList(stocks, ticker)

    @property
    def top_mentioned():
        top = {}
        stocks = StockNews.objects.all().values_list('ticker')
        for stock in stocks:
            top['ticker'] = stock
            top['frequency'] = frequencyInList(stocks, stock)

        sorted_results = sorted(top, key=lambda i: i['frequency'], reverse=True)
        return sorted_results

class Reddit(models.Model):
    id = models.AutoField(primary_key=True)
    stock = models.OneToOneField(Stock, on_delete=models.CASCADE, null=False)
    frequency = models.IntegerField(null=True)
    sentiment = models.CharField(max_length=100, null=True)
    sentimentPercent = models.FloatField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "reddit"