import json
import os
import sys
import colored
from colored import stylize
from app.lab.core.functions import prompt_yes_no
from dotenv import load_dotenv
import twitter
import texttable
load_dotenv()

class Fintwit():
    def __init__(self):
        self.api = twitter.Api(consumer_key=os.environ.get("TWITTER_API_KEY"),
                  consumer_secret=os.environ.get("TWITTER_SECRET_KEY"),
                  access_token_key=os.environ.get("TWITTER_ACCESS_KEY"),
                  access_token_secret=os.environ.get("TWITTER_ACCESS_SECRET"))

    def draw_box(self, text):
        lines = text.splitlines()
        width = max(len(s) for s in lines)
        res = ['┌' + '─' * width + '┐']
        for s in lines:
            res.append('│' + (s + ' ' * width)[:width] + '│')
        res.append('└' + '─' * width + '┘')
        return '\n'.join(res)


    def send_tweet(self, tweet, headline=False, footer=False):
        while True:
            if (headline):
                headline = ""
                sys.stdout.write('Write tweet headline:')
                headline = "{} \n".format(input())
                tweet = headline + tweet
            if (footer):
                footer = ""
                sys.stdout.write('Write tweet footer:')
                footer = "\n{}".format(input())
                tweet = tweet + footer

            print("Tweet:")
            print(self.draw_box(tweet))
            print('Characters: {}'.format(len(tweet)))

            if (len(tweet) > 280):            
                print(stylize("Error: Tweet over 280 characters.", colored.fg("red")))
                continue

            while True:
                # First prompt
                send = str(input('Send Tweet? (y/n): '))
                if send in ('y', 'n'):
                    break            
                print(stylize("Invalid input.", colored.fg("red")))

            if (send == 'n'):
                while True:
                    # Rerun program?
                    rerun = str(input('Rerun program? (y/n): '))
                    if rerun in ('y', 'n'):
                        break
                    else:
                        print(stylize("Invalid input.", colored.fg("red")))
                if (rerun == 'n'):
                    sys.exit()
                else:
                    continue
            if (send == 'y'):
                self.api.PostUpdate(tweet)            
                print(stylize("Tweet Sent", colored.fg("green")))
                break


    def translate_data(self, dic, keys=None):
        content = ""
        if not keys:
            keys = dic.keys()

        for k in keys:
            content = content + "\n{}: {}".format(k.title(), dic[k])
            
        return content
