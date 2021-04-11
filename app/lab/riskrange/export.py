import csv
import os
from datetime import datetime
from datetime import date
import sys


def writeCSV(stats):
    today = date.today().strftime('%m-%d')
    output_file = "lab/exports/portfolio/signals{}.csv".format(today)
    with open(output_file, mode='w') as resultsfile:
        write_results = csv.writer(resultsfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        write_results.writerow([
            'Ticker',
            stats.keys()
        ])
        for ticker, data in stats.items():
            write_results.writerow([
                ticker,
                data.values()
            ])
