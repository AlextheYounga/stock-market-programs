import statistics
import sys
import math
import json
from ..core.functions import extract_data, removeZeroes
from ..core.api.historical import getHistoricalData
from ..core.api.stats import getCurrentPrice
from datetime import datetime


def rangeRules(ticker):
    signalArray = {}
    assetData = getHistoricalData(ticker, timeframe='3m')    
    # --------------------------------------------
    # Data
    prices = list(reversed(removeZeroes(extract_data(assetData, 'close'))))
    current_price = getCurrentPrice(ticker)
    highs = list(reversed(removeZeroes(extract_data(assetData, 'high'))))
    lows = list(reversed(removeZeroes(extract_data(assetData, 'low'))))
    dates = list(reversed(removeZeroes(extract_data(assetData, 'date'))))
    volumes = list(reversed(removeZeroes(extract_data(assetData, 'volume'))))
    # --------------------------------------------

    # -------------------------------------------
    # Technicals
    technicalDonchianHigh = max(highs[:22])
    technicalDonchianLow = min(lows[:22])
    week3DonchianHigh = max(highs[:16])
    week3DonchianLow = min(lows[:16])
    trend = ((prices[0] - prices[-1]) / prices[-1]) * 100 if (prices[0] != 0 and prices[-1] != 0) else 0
    # --------------------------------------------

    # --------------------------------------------
    # Volatility
    stdevTrade = statistics.stdev(prices[:16])
    stdevMonth = statistics.stdev(prices[:22])
    stdevTrend = statistics.stdev(prices[:64])
    volTrade = current_price * (stdevTrade / current_price) * (math.sqrt(1/16)) if (current_price != 0) else 0
    volMonth = current_price * (stdevMonth / current_price) * (math.sqrt(1/22)) if (current_price != 0) else 0
    volTrend = current_price * (stdevTrend / current_price) * (math.sqrt(1/64)) if (current_price != 0) else 0
    volPercent = (volMonth / current_price) * 100
    # --------------------------------------------

    # --------------------------------------------
    # Volume
    volumeTrend = volumes[:64]
    volumeChange = ((volumeTrend[0] - volumeTrend[-1]) / volumeTrend[-1]) * 100 if (volumeTrend[0] != 0 and volumeTrend[-1] != 0) else 0
    # --------------------------------------------

    # --------------------------------------------
    # Probability Range
    upperVol = (current_price + volMonth)
    lowerVol = (current_price - volMonth)
    highRange = (week3DonchianHigh - (volMonth * 3))
    lowRange = (week3DonchianLow + (volMonth * 3))
    percentUpside = ((week3DonchianHigh - current_price) / current_price) * 100 if (technicalDonchianHigh > current_price) else "Infinite"
    percentDownside = ((current_price - week3DonchianLow) / current_price) * 100 if (current_price > technicalDonchianLow) else "Infinite"
    # --------------------------------------------

    # --------------------------------------------
    # Convert to Percentage Format
    volPercent = "{}%".format(round(volPercent, 2))
    volumeChange = "{}%".format(round(volumeChange, 2))
    percentUpside = "{}%".format(round(percentUpside, 2)) if isinstance(percentUpside, float) else percentUpside
    percentDownside = "{}%".format(round(percentDownside, 2)) if isinstance(percentDownside, float) else percentDownside
    month3trend = "{}%".format(round(trend, 2))
    # --------------------------------------------

    # --------------------------------------------
    # Signal based on volatility and probability.
    if (upperVol < current_price):
        signal = '~1 Stdev Higher'
    if (lowerVol > current_price):
        signal = '~1 Stdev Lower'
    if (lowerVol <= current_price <= upperVol):
        signal = 'Hold - Within StDev'
    if (lowRange > current_price):
        signal = 'Buy!'
    if (highRange < current_price):
        signal = 'Sell Signal'
    if (technicalDonchianLow > current_price):
        signal = 'Donchian Low Breached; Potential Breakout'
    if (technicalDonchianHigh < current_price):
        signal = 'Donchian High Breached; Potential Breakout'

    signalArray[ticker] = {
        'currentPrice': current_price,
        'lowerRange': round(lowRange, 3),
        'upperRange': round(highRange, 3),
        'technicalLow': round(technicalDonchianLow, 3),
        'technicalHigh': round(technicalDonchianHigh, 3),
        'stDev': round(volMonth, 3),
        'stDevPercent%': volPercent,
        'VolumeChange': volumeChange,
        'PercentUpside': percentUpside,
        'PercentDownside': percentDownside,
        '3MonthTrend': month3trend,
        'Signal': signal,
    }

    return signalArray
