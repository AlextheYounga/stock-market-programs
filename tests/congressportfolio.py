import json
import sys
import statistics
import django
from dotenv import load_dotenv
load_dotenv()
django.setup()
from app.lab.congress.portfolio import PortfolioBuilder
from app.database.models import Congress, CongressPortfolio, CongressTransaction

pb = PortfolioBuilder()
pb.build()
pb.calculateGains()
# CongressPortfolio().mostBoughtTicker()
# print(CongressTransaction().top_trader())
