# Task Scheduler Windows Python Path
# C:\Users\alexy\Documents\Development\Python\hazlitt-data\env\Scripts\python

import sys
sys.path.append('C:/Users/alexy/Documents/Development/Python/hazlitt-data')
from app.lab.fintwit.twitter_accounts import TwitterAccounts

accounts = TwitterAccounts()
accounts.followList()