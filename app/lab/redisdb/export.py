import json
import redis
from ..core.functions import zipfolder
from datetime import datetime, date, timedelta
from .schema import rdb_schema
import progressbar
import colored
from colored import stylize 
import sys
import os


def export_rdb():
    if (os.path.exists("lab/redisdb/export/rdb_export.zip")):
        os.remove("lab/redisdb/export/rdb_export.zip")
        
    r = redis.Redis(host='localhost', port=6379, db=0, charset="utf-8", decode_responses=True)
    roots = rdb_schema()

    for root in roots:
        dictexport = {}
        filename = "{}_rdb.json".format(root.split('-')[0])
        json_output = "lab/redisdb/export/"+filename
        print(stylize("Exporting keys containing "+root, colored.fg("yellow")))
        for key in progressbar.progressbar(r.scan_iter(root)):
            value = r.get(key)
            try:
                dictexport[key] = json.loads(value)
            except json.decoder.JSONDecodeError:
                dictexport[key] = value

        with open(json_output, 'w') as json_file:
            json.dump(dictexport, json_file)
            print(stylize("Exported "+filename, colored.fg("green")))

    zipfolder("lab/redisdb/export/", "rdb_export.zip")
    print(stylize("Zipped file", colored.fg("green")))

