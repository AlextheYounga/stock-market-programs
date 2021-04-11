import json
import sys
import redis
from .methodology import sectors
from ..core.output import printTabs
from ..database.hp.update_prices import batch_refresh_prices


def refresh_sector_prices():
    batch_refresh_prices(batch=sectors(), timeframe='max')


def fetch_names():
    """
    python -c "from lab.inflation.functions import fetch_names; print(fetch_names())"
    """
    r = redis.Redis(host='localhost', port=6379, db=0, charset="utf-8", decode_responses=True)

    companies = {}
    for ticker in sectors():    
        companies[ticker] = r.get('stock-'+ticker+'name')

    printTabs(companies)
