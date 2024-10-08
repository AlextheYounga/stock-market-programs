import json
import os
import sys
import colored
from colored import stylize
from dotenv import load_dotenv
from log_handler import log
from app.lab.core.output import printTable
import twitter
import tweepy
load_dotenv()

logger = log('Tweet')
class Tweet():
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

    def prompt_user(self):
        while True:
            # First prompt
            send = str(input('Send Tweet? (y/n): '))
            if send in ('y', 'n'):
                break            
            print(stylize("Invalid input.", colored.fg("red")))

        return send
            
    def confirm_thread(self, thread):
        for tweet in thread:
            print(self.draw_box(tweet))
        send = self.prompt_user()
        return True if (send == 'y') else False
    
    def send_thread(self, lst):
        if (isinstance(lst, list)):
            if self.confirm_thread(lst):
                ids = {}
                for i, tweet in enumerate(lst):
                    if (i == 0):
                        sent_tweet = self.api.PostUpdate(tweet)._json
                        ids[i] = sent_tweet['id']
                        continue
                    reply_to = ids[i - 1]
                    sent_tweet = self.api.PostUpdate(status=tweet, in_reply_to_status_id=reply_to)._json
                    ids[i] = sent_tweet['id']
                print(stylize("Thread sent", colored.fg("green")))
            else:
                print(stylize("Thread aborted", colored.fg("green")))

        else:
            self.send(lst)


    def send(self, tweet, headline=False, footer=False, prompt=True):
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
            if (prompt):
                send = self.prompt_user()
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
            if (prompt == False or send == 'y'):
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

    
    def analyze_tweet(self, tweet_id):
        tweet = self.api.GetStatus(status_id=tweet_id)        
        for att in dir(tweet):
            print(f"{att}: ", getattr(tweet,att))         

    def analyze_favourites(self, handle):
        likes = self.api.GetFavorites(screen_name=handle, count=200)
        # print(dir(likes))
        print()
        for like in likes:            
            print(like.user.screen_name, like.id, like.created_at)            



