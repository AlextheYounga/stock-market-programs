
from app.lab.core.output import printFullTable
from app.functions import chunks, filterNone
from app.lab.core.api.iex import IEX
import sys
import os
import json
import datetime
from app.database.redisdb.rdb import Rdb
import django
from dotenv import load_dotenv
load_dotenv()
django.setup()
from app.database.models import Congress, CongressTransaction, Stock
from app.lab.core.api.senatewatcher import SenateWatcher


class CongressPortfolio():

    def calculate(self):
        members = Congress.objects.all()
        for member in members:
            transactions = member.congresstransaction_set.all().order_by('date')            
            for tr in transactions:
                print('')

cp = CongressPortfolio()
cp.calculate()