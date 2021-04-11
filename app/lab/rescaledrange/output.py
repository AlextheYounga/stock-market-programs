import csv
import os
import texttable
from .functions import *
from datetime import datetime


def writeCSV(fractal_results, refScales, resultsfile, append):
    now = datetime.now()
    datenow = now.strftime("%m-%d-%Y %H:%M:%S")
    write_results = csv.writer(resultsfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    if (append == True):
        for x in range(2):
            write_results.writerow([''])

    write_results.writerow(['Fractal Statistics', 'Generated {}'.format(datenow)])

    results_scales = []
    headers = []
    for scale, stats in fractal_results['regressionResults'].items():
        results_scales.append(scale)
    for header, value in fractal_results['regressionResults'][results_scales[0]].items():
        headers.append(header)

    # Making lists from each set of data
    hurstExponents = scaled_data_collector(results_scales, fractal_results['regressionResults'], 'hurstExponent')
    fractalDimensions = scaled_data_collector(results_scales, fractal_results['regressionResults'], 'fractalDimension')
    rSquared = scaled_data_collector(results_scales, fractal_results['regressionResults'], 'r-squared')
    pValues = scaled_data_collector(results_scales, fractal_results['regressionResults'], 'p-value')
    standardErrors = scaled_data_collector(results_scales, fractal_results['regressionResults'], 'standardError')
    # Zipping all lists into row
    rows = zip(results_scales, hurstExponents, fractalDimensions, rSquared, pValues, standardErrors)

    # Writing Headers
    headers.insert(0, 'Scale')
    write_results.writerow(headers)

    # Writing Data Columns
    for row in rows:
        write_results.writerow(row)

    # Rescale Range
    write_results.writerow('')
    write_results.writerow(['Rescale Range:'])
    write_results.writerow(['Scale', 'RescaleRange'])
    for scale, rr in fractal_results['rescaleRange'].items():
        write_results.writerow(['fullSeries / {} : {} day chunks'.format(scale, refScales[scale]), rr])


def exportFractal(fractal_results, refScales):
    output_file = 'lab/rescaledrange/output/fractal_results.csv'

    # If output file does not exist, create new.
    if (not os.path.exists(output_file)):
        with open(output_file, mode='w') as resultsfile:
            writeCSV(fractal_results, refScales, resultsfile, append=False)

    # If output file already exists, append results, else generate new file.
    else:
        with open(output_file, mode='a') as resultsfile:
            writeCSV(fractal_results, refScales, resultsfile, append=True)


def setWidths(data):
    """ 
    Parameters
    ----------
    data :  list
    """
    if (type(data) == list):
        widths = []
        for word in data:
            length = len(word)
            if (word == 'Scale'):
                length = length * 6
            widths.append(length)
        return widths
    return False


def outputTable(fractal_results, refScales):
    print('Fractal Statistics:')

    results_scales = []
    headers = []
    for scale, stats in fractal_results['regressionResults'].items():
        results_scales.append(scale)
    for header, value in fractal_results['regressionResults'][results_scales[0]].items():
        headers.append(header)

    # Making lists from each set of data
    hurstExponents = scaled_data_collector(results_scales, fractal_results['regressionResults'], 'hurstExponent')
    fractalDimensions = scaled_data_collector(results_scales, fractal_results['regressionResults'], 'fractalDimension')
    rSquared = scaled_data_collector(results_scales, fractal_results['regressionResults'], 'r-squared')
    pValues = scaled_data_collector(results_scales, fractal_results['regressionResults'], 'p-value')
    standardErrors = scaled_data_collector(results_scales, fractal_results['regressionResults'], 'standardError')
    # Zipping all lists into row
    rows = zip(results_scales, hurstExponents, fractalDimensions, rSquared, pValues, standardErrors)

    table = texttable.Texttable()
    # Writing Headers
    headers.insert(0, 'Scale')
    table.header(headers)
    table.set_cols_width(setWidths(headers))

    for r in rows:
        table.add_rows([list(r)], header=False)

    # Draw statistics table
    print(table.draw())
    print("\n")

    # Rescale Range
    print('Rescaled Range:')
    table = texttable.Texttable()
    headers = ['Scale', 'RescaleRange']
    table.header(headers)
    table.set_cols_width(setWidths(headers))

    for scale, rr in fractal_results['rescaleRange'].items():        
        table.add_rows([['fullSeries / {} : {} day chunks'.format(scale, refScales[scale]), rr]], header=False)

    print(table.draw())
