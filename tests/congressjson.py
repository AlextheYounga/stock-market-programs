import json
import sys
from app.functions import readJSONFile, writeJSONFile
from django.forms.models import model_to_dict
import django
from dotenv import load_dotenv
load_dotenv()
django.setup()
from app.database.models import Congress

jsonpath = 'app/lab/congress/database_congress.json'
reps = Congress.objects.all()

jdict = []
for rep in reps:
    dct = model_to_dict(rep)
    dct['date'] = dct['date'].strftime('%Y-%m-%d') if dct['date'] else None
    dct['filing_date'] = dct['filing_date'].strftime('%Y-%m-%d') if dct['filing_date'] else None
    jdict.append(dct)

writeJSONFile(jsonpath, jdict)
