import csv
import os
from datetime import datetime


def writeCSV(donchian_range, ticker, resultsfile, append):
    now = datetime.now()
    datenow = now.strftime("%m-%d-%Y %H:%M:%S")
    write_results = csv.writer(resultsfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    if (append == True):
        for x in range(2):
            write_results.writerow([''])

    write_results.writerow(['{} Range Generated {}'.format(ticker, datenow)])
    headers = list(donchian_range.keys())
    data = list(donchian_range.values())

    write_results.writerow(headers)
    write_results.writerow(data)


def exportDonchian(donchian_range, ticker):
    output_file = 'lab/donchian/output/donchianrange.csv'

# If output file does not exist, create new.
    if (not os.path.exists(output_file)):
        with open(output_file, mode='w') as resultsfile:
            writeCSV(donchian_range, ticker, resultsfile, append=False)

    # If file already exists, append to file
    else:
        with open(output_file, mode='a') as resultsfile:
            write_results = csv.writer(resultsfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            writeCSV(donchian_range, ticker, resultsfile, append=True)
