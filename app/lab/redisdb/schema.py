import django
from django.apps import apps
import json
import redis
import sys
import os
from dotenv import load_dotenv
load_dotenv()
django.setup()


def rdb_schema():
    """
    This is the standard redis db schema for this app, built on key,value pairs.
    The keys are differentiated by tickers.


    # Stocks
    'stock-'+ticker+'-name'
    'stock-'+ticker+'-industry' 
    'stock-'+ticker+'-employees' 
    'stock-'+ticker+'-price' 
    'stock-'+ticker+'-sector' 
    'stock-'+ticker+'-description'

    # Gold
    'gold-'+date+'-open' 
    'gold-'+date+'-low' 
    'gold-'+date+'-high' 
    'gold-'+date+'-close' 

    # Earnings
    'stock-'+ticker+'-ttmEPS' 

    # Financials
    'stock-'+ticker+'-reportDate'
    'stock-'+ticker+'-netIncome'
    'stock-'+ticker+'-netWorth'
    'stock-'+ticker+'-shortTermDebt'
    'stock-'+ticker+'-longTermDebt'
    'stock-'+ticker+'-totalCash'
    'stock-'+ticker+'-totalDebt'
    'stock-'+ticker+'-debtToEquity'
    'stock-'+ticker+'-priceToSales'
    'stock-'+ticker+'-EBITDA'
    'stock-'+ticker+'-freeCashFlow'
    'stock-'+ticker+'-freeCashFlowPerShare'
    'stock-'+ticker+'-freeCashFlowYield'
    'stock-'+ticker+'-longTermDebtToEquity'

    # Stock Trends
    'stock-'+ticker+'-week52'
    'stock-'+ticker+'-day5ChangePercent'
    'stock-'+ticker+'-month1ChangePercent'
    'stock-'+ticker+'-ytdChangePercent'
    'stock-'+ticker+'-day50MovingAvg'
    'stock-'+ticker+'-day200MovingAvg'
    'stock-'+ticker+'-avgPricetarget'
    'stock-'+ticker+'-highPriceTarget'
    'stock-'+ticker+'-fromPriceTarget'
    'stock-'+ticker+'-fromHigh'

    # Google Trends
    'trends-'+ticker+'-interest'

    # Valuation
    'stock-'+ticker+'-peRatio'

    # HistoricalPrices
    'stock-'+ticker+'-prices' (json.dump)
    'stock-'+ticker+'-prices-datapoints' 

    # Correlations
    'correlation-'+t1+'-'+t2+'-rvalue'
    'correlation-'+t1+'-'+t2+'-datapoints'

    #Output
    'lab-last-output'

    """

    key_roots = [
        'stock',
        'gold',
        'correlation',
        'trends'
    ]
    
    return key_roots