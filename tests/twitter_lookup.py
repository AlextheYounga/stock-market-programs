from app.lab.fintwit.twitter_accounts import TwitterAccounts
from app.lab.fintwit.tweet import Tweet

account = TwitterAccounts()
tweet = Tweet()
# account.lookupAccount('@boohanmugullah1')
# tweet.analyze_tweet(1434350004727070722)
account.favorites_count('@boohanmugullah1')
account.favorites_count('@IndyJones2021')
account.favorites_count('@AlextheYounga')
tweet.analyze_favourites('@boohanmugullah1')

