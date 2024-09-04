from app.lab.core.output import printTabs
from app.functions import get_app_path, readJSONFile, compare_dicts
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import pylab
import datetime
import statistics
import sys
import json
from dotenv import load_dotenv
load_dotenv()

balancesheet = f"{get_app_path()}/app/lab/fed/storage/balancesheet.json"
balancesheetJSON = readJSONFile(balancesheet)

monthly = {}
increases = {}
months = []
increases = []

for day, figures in balancesheetJSON.items():
    date = datetime.datetime.strptime(day, '%Y-%m-%d')
    if (f"{date.month}-{date.year}" not in monthly):
        monthly[f"{date.month}-{date.year}"] = [float(figures["value"])]
        continue
    monthly[f"{date.month}-{date.year}"].append(float(figures["value"]))

for month, values in monthly.items():
    months.append(month)
    increases.append(max(values) - min(values))


def graph(x, y):
    # fig = plt.subplots(figsize=(12, 7))
    plt.plot(x, y, label='increase')
    plt.xlabel('x Month')
    plt.ylabel('y Increase')
    plt.title("Monthly Increases to Balance Sheet")
    # plt.xticks(np.arange(0, len(x)+1, 126))
    plt.xticks(rotation=45)

    # plt.show()
    plt.draw()
    plt.pause(1)
    input("<Hit Enter To Close>")
    plt.close()

graph(months[-36:], increases[-36:])