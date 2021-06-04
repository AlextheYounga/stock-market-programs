from django.db import models
from jsonfield import JSONField

# Create your models here.
class Stock(models.Model):
    ticker = models.CharField(db_index=True, max_length=30, unique=True)
    name = models.CharField(max_length=300, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Hurst(models.Model):
    stock_id = models.ForeignKey(Stock, on_delete = models.CASCADE)
    values = models.JSONField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Gold(models.Model):
    date = models.models.DateField(auto_now=False, auto_now_add=False)
    close = models.FloatField(null=True)
    low = models.FloatField(null=True)
    high = models.FloatField(null=True)    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Vix(models.Model):
    ticker = models.CharField(db_index=True, max_length=30, unique=True)
    value = models.FloatField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class News(models.Model):
    url = models.CharField(null=True)
    stock = models.CharField(db_index=True, max_length=30, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)