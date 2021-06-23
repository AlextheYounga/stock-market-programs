from django.db import models
from jsonfield import JSONField

# Create your models here.
class Stock(models.Model):
    id = models.AutoField(primary_key=True)
    ticker = models.CharField(db_index=True, max_length=30, unique=True)
    name = models.CharField(max_length=300, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Hurst(models.Model):
    id = models.AutoField(primary_key=True)
    stock_id = models.ForeignKey(Stock, on_delete = models.CASCADE)
    values = models.JSONField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Gold(models.Model):
    id = models.AutoField(primary_key=True)
    date = models.DateField(auto_now=False, auto_now_add=False)
    close = models.FloatField(null=True)
    low = models.FloatField(null=True)
    high = models.FloatField(null=True)    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Vix(models.Model):
    id = models.AutoField(primary_key=True)
    ticker = models.CharField(db_index=True, max_length=30, unique=True)
    value = models.FloatField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class News(models.Model):
    id = models.AutoField(primary_key=True)
    url = models.CharField(null=True, max_length=1000)
    stock = models.CharField(db_index=True, max_length=30, unique=True)
    frequency = models.IntegerField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Reddit(models.Model):
    id = models.AutoField(primary_key=True)
    stock = models.CharField(db_index=True, max_length=30, unique=True)
    frequency = models.IntegerField(null=True)
    sentiment = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)