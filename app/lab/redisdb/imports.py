import json
import redis
from ..core.functions import unzip_folder
from datetime import datetime, date, timedelta
from .schema import rdb_schema
import progressbar
import colored
from colored import stylize
import sys
import os

def import_rdb():
    directory = "lab/redisdb/imports/"
    filepath = "lab/redisdb/imports/rdb_export.zip"
    if (os.path.exists(filepath)):

        unzip_folder(directory, filepath)
        r = redis.Redis(host='localhost', port=6379, db=0, charset="utf-8", decode_responses=True)
        
        for root, dirs, files in os.walk(directory+"export/"):
            for file in files:
                with open(directory+"export/"+file) as jsonfile:
                    print(stylize("Saving key values from "+file, colored.fg("yellow")))
                    rdb_data = json.loads(jsonfile.read())
                    keys = rdb_data.keys()
                    for key in progressbar.progressbar(keys):
                        try:
                            r.set(key, json.dumps(rdb_data[key]))
                        except json.decoder.JSONDecodeError:
                            r.set(key, rdb_data[key])
            print(stylize("Saved "+file, colored.fg("green")))

    print(stylize("Import complete", colored.fg("green")))

