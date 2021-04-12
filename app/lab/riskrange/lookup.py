import statistics
import math
import json
import sys
from .methodology import rangeRules
from ..core.output import printTable
from ..fintwit.tweet import send_tweet


def rangeLookup(ticker, sendtweet=False):
    data = rangeRules(ticker)
    printTable(data[ticker])

    if (sendtweet):
        percentDownside = data[ticker]['PercentDownside']
        percentUpside = data[ticker]['PercentUpside']
        lowerRange = data[ticker]['lowerRange']
        upperRange = data[ticker]['upperRange']
        tweet = "${} short term probability range: \nlowerBound: {} \nupperBound: {} \npercentDownside: {} \npercentUpside: {} \n(Markets are fractal, upside and downside probabilities do not always translate to risk).".format(
            ticker,
            lowerRange,
            upperRange,
            percentDownside,
            percentUpside
        )
        
        send_tweet(tweet, True)
