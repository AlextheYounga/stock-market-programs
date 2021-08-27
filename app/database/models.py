from os import lstat, spawnve
from django.db import models
from django.db.models.deletion import CASCADE
from django.db.models.fields.related import ForeignKey
from jsonfield import JSONField
from numpy import save
from statistics import mode
from requests.models import LocationParseError
from app.functions import frequencyInList, filterNone
from django.forms.models import model_to_dict
from app.lab.vix.vixvol import VixVol
import colored
from colored import stylize


# Create your models here.
class Stock(models.Model):
    id = models.AutoField(primary_key=True)
    ticker = models.CharField(db_index=True, max_length=30, unique=True)
    name = models.CharField(max_length=1000)
    latestPrice = models.FloatField(null=True)
    changePercent = models.FloatField(null=True)
    ytdChange = models.FloatField(null=True)
    volume = models.FloatField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def store(self, data, ticker=None):
        apiFields = {
            'symbol': 'ticker',
            'companyName': 'name',
        }

        dbOnly = [f.name for f in self._meta.get_fields()]

        for k, v in apiFields.items():
            if (data.get(k, False)):
                data[v] = data[k]
                del data[k]

        ticker = ticker or data['ticker']
        data = filterNone({key: data.get(key, None) for key in dbOnly})

        # Save
        stock, created = self.__class__.objects.update_or_create(
            ticker=ticker,
            defaults=data
        )
        return stock, created

    def getETFs(self, tickersonly=False):
        stocks = self.__class__.objects.all()
        etfs = []
        for stock in stocks:
            if ('ETF' in stock.name):
                if (tickersonly):
                    etfs.append(stock.ticker)
                else:
                    etfs.append(stock)

        return etfs


class Hurst(models.Model):
    id = models.AutoField(primary_key=True)
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
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


class Congress(models.Model):
    id = models.AutoField(primary_key=True)    
    first_name = models.CharField(max_length=300, null=True)
    last_name = models.CharField(max_length=300)
    name = models.CharField(max_length=300, unique=True, default=last_name)
    house = models.CharField(max_length=300)    
    office = models.CharField(max_length=300, null=True)
    district = models.CharField(max_length=300, null=True)
    total_gain_dollars = models.FloatField(null=True)
    total_gain_percent = models.FloatField(null=True)
    trades = models.IntegerField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "congress"
    
    def store(self, data):
        # Save
        congress, created = self.__class__.objects.update_or_create(
            first_name=data.get('first_name'), last_name=data.get('last_name'),
            defaults=data
        )
        return congress, created

    def top_trader(self):
        # TODO: Make top trader
        print('Make top trader')



class CongressTransaction(models.Model):
    id = models.AutoField(primary_key=True)
    congress = models.ForeignKey(Congress, on_delete=CASCADE)
    first_name = models.CharField(max_length=300, null=True)
    last_name = models.CharField(max_length=300)
    sale_type = models.CharField(max_length=300, null=True)
    asset_type = models.CharField(max_length=100, null=True)
    ticker = models.CharField(max_length=10, null=True)
    price_at_date = models.FloatField(null=True)
    amount_low = models.IntegerField(null=True)
    amount_high = models.IntegerField(null=True)
    date = models.DateField(auto_now=False, auto_now_add=False, null=True)
    filing_date = models.DateField(auto_now=False, auto_now_add=False, null=True)
    owner = models.CharField(max_length=300, null=True)
    link = models.TextField(null=True)
    transaction = models.JSONField(null=True)
    description = models.TextField(null=True) 
    comment = models.TextField(null=True) 
    hash_key = models.CharField(max_length=70, unique=True, default=None)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def store(self, data):
        # Save
        transaction, created = self.__class__.objects.update_or_create(
            hash_key=data.get('hash_key'),
            defaults=data
        )
        return transaction, created


class CongressPortfolio(models.Model):
    id = models.AutoField(primary_key=True)
    congress = models.ForeignKey(Congress, on_delete=CASCADE)
    first_name = models.CharField(max_length=300, null=True)
    last_name = models.CharField(max_length=300)
    position = models.CharField(max_length=100, null=True)
    ticker = models.CharField(max_length=10, null=True)
    description = models.TextField(null=False)
    shares = models.IntegerField(null=True)    
    cost_share = models.FloatField(null=True)
    latest_price = models.FloatField(null=True)
    market_value = models.FloatField(null=True)
    gain_dollars = models.FloatField(null=True)
    gain_percent = models.FloatField(null=True)    
    orders = models.JSONField(null=True)
    status = models.CharField(max_length=100, null=True)   
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Vix(models.Model):
    id = models.AutoField(primary_key=True)
    ticker = models.CharField(db_index=True, max_length=30, unique=True)
    value = models.FloatField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "vix"

    def store(self, ticker, vix):
        vix, created = self.__class__.objects.update_or_create(
            ticker=ticker,
            defaults={
                'value': round(vix, 3),
            }
        )
        return vix, created

    def get(self, ticker):
        if (self.__class__.objects.filter(ticker=ticker).exists()):
            return self.__class__.objects.get(ticker=ticker).value
        return None

    def lookup(self, ticker):
        vix = self.get(ticker)
        if (vix):
            return vix

        vixvol = VixVol().equation(ticker)
        if (vixvol):
            self.__class__.store(ticker, vixvol)
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
        article, created = self.__class__.objects.update_or_create(
            url=item['url'],
            defaults={
                'headline': item.get('headline', None),
                'author': item.get('author', None),
                'source': item.get('source', None),
                'description': item.get('description', None),
                'pubDate': item.get('pubDate', None)}
        )
        return article, created

    def latest_news(self):
        latest_news = []
        model_set = self.__class__.objects.filter(pubDate__isnull=False).all().order_by('-pubDate')[:40]
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
                        'latestPrice': stock.stock.latestPrice,
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
        stocks = self.__class__.objects.all().values_list('ticker')
        return frequencyInList(stocks, ticker)

    def top_mentioned(self):
        top = {}
        stocks = self.__class__.objects.all().values_list('ticker')
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
