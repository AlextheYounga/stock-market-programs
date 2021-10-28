# Task Scheduler Windows Python Path
# C:\Users\alexy\Documents\Development\Python\hazlitt-data\env\Scripts\python

import sys
import os
get_hazlitt_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
if (sys.platform == 'win32'):
    sys.path.append(f"{get_hazlitt_path}")
from hazlitt_log import log
from app.lab.fintwit.tweet import Tweet

twit = Tweet()
tweet = "This is an automation test"
twit.send(tweet, prompt=True)

logger = log('Task Test')
logger.info('This is a twitter test')