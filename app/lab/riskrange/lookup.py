import statistics
import math
import json
import sys
from .methodology import rangeRules
from app.lab.core.output import printTable
from app.lab.fintwit.fintwit import Fintwit


def rangeLookup(ticker, sendtweet=False):
    data = rangeRules(ticker)
    printTable(data[ticker])

    if (sendtweet):
        twit = Fintwit()
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
        
        twit.send_tweet(tweet, True)
