from app.lab.fintwit.tweet import Tweet
import datetime
import django
from dotenv import load_dotenv
import sys
import json
load_dotenv()
django.setup()
from app.database.models import CongressTransaction


today_min = datetime.datetime.combine(datetime.date.today(), datetime.time.min)
today_max = datetime.datetime.combine(datetime.date.today(), datetime.time.max)
trades = list(CongressTransaction.objects.filter(created_at__range=(today_min, today_max)))

def tweet(trades, prompt=True):
    def writeLine(trade):
        """
        Specifically building each line of tweet based on each trade.
        """
        relation = f" Owner: {trade.owner}" if (trade.owner and trade.owner != 'Self') else ''
        ticker = f"${trade.ticker}"
        saletype = trade.sale_type.replace('_', ' ').title()
        date = datetime.datetime.strptime(trade.date, '%Y-%m-%d').strftime('%b %d') if (isinstance(trade.date, str)) else trade.date.strftime('%b %d')
        # date = datetime.datetime.strptime(trade.date, '%Y-%m-%d').strftime('%b %d')
        amount = f"${trade.amount_low} - ${trade.amount_high}" if (trade.amount_low and trade.amount_high) else f"${trade.amount_low or trade.amount_high}"

        bodyline = f"{saletype} {ticker} {amount} on {date}{relation}\n"
        return bodyline

    def buildThreads(orders):
        """
        Incrimentally building each tweet by adding lines until it becomes longer than
        280 characters. Once the tweet reaches just below 280, it is appended to thread object.
        Returns dict of threads keyed by congress member name.
        """
        thread = {}               
        for name, order in orders.items():
            if (name not in thread):
                thread[name] = []

            headline = order['headline']
            body = ""

            for line in order['body']:
                if (len(headline + body + line) >= 280):  
                    tweet = headline + body
                    thread[name].append(tweet)
                    body = ""  # Resetting body

                body = (body + line)

            tweet = headline + body  # Handles remaining lines.
            thread[name].append(tweet)

        return thread
    
    # Tweet building start
    twit = Tweet()
    orders = {}

    for trade in trades:
        rep = trade.congress  # Get representitive info
        if (trade.ticker):
            if (rep.last_name not in orders):
                orders[rep.last_name] = {
                    'headline': f"New market transaction for house rep: {rep.name}.\n",
                    'body': [],
                }

            bodyline = writeLine(trade)
            orders[rep.last_name]['body'].append(bodyline)  # Building tweet line by line.

    threads = buildThreads(orders)

    for rep, thread in threads.items():
        twit.send_thread(thread)