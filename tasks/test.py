# Task Scheduler Windows Python Path
# C:\Users\alexy\Documents\Development\Python\hazlitt-data\env\Scripts\python

import sys
import os
if os.name == 'nt': #windows
	sys.path.append('C:/Users/alexy/Documents/Development/Python/hazlitt-data')
from log_handler import log
from app.lab.fintwit.tweet import Tweet

twit = Tweet()
tweet = "This is an automation test"
twit.send(tweet, prompt=True)

logger = log('Task Test')
logger.info('This is a twitter test')