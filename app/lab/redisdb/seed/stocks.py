import django
from django.apps import apps
import json
import redis
import sys
import os
from dotenv import load_dotenv
load_dotenv()
django.setup()

r = redis.Redis(host='localhost', port=6379, db=0, charset="utf-8", decode_responses=True)

Stock = apps.get_model('database', 'Stock')
Earnings = apps.get_model('database', 'Earnings')
Financials = apps.get_model('database', 'Financials')
Trend = apps.get_model('database', 'Trend')
Valuation = apps.get_model('database', 'Valuation')
stocks = Stock.objects.all()

for stock in stocks:    
    ticker = stock.ticker
    print(ticker)

    # Stocks    
    r.set('stock-'+ticker+'-name', (stock.name if stock.name else ""))
    r.set('stock-'+ticker+'-industry', (stock.industry if stock.industry else ""))
    r.set('stock-'+ticker+'-employees', (stock.employees if stock.employees else ""))
    r.set('stock-'+ticker+'-price', (stock.lastPrice if stock.lastPrice else ""))
    r.set('stock-'+ticker+'-sector', (stock.sector if stock.sector else ""))
    r.set('stock-'+ticker+'-description', (stock.description if stock.description else ""))    

    # Earnings
    if (Earnings.objects.filter(stock=stock).count() != 0):
        earnings = Earnings.objects.get(stock=stock)

        r.set('stock-'+ticker+'-ttmEPS', (earnings.ttmEPS if earnings.ttmEPS else ""))
        # r.set('stock-'+ticker+'-reportedEPS', (earnings.reportedEPS if earnings.reportedEPS else ""))
        # r.set('stock-'+ticker+'-reportedConsensus', (earnings.reportedConsensus if earnings.reportedConsensus else ""))

    # Financials
    if (Financials.objects.filter(stock=stock).count() != 0):
        financials = Financials.objects.get(stock=stock)

        r.set('stock-'+ticker+'-reportDate', (financials.reportDate if financials.reportDate else ""))
        r.set('stock-'+ticker+'-netIncome', (financials.netIncome if financials.netIncome else ""))
        r.set('stock-'+ticker+'-netWorth', (financials.netWorth if financials.netWorth else ""))
        r.set('stock-'+ticker+'-shortTermDebt', (financials.shortTermDebt if financials.shortTermDebt else ""))
        r.set('stock-'+ticker+'-longTermDebt', (financials.longTermDebt if financials.longTermDebt else ""))
        r.set('stock-'+ticker+'-totalCash', (financials.totalCash if financials.totalCash else ""))
        r.set('stock-'+ticker+'-totalDebt', (financials.totalDebt if financials.totalDebt else ""))
        r.set('stock-'+ticker+'-debtToEquity', (financials.debtToEquity if financials.debtToEquity else ""))
        r.set('stock-'+ticker+'-priceToSales', (financials.priceToSales if financials.priceToSales else ""))
        r.set('stock-'+ticker+'-EBITDA', (financials.EBITDA if financials.EBITDA else ""))
        r.set('stock-'+ticker+'-freeCashFlow', (financials.freeCashFlow if financials.freeCashFlow else ""))
        r.set('stock-'+ticker+'-freeCashFlowPerShare', (financials.freeCashFlowPerShare if financials.freeCashFlowPerShare else ""))
        r.set('stock-'+ticker+'-freeCashFlowYield', (financials.freeCashFlowYield if financials.freeCashFlowYield else ""))
        r.set('stock-'+ticker+'-longTermDebtToEquity', (financials.longTermDebtToEquity if financials.longTermDebtToEquity else ""))

    # Trend
    if (Trend.objects.filter(stock=stock).count() != 0):
        trend = Trend.objects.get(stock=stock)

        r.set('stock-'+ticker+'-week52', (trend.week52 if trend.week52 else ""))
        r.set('stock-'+ticker+'-day5ChangePercent', (trend.day5ChangePercent if trend.day5ChangePercent else ""))
        r.set('stock-'+ticker+'-month1ChangePercent', (trend.month1ChangePercent if trend.month1ChangePercent else ""))
        r.set('stock-'+ticker+'-ytdChangePercent', (trend.ytdChangePercent if trend.ytdChangePercent else ""))
        r.set('stock-'+ticker+'-day50MovingAvg', (trend.day50MovingAvg if trend.day50MovingAvg else ""))
        r.set('stock-'+ticker+'-day200MovingAvg', (trend.day200MovingAvg if trend.day200MovingAvg else ""))
        r.set('stock-'+ticker+'-avgPricetarget', (trend.avgPricetarget if trend.avgPricetarget else ""))
        r.set('stock-'+ticker+'-highPriceTarget', (trend.highPriceTarget if trend.highPriceTarget else ""))
        r.set('stock-'+ticker+'-fromPriceTarget', (trend.fromPriceTarget if trend.fromPriceTarget else ""))
        r.set('stock-'+ticker+'-fromHigh', (trend.fromHigh if trend.fromHigh else ""))

    # Valuation
    if (Valuation.objects.filter(stock=stock).count() != 0):
        valuation = Valuation.objects.get(stock=stock)

        r.set('stock-'+ticker+'-peRatio', (valuation.peRatio if valuation.peRatio else ""))