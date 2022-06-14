from app.lab.fintwit.tweet import Tweet
import datetime
from dotenv import load_dotenv
load_dotenv()

class Fed():
    def balance_sheet_tweet(self, last, new, prompt=True):        
        def preposition(number):
            if (number < 0):
                return 'Down'
            else:
                return 'Up'

        twit = Tweet()
        newdate = datetime.datetime.strptime(new['date'], '%Y-%m-%d').strftime('%b %d')
        lastdate = datetime.datetime.strptime(last['date'], '%Y-%m-%d').strftime('%b %d')
        diff = str(int(float(new['value']) - float(last['value'])))
        headline = f"LATEST FED BALANCE SHEET NUMBER {newdate}:"
        value = self.format_number(new['value'])
        body = f"{preposition(int(diff))} {self.format_number(diff)} compared to last number on {lastdate}"
        tweet_data = [
            headline,
            value,
            body
        ]

        tweet = "\n".join(tweet_data)
        twit.send(tweet, prompt=prompt)