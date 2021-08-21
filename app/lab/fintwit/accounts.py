from django.core.cache import cache
from datetime import datetime, timedelta
from .functions import prompt_yes_no, readJSONFile, wordVariator
import time
from time import sleep
from dotenv import load_dotenv
import os
import json
import sys
import tweepy
load_dotenv()


class Accounts():
    def __init__(self):
        self.auth = tweepy.OAuthHandler(os.environ.get("TWITTER_API_KEY"), os.environ.get("TWITTER_SECRET_KEY"))
        self.auth.set_access_token(os.environ.get("TWITTER_ACCESS_KEY"), os.environ.get("TWITTER_ACCESS_SECRET"))
        self.api = tweepy.API(self.auth)

    def followFollowers(self, handle, p=cache.get('auto_followers_last_page'), accountList=False):
        user = self.api.get_user(handle)
        keywords = self.collect_keywords()
        print("Name: {}\nScreen Name: {}\nDescription: {}\n".format(user.name, user.screen_name, user.description))

        if (prompt_yes_no("This user?")):

            for page in self.limit_handled(tweepy.Cursor(self.api.followers, id=user.id, page=p).pages()):
                p += 1
                if (accountList and (p >= 200)):
                    break
                current_time = datetime.now()
                cache.set('twitter_last_run', current_time, 910)
                cache.set('auto_followers_last_page', p, None)

                print('Page {}'.format(p))
                for f in page:
                    if (self.screen_follower(f, keywords)):
                        try:
                            friendship = self.api.lookup_friendships([f.id])[0]
                        except:
                            break
                        if (not(friendship.is_following or friendship.is_following_requested)):
                            self.api.create_friendship(f.id, screen_name=None, user_id=f.id, follow=False)
                            print("{} - {} followers".format(f.screen_name, f.followers_count))

    def accountList(self):
        path = 'bot\data\accounts.txt'
        txt = open(path, "r")

        userlist = []
        for line in txt:
            stripped_line = line.strip()
            line_list = stripped_line.split()
            userlist.append(line_list[0])

        txt.close()

        return userlist

    def limit_handled(self, cursor):
        while True:
            try:
                yield cursor.next()
            except tweepy.RateLimitError:
                last_run = cache.get('twitter_last_run')
                current_time = datetime.now()
                if (last_run):
                    next_run = (last_run + timedelta(minutes=15))
                    wait_time = (next_run - current_time).seconds + 5  # Giving it a little leeway of 5 seconds
                    print("Run Halted =", last_run.strftime("%H:%M:%S"))
                    print("Next Run = {}".format(next_run.strftime("%H:%M:%S")))

                    time.sleep(wait_time)
                else:
                    print('Halt time not being cached.')
                    wait_time = (15 * 60)
                    next_run = (current_time + timedelta(minutes=15)).strftime("%H:%M:%S")
                    print("Run Stopped =", current_time.strftime("%H:%M:%S"))
                    print("Next Run = {}".format(next_run))

                    time.sleep(wait_time)

    def collect_keywords(self):
        keywords = readJSONFile('bot\data\keywords.json')

        for group, words in keywords.items():
            if (type(keywords[group]) == list):
                keywords[group].extend(wordVariator(words))
            else:
                for k, v in keywords[group].items():
                    keywords[group][k].extend(wordVariator(v))

        return keywords

    def screen_follower(f, keywords, trim=False):
        reason = None
        for nb in keywords['negative']['bio']:
            if (nb in f.description):
                if (trim):
                    print('Contained negative word in bio')
                return False
        for ns in keywords['negative']['screen_name']:
            if (ns in f.screen_name):
                if (trim):
                    print('Contained negative word in screen name')
                return False

        if (trim):
            # No red flags by this point
            # trimfollowers() may safely exit
            return True

        if (f.followers_count > 400):
            for p in keywords['positive']:
                if (p in f.description):
                    return True
                if (p in f.screen_name):
                    return True

        return False

    def trimFollowers(self, p=cache.get('trim_followers_last_page')):
        user = self.api.get_user(os.environ.get("TWITTER_HANDLE"))
        keywords = self.collect_keywords()

        for page in self.limit_handled(tweepy.Cursor(self.api.friends, id=user.id, page=p).pages()):
            p += 1
            current_time = datetime.now()
            cache.set('twitter_last_run', current_time, 910)
            cache.set('trim_followers_last_page', p, None)

            print('Page {}'.format(p))
            for f in page:
                if (self.screen_follower(f, keywords, trim=True) == False):
                    try:
                        self.api.destroy_friendship(f.id, screen_name=None, user_id=f.id)
                        print("unfollowed {} - {} followers".format(f.screen_name, f.followers_count))
                    except:
                        break

    def followList(self):
        for account in self.accountList():
            self.followFollowers(account, p=0, accountList=True)
