from app.lab.core.output import printFullTable
import praw
from praw.models import MoreComments
import colored
from colored import stylize
from app.functions import frequencyInList, chunks
from app.lab.core.api.iex import IEX
from .functions import *
import time
import datetime
from app.lab.fintwit.tweet import Tweet
from dotenv import load_dotenv
load_dotenv()


def scanHeap(heap):
    """
    This function takes a list of text blobs and scans all words for potential stocks based on a regex formula. 
    The function will cross-reference every potential stock with IEX to determine whether or not it is an actual stock.
    Strings that do not pass the test will be sent to the blacklist to prevent future lookups.

    Parameters
    ----------
    heap     : list
               list of text blobs taken from reddit

    Returns
    -------
    dict
        list of results confirmed to be stocks
    """
    target_strings = []
    sentiment_index = {}
    for h in heap:

        # Find all capital letter strings, ranging from 1 to 5 characters, with optional dollar signs
        # preceded and followed by space. Collect 3 words before and after capital letter to check context.
        sentiments = re.findall(r'(?:\S+\s+){0,3}[\S][$]?[A-Z]{1,5}[\s]*(?:\S+\b\s*){0,3}', str(h))

        for thoughts in sentiments:
            # Find all capital letter strings, ranging from 1 to 5 characters, with optional dollar
            # signs preceded and followed by space.
            tickers = re.findall(r'[\S][$]?[A-Z]{1,5}[\S]*', str(thoughts))

            for tick in tickers:
                tformat = removeBadCharacters(tick)
                feel = sentimentScanner(thoughts)
                if (feel):
                    if (sentiment_index.get(tformat, False)):
                        sentiment_index[tformat].append(feel)
                    else:
                        sentiment_index[tformat] = [feel]

                target_strings.append(tformat)

    blacklist = blacklistWords()
    possible = []

    for string in target_strings:
        if (string):
            if ((not string) or (string in blacklist)):
                continue

            possible.append(string)

    iex = IEX()
    results = []
    stockfound = []

    unique_possibles = list(dict.fromkeys(possible))
    chunked_strings = chunks(unique_possibles, 100)

    apiOnly = [
        'symbol',
        'companyName',
        'latestPrice',
        'changePercent',
        'ytdChange',
        'volume'
    ]

    print(stylize("{} possibilities".format(len(unique_possibles)), colored.fg("yellow")))

    for i, chunk in enumerate(chunked_strings):
        print(stylize("Sending heap to API", colored.fg("yellow")))
        batch = iex.get('quote', chunk)
        time.sleep(1)

        for ticker, stockinfo in batch.items():

            if (stockinfo.get('quote', False)):
                result = {}
                stockfound.append(ticker)
                freq = frequencyInList(possible, ticker)
                sentiment = sentimentCalculation(sentiment_index[ticker]) if sentiment_index.get(ticker, False) else 'unknown'

                print(stylize("{} stock found".format(ticker), colored.fg("green")))
                if (freq > 1):
                    result = {
                        'ticker': ticker,
                        'frequency': freq,
                        'sentiment': sentiment,
                    }
                    filteredinfo = {key: stockinfo['quote'].get(key, None) for key in apiOnly}
                    result.update(filteredinfo)
                    results.append(result)

    # Updating blacklist
    for un in unique_possibles:
        if (un not in stockfound):
            blacklist.append(un)

    updateBlacklist(blacklist)
    return results


def scrapeWSB(sendtweet=False, printResults=False):
    """
    This function uses the PRAW Reddit API to search the hottest posts on wallstreet bets.
    It will send a list of text blobs to the scanHeap() function.
    Handles tweeting functionality. 

    Parameters
    ----------
    sendtweet  : bool
               whether or not to tweet results

    Returns
    -------
    dict
        list of most-talked-about stocks on wallstreetbets
    """

    reddit = praw.Reddit(
        client_id=os.environ.get("REDDIT_CLIENT"),
        client_secret=os.environ.get("REDDIT_SECRET"),
        user_agent="Hazlitt Data by u/{}".format(os.environ.get("REDDIT_USERNAME")),
        username=os.environ.get("REDDIT_USERNAME"),
        password=os.environ.get("REDDIT_PASSWORD"),
    )

    subreddit = reddit.subreddit("wallstreetbets")

    urls = []
    heap = []

    for submission in subreddit.hot(limit=50):
        post_time = datetime.datetime.fromtimestamp(submission.created)
        print(stylize("r/wallstreetbets postdate={}: ".format(str(post_time)) + submission.title, colored.fg("green")))
        urls.append(submission.url)
        heap.append(submission.title)

        for top_level_comment in submission.comments:
            if isinstance(top_level_comment, MoreComments):
                continue
            heap.append(top_level_comment.body)

    results = scanHeap(heap)
    sorted_results = sorted(results, key=lambda i: i['frequency'], reverse=True)

    if (sendtweet):
        twit = Tweet()
        tweetdata = {}
        for r in sorted_results[:10]:
            tweetdata['$' + r['ticker']] = r['frequency']

        headline = "Top mentioned stocks on r/wallstreetbets and times mentioned:\n"
        tweet = headline + twit.translate_data(tweetdata)
        twit.send(tweet)

    if (printResults):
        printFullTable(sorted_results, struct='dictlist')
        return

    

    return results
