import django
from django.apps import apps
import json
import sys
from dotenv import load_dotenv
from app.lab.fintwit.tweet import send_tweet
load_dotenv()
django.setup()


def getETFs(tickersonly=False):
    Stock = apps.get_model('database', 'Stock')
    stocks = Stock.objects.all()
    etfs = []
    for stock in stocks:
        if ('ETF' in stock.name):
            if (tickersonly):
                etfs.append(stock.ticker)
            else:
                etfs.append(stock)

    return etfs


def getTopPerformingETFsYTD(n=None):
    """
    Parameters
    ----------
    n      :int
            number of items you wish to take

    Returns
    -------
    query object
    """
    MacroTrends = apps.get_model('database', 'MacroTrend')
    if (n):
        etfs = MacroTrends.objects.order_by('-ytdChangePercent')[:n]
    else:
        etfs = MacroTrends.objects.order_by('-ytdChangePercent')

    return etfs


def getMonthMovers(n=None):
    """
    Parameters
    ----------
    n      :int
            number of items you wish to take

    Returns
    -------
    query object
    """
    MacroTrends = apps.get_model('database', 'MacroTrend')
    if (n):
        etfs = MacroTrends.objects.order_by('-month1ChangePercent')[:n]
    else:
        etfs = MacroTrends.objects.order_by('-month1ChangePercent')

    return etfs


def queryNameEtfs(string):
    MacroTrends = apps.get_model('database', 'MacroTrend')
    results = []
    if (isinstance(string, str)):
        etfs = MacroTrends.objects.all()
        for etf in etfs:
            if(string in etf.name):
                print("{} - {} monthChange:{}%".format(etf.ticker, etf.name, round(etf.month1ChangePercent, 2)))
                results.append(etf)

    return results               
    


def top_performing_ytd_etf_tweet():
    tweet = ""
    for etf in getTopPerformingETFsYTD(5):
        txt = "${} +{}%\n".format(etf.ticker, round(etf.ytdChangePercent, 2))
        tweet = tweet + txt
    send_tweet(tweet, True)


def month_movers_etf_tweet():
    tweet = ""
    for etf in getMonthMovers(5):
        txt = "${} - {} +{}%\n".format(etf.ticker, etf.name, round(etf.month1ChangePercent, 2))
        tweet = tweet + txt
    send_tweet(tweet, True)
