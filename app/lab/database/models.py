from django.db import models
from jsonfield import JSONField
# from bulk_update_or_create import BulkUpdateOrCreateQuerySet

# Create your models here.
class Stock(models.Model):
    ticker = models.CharField(db_index=True, max_length=30, unique=True)
    name = models.CharField(max_length=300, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Watchlist(models.Model):
    ticker = models.CharField(max_length=30)
    name = models.CharField(max_length=200)
    lastPrice = models.FloatField(null=True)
    peRatio = JSONField(null=True)
    week52 = models.FloatField(null=True)
    day5ChangePercent = models.FloatField(null=True)
    month1ChangePercent = models.FloatField(null=True)
    ytdChangePercent = models.FloatField(null=True)
    day50MovingAvg = models.FloatField(null=True)
    day200MovingAvg = models.FloatField(null=True)
    highPriceTarget = models.FloatField(null=True)
    fromPriceTarget = models.FloatField(null=True)
    fromHigh = models.FloatField(null=True)
    reportedEPS = JSONField(null=True)
    reportedConsensus = JSONField(null=True)
    ttmEPS = models.FloatField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)



    
