
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
from app.database.models import Congress, Stock
from app.lab.core.api.senatewatcher import SenateWatcher


class CongressPortfolio():

    def calculate(self, rep):
        records = Congress.objects.filter(first_name=rep.first_name)
