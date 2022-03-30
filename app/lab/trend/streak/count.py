from .functions import *
from app.functions import extract_data
from app.lab.core.api.iex import IEX
from tabulate import tabulate



def count_streak(ticker):
    iex = IEX()
    asset_data = list(reversed(iex.getChart(ticker, timeframe='1y', priceOnly=True)))

    prices = extract_data(asset_data, 'close')
    dates = extract_data(asset_data, 'date')
    
    upStreaks, downStreaks = longestStretch(asset_data)
    trend_data = trendAnalysis(prices[:64])



    print("\n")
    print(tabulate([
        ['UpDays', trend_data['upDays']['count']],
        ['Current Streak', trend_data['upDays']['consecutive']],
        ['Longest Streak', len(upStreaks)],
        ['Average', trend_data['upDays']['average']]],
        headers=['Up Days', '']))

    print("\n")
    print(tabulate([
        ['DownDays', trend_data['downDays']['count']],
        ['Current Streak', trend_data['downDays']['consecutive']],
        ['Longest Streak', len(downStreaks)],
        ['Average', trend_data['downDays']['average']]],
        headers=['Down Days', '']))
    print("\n")

    print("Up")
    for i, day in enumerate(upStreaks):
        print("{} - {}".format(day['date'], day['close']))

    print("\n")
    print("Down")
    for i, day in enumerate(downStreaks):
        print("{} - {}".format(day['date'], day['close']))

    
   


