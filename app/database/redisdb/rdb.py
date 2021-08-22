import redis
class Rdb():    
    def setup(self):
        r = redis.Redis(
            host='localhost', 
            port=6379, 
            db=0,
            charset="utf-8",
            decode_responses=True
        )
        return r

    def imports(self):
        import os
        import json
        import progressbar
        import colored
        from colored import stylize
        from app.functions import unzip_folder
        r = self.setup()

        directory = "app/database/redisdb/imports/"
        filepath = "app/database/redisdb/imports/rdb_export.zip"
        if (os.path.exists(filepath)):
            unzip_folder(directory, filepath)

            for root, dirs, files in os.walk(directory+"export/"):
                for file in files:
                    with open(directory+"export/"+file) as jsonfile:
                        print(stylize("Saving key values from " +
                              file, colored.fg("yellow")))
                        rdb_data = json.loads(jsonfile.read())
                        keys = rdb_data.keys()
                        for key in progressbar.progressbar(keys):
                            try:
                               r.set(key, json.dumps(rdb_data[key]))
                            except json.decoder.JSONDecodeError:
                               r.set(key, rdb_data[key])
                print(stylize("Saved "+file, colored.fg("green")))

        print(stylize("Import complete", colored.fg("green")))

    def export(self):
        import os
        import json
        import progressbar
        import colored
        from colored import stylize
        from app.functions import zipfolder
        r = self.setup()

        if (os.path.exists("lab/redisdb/export/rdb_export.zip")):
            os.remove("lab/redisdb/export/rdb_export.zip")

        all_keys =r.keys()

        for key in all_keys:
            dictexport = {}
            filename = "{}_rdb.json".format(key.split('-')[0])
            json_output = "lab/redisdb/export/"+filename
            print(stylize("Exporting keys containing "+key, colored.fg("yellow")))
            for k in progressbar.progressbar(self.r.scan_iter(key)):
                value =r.get(k)
                try:
                    dictexport[k] = json.loads(value)
                except json.decoder.JSONDecodeError:
                    dictexport[k] = value

            with open(json_output, 'w') as json_file:
                json.dump(dictexport, json_file)
                print(stylize("Exported "+filename, colored.fg("green")))

        zipfolder("lab/redisdb/export/", "rdb_export.zip")
        print(stylize("Zipped file", colored.fg("green")))

