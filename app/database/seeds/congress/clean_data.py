import sys
import os
import json
import datetime
import django
from dotenv import load_dotenv
load_dotenv()
django.setup()
from app.database.models import Congress

# A patch job to clean up any remaining impurities in the data.

reps = Congress.objects.all()
for rep in reps:
    if (rep.ticker == '--'):
        rep.ticker = None
        rep.save()
        print(f"Updated {rep.first_name} {rep.last_name} at {rep.date}")
    if (rep.owner == '--'):
        rep.owner = None
        rep.save()
        print(f"Updated {rep.first_name} {rep.last_name} at {rep.date}")

    
    


        