from dotenv import load_dotenv
from .functions import getETFs
from app.lab.fintwit.fintwit import Fintwit
from app.functions import chunks
from app.lab.core.api.batch import quoteStatsBatchRequest
from app.lab.core.output import printFullTable
import progressbar
import json
import time
import sys
from datetime import date
load_dotenv()

class Macro():
    # TODO: Turn into class