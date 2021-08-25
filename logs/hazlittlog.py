import logging
import os
from app.functions import get_hazlitt_path

"""
This is my simple logging system I made. Django's logging system seems to make 
and already easy-to-use package more esoteric, and their settings file never seems to 
work as the docs say. 

I just create the settings I want in this function, pass whatever I want to call the log user, 
and call it day.
"""


def log(name):
    logging.basicConfig(
        filename=f"{get_hazlitt_path()}/logs/hazlitt.log",
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    logger = logging.getLogger(name)
    return logger


def twitter_log(name):
    logging.basicConfig(
        filename=f"{get_hazlitt_path()}/logs/twitter.log",
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    logger = logging.getLogger(name)
    return logger
