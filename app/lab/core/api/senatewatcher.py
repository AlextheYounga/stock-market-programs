import xml.etree.ElementTree as ET
from app.lab.core.output import printFullTable, printTable
import requests
import sys
import json
import os
from logs.hazlittlog import log

logger = log('SenateWatcherAPI')

class SenateWatcher():

    def __init__(self):
        self.domain = 'https://senate-stock-watcher-data.s3-us-west-2.amazonaws.com'
        self.settings = {'timeout': 5}

    def lastReport(self, print_results=False):
        # https://senate-stock-watcher-data.s3-us-west-2.amazonaws.com/data/transaction_report_for_07_23_2021.json
        latest = self.fileMap()[0]
        url = f"{self.domain}/{latest}"
        print(url)
        try:
            response = requests.get(url, **self.settings).json()
        except:
            logger.error("Unexpected error:", sys.exc_info()[0])
            return None
                

        if (print_results):
            printFullTable(response, struct='dictlist')

        return response

    def fileMap(self):
        # https://senate-stock-watcher-data.s3-us-west-2.amazonaws.com/aggregate/filemap.xml
        fmap = []
        url = f"{self.domain}/aggregate/filemap.xml"
        try:
            response = requests.get(url, **self.settings)
        except:
            logger.error("Unexpected error:", sys.exc_info()[0])
            return None

        root = ET.fromstring(response.content)
        for child in root.iter('Key'):
            fmap.append(child.text)

        return fmap
