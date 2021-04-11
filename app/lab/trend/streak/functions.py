import statistics
import json
import sys
import os


def consecutiveDays(prices):
    upDays = 0
    downDays = 0
    for i, price in enumerate(prices):
        percentChange = (price - prices[i + 1]) / prices[i + 1]
        if percentChange > 0:
            upDays = upDays + 1
        else:
            break
    for i, price in enumerate(prices):
        percentChange = (price - prices[i + 1]) / prices[i + 1]
        if percentChange < 0:
            downDays = downDays + 1
        else:
            break
    return upDays, downDays


def longestStretch(data):
    upStreaks = []
    downStreaks = []
    strkTemp = []
    streak = 0
    # UpDays
    for i, day in enumerate(data):
        if (i+1 >= 0 and i+1 < len(data)):
            percentChange = (day['close'] - data[i + 1]['close']) / data[i + 1]['close']
            if percentChange > 0:
                streak = streak + 1
                strkTemp.append(day)
            else:
                if(len(strkTemp) > 0):
                    upStreaks.append(strkTemp)
                streak = 0
                strkTemp = []

    maxcount = max(len(v) for v in upStreaks)
    longest = [k for k, v in enumerate(upStreaks) if len(v) == maxcount][0]
    upStreaks = upStreaks[longest]
    strkTemp = []
    streak = 0
    # DownDays
    for i, day in enumerate(data):
        if (i+1 >= 0 and i+1 < len(data)):
            percentChange = (day['close'] - data[i + 1]['close']) / data[i + 1]['close']
            if percentChange < 0:
                streak = streak + 1
                strkTemp.append(day)
            else:
                if(len(strkTemp) > 0):
                    downStreaks.append(strkTemp)
                streak = 0
                strkTemp = []

    maxcount = max(len(v) for v in downStreaks)
    longest = [k for k, v in enumerate(downStreaks) if len(v) == maxcount][0]
    downStreaks = downStreaks[longest]
    return upStreaks, downStreaks


def trendAnalysis(prices):
    analysis = {}
    consecutiveUps, consecutiveDowns = consecutiveDays(prices)
    downDays = []
    upDays = []
    for i, price in enumerate(prices):
        if (i + 1 in range(-len(prices), len(prices))):
            percentChange = (price - prices[i + 1]) / prices[i + 1]
            if percentChange > 0:
                upDays.append(percentChange)
            if percentChange <= 0:
                downDays.append(percentChange)
        else:
            continue

    analysis['upDays'] = {
        'count': len(upDays),
        'consecutive': consecutiveUps,
        'average': "{}%".format(statistics.mean(upDays) * 100)
    }

    analysis['downDays'] = {
        'count': len(downDays),
        'consecutive': consecutiveDowns,
        'average': "{}%".format(statistics.mean(downDays) * 100)
    }

    return analysis
