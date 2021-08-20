from os import spawnve
from django.db import models
from django.db.models.deletion import CASCADE
from jsonfield import JSONField
from numpy import save
from requests.models import LocationParseError
from app.functions import frequencyInList, filterNone
from django.forms.models import model_to_dict
from app.lab.vix.vixvol import VixVol


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

    def store(self, data, ticker=None):
        if (data['symbol']):
            data['ticker'] = data['symbol']
            del data['symbol']
        if (data['companyName']):
            data['name'] = data['companyName']
            del data['companyName']
        ticker = ticker or data['ticker']
        data = filterNone(data)
        # Save
        stock, created = Stock.objects.update_or_create(
            ticker=ticker,
            defaults={data}
        )        
        return stock, created


    def getETFs(tickersonly=False):
        stocks = Stock.objects.all()
        etfs = []
        for stock in stocks:
            if ('ETF' in stock.name):
                if (tickersonly):
                    etfs.append(stock.ticker)
                else:
                    etfs.append(stock)

        return etfs
    
    def get(self, ticker):
        if (Stock.objects.filter(ticker=ticker).exists()):
            return Stock.objects.get(ticker=ticker).value
        return False 
        

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

class Senate(models.Model):
    id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=300, null=True)
    last_name = models.CharField(max_length=300)
    office = models.CharField(max_length=300, null=True)
    link = models.TextField(null=True)
    date = models.DateField(auto_now=False, auto_now_add=False)
    transactions = models.JSONField(null=True) 
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "senate"

class Vix(models.Model):
    id = models.AutoField(primary_key=True)
    ticker = models.CharField(db_index=True, max_length=30, unique=True)
    value = models.FloatField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        verbose_name_plural = "vix"
    
    def store(self, ticker, vix):
        vix, created = Vix.objects.update_or_create(
            ticker=ticker,
            defaults = {
                'value': round(vix, 3),
            }                
        )
        return vix, created
    
    def get(self, ticker):
        if (Vix.objects.filter(ticker=ticker).exists()):
            return Vix.objects.get(ticker=ticker).value
        return None 
    
    def lookup(self, ticker):
        vix = self.get(ticker)
        if (vix):
            return vix
            
        vixvol = VixVol().equation(ticker)
        if (vixvol):
            Vix().store(ticker, vixvol)
            return self.get(ticker)
        return None
        

class News(models.Model):
    id = models.AutoField(primary_key=True)
    url = models.TextField(unique=True)
    headline = models.CharField(null=True, max_length=2000)
    author = models.CharField(null=True, max_length=200)
    source = models.CharField(null=True, max_length=200)
    description = models.CharField(null=True, max_length=5000)
    pubDate = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        verbose_name_plural = "news"
    
    def store(self, item):        
        article, created = News.objects.update_or_create(
            url=item['url'],
            defaults = {
            'headline': item.get('headline', None),
            'author': item.get('author', None),
            'source': item.get('source', None),
            'description': item.get('description', None),
            'pubDate': item.get('pubDate', None)}
        )        
        return article, created

    def latest_news(self):
        latest_news = []
        model_set = News.objects.filter(pubDate__isnull=False).all().order_by('-pubDate')[:40]
        for m in model_set:
            dct = model_to_dict(m)
            dct['stocknews'] = m.stocknews_set.all() or []
            latest_news.append(dct)
        return latest_news
    
    def latest_stocks_mentioned(self):
        latest_news = self.latest_news()
        stocks = []
        for ln in latest_news:
            print(ln)
            if ('stocknews' in ln):
                for stock in ln['stocknews']:
                    dct = {
                        'ticker': stock.ticker,
                        'name': stock.name,
                        'lastPrice': stock.stock.lastPrice,
                        'changePercent': round((stock.stock.changePercent or 0) * 100, 2),                        
                    }
                    stocks.append(dct)
        return stocks


class StockNews(models.Model):
    id = models.AutoField(primary_key=True)
    article = models.ForeignKey(News, on_delete=CASCADE)
    stock = models.ForeignKey(Stock, on_delete=CASCADE)
    name = models.CharField(max_length=500, null=True)
    ticker = models.CharField(db_index=True, max_length=30)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        verbose_name_plural = "stocknews"
    
    def store(self, article, stock, data, ticker=None, save_vix=False):
        ticker = ticker or (data.get('ticker', None) or data.get('symbol', None))
        name = data.get('name', None) or data.get('companyName', None)

        stock, created = article.stocknews_set.update_or_create(
            article=article, stock=stock,
            defaults={
                'ticker': ticker,
                'name': name,
            }
        )       
        if (save_vix):
            Vix().lookup(stock.ticker)

        return stock, created
    
    def get(self, ticker):
        if (Stock.objects.filter(ticker=ticker).exists()):
            return Stock.objects.get(ticker=ticker).value
        return False 
    
    def frequency(self, ticker):
        stocks = StockNews.objects.all().values_list('ticker')
        return frequencyInList(stocks, ticker)

    def top_mentioned(self):
        top = {}
        stocks = StockNews.objects.all().values_list('ticker')
        for stock in stocks:
            top['ticker'] = stock
            top['frequency'] = frequencyInList(stocks, stock)

        sorted_results = sorted(top, key=lambda i: i['frequency'], reverse=True)
        return sorted_results[:10]

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