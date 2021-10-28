# Task Scheduler Windows Python Path
# C:\Users\alexy\Documents\Development\Python\hazlitt-data\env\Scripts\python

import sys
import os
get_hazlitt_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
if (sys.platform == 'win32'):
    sys.path.append(f"{get_hazlitt_path}")
from app.lab.fintwit.twitter_accounts import TwitterAccounts

accounts = TwitterAccounts()
accounts.trimFollowers()