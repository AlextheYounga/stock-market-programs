# Task Scheduler Windows Python Path
# C:\Users\alexy\Documents\Development\Python\hazlitt-data\env\Scripts\python C:\Users\alexy\Documents\Development\Python\hazlitt-data\tasks\congresswatcher.py

import sys
sys.path.append('C:/Users/alexy/Documents/Development/Python/hazlitt-data')
from app.lab.core.api.congresswatcher import CongressWatcher
from hazlitt_log import log

print("RUNNING CONGRESS WATCHER... \n")
logger = log('CongressWatcher')
sw = CongressWatcher(branch='senate')
hw = CongressWatcher(branch='house')

sentrades = sw.scanReports()
if (sentrades):
    sw.tweet(sentrades)
    
    for senator in sentrades:
        logger.info(f"New senator transaction {senator.first_name} {senator.last_name} {senator.ticker or 'No ticker'} {senator.date or 'No date'}")
        
else:
    logger.info('No new senate transactions')

reptrades = hw.scanReports()
if (reptrades):
    hw.tweet(reptrades)

    for rep in reptrades:
        logger.info(f"New house rep transaction {rep.first_name} {rep.last_name} {rep.ticker or 'No ticker'} {rep.date or 'No date'}")
        
else:
    logger.info('No new house transactions')
