# Task Scheduler Windows Python Path
# C:\Users\alexy\Documents\Development\Python\hazlitt-data\env\Scripts\python C:\Users\alexy\Documents\Development\Python\hazlitt-data\tasks\fedwatcher.py

import sys
sys.path.append('C:/Users/alexy/Documents/Development/Python/hazlitt-data')
from app.lab.core.api.fred import Fred
from hazlitt_log import log

print("RUNNING FED WATCHER... \n")
logger = log('FedWatcher')
logger.info('Running fed watcher')
fed = Fred()
fed.checkLatest('balance-sheet', tweet=True)
series = fed.series('balance-sheet')
fed.store('balance-sheet', series)
