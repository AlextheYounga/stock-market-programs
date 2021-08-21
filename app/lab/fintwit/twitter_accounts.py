from django.core.cache import cache
from datetime import datetime, timedelta
from app.lab.fintwit.functions import *
from app.functions import writeTxtFile, readTxtFile, deleteFromTxTFile, get_hazlitt_path
import time
from dotenv import load_dotenv
from logs.hazlittlog import log
import os
import json
import sys
import tweepy
load_dotenv()

logger = log('TwitterAccounts')
KEYWORDS = f"{get_hazlitt_path()}/app/lab/fintwit/data/keywords.json"
ACCOUNT_LIST = f"{get_hazlitt_path()}/app/lab/fintwit/data/accounts.txt"
USED_LIST = f"{get_hazlitt_path()}/app/lab/fintwit/data/finished.txt"

class TwitterAccounts():
    def __init__(self):
        self.auth = tweepy.OAuthHandler(os.environ.get("TWITTER_API_KEY"), os.environ.get("TWITTER_SECRET_KEY"))
        self.auth.set_access_token(os.environ.get("TWITTER_ACCESS_KEY"), os.environ.get("TWITTER_ACCESS_SECRET"))
        self.api = tweepy.API(self.auth)

    def followList(self, p=0):
        accounts = readTxtFile(ACCOUNT_LIST)
        if (accounts):
            for account in accounts:
                self.followFollowers(account, p, accountList=True)
                deleteFromTxTFile(ACCOUNT_LIST, [account])
                writeTxtFile(USED_LIST, [account])
        else:
            logger.error('No accounts to follow')

    def followFollowers(self, handle, p=cache.get('auto_followers_last_page'), accountList=False):
        user = self.api.get_user(handle)
        keywords = self.collect_keywords()
        logger.info(f"Following from account: Name: {user.name} - Screen Name: {user.screen_name} - Description: {user.description}")        

        for page in self.limit_handled(tweepy.Cursor(self.api.followers, id=user.id, page=p).pages()):
            p += 1
            if (accountList and (p >= 200)):
                break
            current_time = datetime.now()
            cache.set('twitter_last_run', current_time, 910)
            cache.set('auto_followers_last_page', p, None)

            logger.info(f"Twitter page {p}")
            for f in page:
                if (self.screen_follower(f, keywords)):
                    try:
                        friendship = self.api.lookup_friendships([f.id])[0]
                    except:
                        break
                    if (not(friendship.is_following or friendship.is_following_requested)):
                        self.api.create_friendship(f.id, screen_name=None, user_id=f.id, follow=False)
                        logger.info(f"Followed: {f.screen_name} - {f.followers_count} followers")                        

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
                    logger.info("Twitter run halted =", last_run.strftime("%H:%M:%S"))
                    logger.info(f"Next Twitter Run = {next_run.strftime('%H:%M:%S')}")

                    time.sleep(wait_time)
                else:
                    logger.warning('Twitter halt time not being cached.')
                    wait_time = (15 * 60)
                    next_run = (current_time + timedelta(minutes=15)).strftime("%H:%M:%S")
                    logger.info("Run Stopped =", current_time.strftime("%H:%M:%S"))
                    logger.info(f"Next Run = {next_run}")

                    time.sleep(wait_time)

    def collect_keywords(self):
        keywords = readJSONFile(KEYWORDS)

        for group, words in keywords.items():
            if (type(keywords[group]) == list):
                keywords[group].extend(wordVariator(words))
            else:
                for k, v in keywords[group].items():
                    keywords[group][k].extend(wordVariator(v))

        return keywords

    def screen_follower(self, f, keywords, trim=False):
        for nb in keywords['negative']['bio']:
            if (nb in f.description):
                if (trim):
                    reason='Contained negative word in bio'
                    return False, reason
                return False
        for ns in keywords['negative']['screen_name']:
            if (ns in f.screen_name):
                if (trim):
                    reason='Contained negative word in screen name'
                    return False, reason
                return False

        if (trim):
            """
            No red flags by this point.
            trimFollowers() may safely exit.
            """
            return True, None

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
        if (p == None):
            p=0

        for page in self.limit_handled(tweepy.Cursor(self.api.friends, id=user.id, page=p).pages()):
            p += 1
            current_time = datetime.now()
            cache.set('twitter_last_run', current_time, 910)
            cache.set('trim_followers_last_page', p, None)

            logger.info(f"Twitter page {p}")
            for f in page:   
                evaluation, reason = self.screen_follower(f, keywords, trim=True)  
                if (evaluation == False):
                    try:
                        self.api.destroy_friendship(f.id, screen_name=None, user_id=f.id)
                        logger.warning(f"Unfollowed {f.screen_name} - {f.followers_count} followers - Reason: {reason}")
                    except:
                        break
