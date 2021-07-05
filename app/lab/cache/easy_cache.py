import json
from colored import stylize
from ..core.functions import zipfolder
import cryptography
import sys
import os
import colored


class EasyCache:
    # My own storage system because this is just how I am.
    def __init__(self):
        self.path = 'lab/cache/ez'  # better for complex data
        self.json_path = f"{self.path}/ez.json"  # for simple data
        self.ledger_path = f"{self.path}/ledger.json"  # for simple data

    def get(key):
        path = pathfinder(EasyCache().path, key)
        if os.path.exists(path):
            return readCacheFile(path, key)

        with open(path) as jsonfile:
            cache = json.loads(jsonfile.read())

        jsonfile.close()
        return cache.get(key, False)

    def put(key, value):
        path = pathfinder(EasyCache().path, key)
        writeCacheFile(key, value, path)
        return True

    def quickstore(key, value):
        path = EasyCache().path
        with open(path) as jsonfile:
            cache = json.loads(jsonfile.read())
        jsonfile.close()

        cache[key] = value

        with open(path, 'w') as jsonfile:
            json.dump(cache, jsonfile)
        jsonfile.close()

        return True

    def clear():
        ez = EasyCache()
        os.remove(ez.path)
        os.mkdir(ez.path)
        with open(ez.json_path, 'w') as jsonfile:
            json.dump({}, jsonfile)
        with open(ez.ledger_path, 'w') as jsonfile:
            json.dump({}, jsonfile)

        print(stylize('Cache cleared!', colored.fg('green')))


def pathfinder(path, key):
    separators = ['-', '.', '_', ':', '->']
    for sep in separators:
        if (sep in key):
            levels = key.split(sep)

            for level in levels:
                path = path + f"/{level}"
                if not os.path.exists(path):
                    os.mkdir(path)
            break

    path = path + f"/{path.split('/')[-1]}.txt"

    return path


def readLedger():
    ledger = open(EasyCache().ledger_path, "r")    
    return json.loads(ledger.read())


def writeLedger(key, fmt):
    ledger = readLedger()
    ledger[key] = str(fmt)
    with open(EasyCache().ledger_path, "w") as jsonfile:
        jsonfile.write(json.dumps(ledger))


def checkFormat(key):
    ledger = readLedger()
    return ledger.get(key, False)


def readCacheFile(path, key):
    txtfile = open(path, "r")

    fmt = checkFormat(key)
    
    if (fmt):
        if (fmt == "<class 'list'>"):
            items = []
            txtfile = open(path, "r")
            for line in txtfile:                
                stripped_line = line.strip()
                line_list = stripped_line.split()
                items.append(str(line_list[0]))

            return list(dict.fromkeys(items))

        if (fmt == "<class 'str'>"):
            txtfile = open(path, "r")            
            return txtfile.read()

        if (fmt == "<class 'dict'>"):
            txtfile = open(path, "r")
            return json.loads(txtfile.read())


def writeCacheFile(key, data, path, append=False):
    # Appending function
    if (append):
        checked = readCacheFile(path, key)
        if (checked):
            lst = list(dict.fromkeys(checked + data))

    fmt = type(data)
    writeLedger(key, fmt)
    txtfile = path
    # os.remove(txtfile)
    with open(txtfile, 'w') as f:        
        if (fmt == list):
            for item in lst:
                f.write("%s\n" % item)
        if (fmt == str):
            f.write(data)
        if (fmt == dict):
            f.write(json.dumps(data))

    return True
