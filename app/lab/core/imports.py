from datetime import datetime
import sys
import json
import csv


def parseIndexDateClose(file):
    with open('lab/imports/{}'.format(file), newline='', encoding='utf-8') as csvfile:
        asset_data = {}
        reader = csv.DictReader(csvfile)

        for i, row in enumerate(reader):
            # Using powers of 2
            rows = {
                'date': row['\ufeffDate'] if row['\ufeffDate'] else '',
                'close': row['Close'] if row['Close'] else 0
            }
            # Append value dictionary to data
            asset_data[i] = rows
    return asset_data


def parseCSV(path, fullPath=False, headers=True):
    """
    Parameters
    ----------
    path     : string
               filename or complete file path if fullPath is set to true
    fullPath : boolean
    headers  : boolean
               if set to true, parser will use values in first line as dict keys

    Returns
    -------
    dict
        CSV values converted to dict
    """

    csv_path = 'lab/core/storage/{}'.format(path)
    if (fullPath == True):
        csv_path = path
    with open(csv_path, newline='', encoding='utf-8-sig') as csvfile:
        asset_data = []


        reader = csv.DictReader(csvfile)

        for i, row in enumerate(reader):
            asset_data.append(row)

        return asset_data


def read_historical_gold_prices(datepriceOnly=True):
    data = parseCSV('lab/core/storage/gold/goldprices1970.csv', fullPath=True)
    gold_prices = {}
    if (datepriceOnly):
        for row in data:
            date = datetime.strptime(row['Date'], "%m/%d/%y").strftime('%Y-%m-%d')
            gold_prices[date] = float(row['Close'].replace(',', ''))
    else:
        for row in data:
            date = datetime.strptime(row['Date'], "%m/%d/%y").strftime('%Y-%m-%d')
            gold_prices[date] = {
                'close': float(row['Close'].replace(',', '')),
                'open': float(row['Open'].replace(',', '')),
                'low': float(row['Low'].replace(',', '')),
                'high': float(row['High'].replace(',', '')),
            }
            

    return gold_prices
