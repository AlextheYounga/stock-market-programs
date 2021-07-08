import redis
from queue import SimpleQueue
from lab.core.functions import unzip_folder, zipfolder
import progressbar
import colored
from colored import stylize
import json
import sys
import os

LEDGER = 'app/redisdb/ledger.txt'
class Rdb():
    def put(key, value):
        r = redis.Redis(host='localhost', port=6379, db=0, charset="utf-8", decode_responses=True)
        r.set(key, value)
        sq = SimpleQueue()    
        sq.put(writeLedger([key]))

    def import_rdb():
        directory = "app/database/redisdb/imports/"
        filepath = "app/database/redisdb/imports/rdb_export.zip"
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


    def export_rdb():
        if (os.path.exists("lab/redisdb/export/rdb_export.zip")):
            os.remove("lab/redisdb/export/rdb_export.zip")
            
        r = redis.Redis(host='localhost', port=6379, db=0, charset="utf-8", decode_responses=True)
        all_keys = readLedger()

        for key in all_keys:
            dictexport = {}
            filename = "{}_rdb.json".format(key.split('-')[0])
            json_output = "lab/redisdb/export/"+filename
            print(stylize("Exporting keys containing "+key, colored.fg("yellow")))
            for k in progressbar.progressbar(r.scan_iter(key)):
                value = r.get(k)
                try:
                    dictexport[k] = json.loads(value)
                except json.decoder.JSONDecodeError:
                    dictexport[k] = value

            with open(json_output, 'w') as json_file:
                json.dump(dictexport, json_file)
                print(stylize("Exported "+filename, colored.fg("green")))

        zipfolder("lab/redisdb/export/", "rdb_export.zip")
        print(stylize("Zipped file", colored.fg("green")))

def writeLedger(lst):
    # Appending function
    check = readLedger(LEDGER)
    if (check):
        lst = list(dict.fromkeys(check + lst))

    with open(LEDGER, 'w') as f:
        for item in lst:
            f.write("%s\n" % item)

def readLedger():
    items = []
    txtfile = open(LEDGER, "r")
    for line in txtfile:
        stripped_line = line.strip()
        line_list = stripped_line.split()
        items.append(str(line_list[0]))

    return list(dict.fromkeys(items))