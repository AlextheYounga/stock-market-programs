from iexfinance.stocks import get_market_gainers
from dotenv import load_dotenv
from ..core.output import printTable
from ..database.functions import dynamicUpdateCreate
import requests
import json
import sys
load_dotenv()

gainers = get_market_gainers()
print(gainers)

