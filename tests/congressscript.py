import json
import sys
import statistics
import django
from dotenv import load_dotenv
load_dotenv()
django.setup()
from app.lab.congress.portfolio import PortfolioBuilder
from app.database.models import Congress, CongressPortfolio, CongressTransaction
from app.lab.core.api.congresswatcher import CongressWatcher


# hw = HouseWatcher()
# print(hw.getLatest())

sw = CongressWatcher(branch='senate')
sw.getLatest()