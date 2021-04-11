import json
import sys
import statistics
from scipy import stats
import pandas as pd
import numpy as np


def scaled_data_collector(scales, data, key):
    """
    Similar to the extract_data function; burrows into nested dict, (nested by scale in this case)
    to find particular values. The function will search and return all matching values and return in a list. The key parameter can 
    be an array, in which case the function will burrow into the nested dict using those keys. If a value is at dict[key1][key2] = value,
    then you can insert [key1, key2] into the key parameter.

    Parameters
    ----------
    scales    :dict
                dictionary object of scales + days in scale (see scales function)
    data      :dict
                fully built range stats, ()
    key       :array|string
                key or keys to search for.

    Returns
    -------
    list
        list of all items that match key
    """
    if (type(scales) == list):
        values = []
        if (type(key) == list):
            if len(key) == 2:
                for scale in scales:
                    value = float(data[scale][key[0]][key[1]])
                    values.append(value)
            if len(key) == 3:
                for scale in scales:
                    value = float(data[scale][key[0]][key[1]][key[2]])
                    values.append(value)
            if len(key) == 4:
                for scale in scales:
                    value = float(data[scale][key[0]][key[1]][key[2]][key[3]])
                    values.append(value)
            if len(key) > 4:
                return 'Nest level too deep to retrieve via function.'
        else:
            for scale in scales:
                value = float(data[scale][key])
                values.append(value)

    else:
        values = []
        if (type(key) == list):
            if len(key) == 2:
                for scale, days in scales.items():
                    value = float(data[scale][key[0]][key[1]])
                    values.append(value)
            if len(key) == 3:
                for scale, days in scales.items():
                    value = float(data[scale][key[0]][key[1]][key[2]])
                    values.append(value)
            if len(key) == 4:
                for scale, days in scales.items():
                    value = float(data[scale][key[0]][key[1]][key[2]][key[3]])
                    values.append(value)
            if len(key) > 4:
                return 'Nest level too deep to retrieve via function.'
        else:
            for scale, days in scales.items():
                value = float(data[scale][key])
                values.append(value)

    return values


def exponential_scales(count, exponent, limit):
    """
    The function will create exponential scales, multiplying the denominator by an exponent each loop.
    The limit param will define how many loops the function runs, for how many scales the user wants.

    (Too complicated, didn't read): The best way to picture what this function is doing: picture an entire stock market graph,
    and imagine zooming into that graph with a telescope. This function is creating the lenses in which you're viewing that graph.
    Each scale is a new lens you're adding to that telescope to get a closer look at smaller sections of the graph, and each lens added
    gives an exponentially microscopic view. Say the first lens lets you view the entire graph, then the second lens lets you view 1/3, 
    then 1/9, then 1/27, etc.

    Parameters
    ----------
    count    :int
                total number of items in main list of prices
    exponent  :int
                Exponent for which the scale will be based on. First scale will always be the entirety of the list
                Ex: if exponent=3 then scales=[1, 3, 9, 27, 81, 243]
    limit     :int
                *For best results, 5 or 6*
                The scales shouldn't go on forever, in general, 5 or 6 is a good number here. 

    Returns
    -------
    dict
        Dictionary of scales and number of items inside each scale.
    """
    e = exponent
    itr = []
    scales = {}
    for i in range(limit):
        if (i == 0):
            scales[i + 1] = count
            itr.append(i + 1)
        else:
            scales[(itr[i - 1] * e)] = int(count / (itr[i - 1] * e))
            itr.append(itr[i - 1] * e)

    return scales


def linear_scales(count, addend, limit):
    """
    The function will create linear scales, adding a number on each loop. This function is the same as 
    exponential_scales() except the scales have a perfectly constant slope.
    The limit param will define how many loops the function runs, for how many scales the user wants.

    For more details, see exponential_scales() function

    Parameters
    ----------
    count    :int
                total number of items in main list of prices
    addend  :int
                Number for which the scale will be based on. First scale will always be the entirety of the list
                Ex: if exponent=2 then scales=[1, 2, 4, 6, 8]
    limit     :int
                *For best results, 5 or 6*
                The scales shouldn't go on forever, in general, 5 or 6 is a good number here. 

    Returns
    -------
    dict
        Dictionary of scales and number of items inside each scale.
    """
    x = addend
    itr = []
    scales = {}
    for i in range(limit):
        if (i == 0):
            scales[i + 1] = count
            itr.append(i + 1)
        else:
            scales[(itr[i - 1] + x)] = int(count / (itr[i - 1] + x))
            itr.append(itr[i - 1] + x)

    return scales


def returns_calculator(prices):
    """
    Calculates daily returns of prices in list

    Parameters
    ----------
    prices    :list
                total list of prices

    Returns
    -------
    list
        List of daily returns based on list of prices. 
        *Make sure prices are ordered in descending order*
    """
    pricesdf = pd.DataFrame(prices)
    returnsdf = pricesdf[:-1].values / pricesdf[1:] - 1
    return returnsdf.iloc[:, 0].tolist()


def chunks(lst, n):
    """
    Creates chunks from list, (usually based on scales)

    Parameters
    ----------
    lst    :list
            full list of items
    n      :int
            number of items in each chunk

    Returns
    -------
    list of chunks
    """
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def backward_chunks(lst, n):
    """
    Creates chunks from list, (usually based on scales), starting from the bottom of list

    Parameters
    ----------
    lst    :list
            full list of items
    n      :int
            number of items in each chunk

    Returns
    -------
    list of chunks starting from the bottom of the list.
    """
    start = 0
    for end in range(len(lst) % n, len(lst)+1, n):
        yield lst[start:end]
        start = end


def chunked_averages(lst, n):
    """
    Convert list to chunks, (usually based on scales), and return average of each chunk

    Parameters
    ----------
    lst    :list
            full list of items
    n      :int
            number of items in each chunk

    Returns
    -------
    dict containing each chunk's average
    """
    chunked_list = list(chunks(lst, n))
    averages = {}
    for i, chunk in enumerate(chunked_list):
        mean = statistics.mean(chunk)
        averages[i] = mean

    return averages


def deviations_calculator(returns, scales):
    """
    Calculates the deviation from the mean of each item in list of returns.
    Calculations are done in chunks according to scales.

    Parameters
    ----------
    returns       :list
                    full list of returns
    scales        :dict
                    scales dict object returned from either exponential_scales() or linear_scales()

    Returns
    -------
    chunked list of deviations, chunks are according to scale 
    """
    deviations = {}
    for scale, days in scales.items():
        deviations[scale] = []
        chunked_returns = chunks(returns, days)
        chunked_means = chunked_averages(returns, days)
        for index, chunk in enumerate(chunked_returns):
            for i, value in enumerate(chunk):
                deviation = float(value) - float(chunked_means[index])
                deviations[scale].append(deviation)
    return deviations


def running_totals_calculator(deviations, scales):
    """
    Calculates running totals of deviations from the mean.
    Calculations are done in chunks according to scales.

    Parameters
    ----------
    deviations    :list
                    chunked list of deviations
    scales        :dict
                    scales dict object returned from either exponential_scales() or linear_scales()

    Returns
    -------
    chunked list of running totals, chunks are according to scale  
    """
    running_totals = {}
    for scale, days in scales.items():
        running_totals[scale] = []
        for i, value in enumerate(deviations[scale]):
            if (i == 0):
                running_totals[scale].append(value)
                continue
            rt = value + running_totals[scale][i - 1]
            running_totals[scale].append(rt)
    return running_totals


def chunked_devs(lst, n):
    """
    Convert list to chunks, (usually based on scales), and return standard deviation of each chunk

    Parameters
    ----------
    lst    :list
            full list of items
    n      :int
            number of items in each chunk

    Returns
    -------
    dict containing each chunk's stdev
    """
    chunked_list = list(chunks(lst, n))
    stDevs = {}
    for i, chunk in enumerate(chunked_list):
        # Checking if chunk is more than one item; stDev needs more than one.
        if (len(chunk) > 1):
            dev = statistics.stdev(chunk)
            stDevs[i] = dev
        else:
            stDevs[i] = 0

    return stDevs


def chunked_range(lst, n):
    """
    Convert list to chunks, (usually based on scales), and return dict of minimum/maximum/full range of each chunk

    Parameters
    ----------
    lst    :list
            full list of items
    n      :int
            number of items in each chunk

    Returns
    -------
    dict containing each chunk's min, max, and range
    """
    chunked_list = list(chunks(lst, n))
    if (len(chunked_list[-1]) == 1):
        remainder = chunked_list[-1].pop(0)
        chunked_list[-2].append(remainder)
        del chunked_list[-1]
    chunk_range = {}
    chunk_range['minimum'] = {}
    chunk_range['maximum'] = {}
    chunk_range['range'] = {}
    for i, chunk in enumerate(chunked_list):
        chunk_range['minimum'][i] = min(chunk)
        chunk_range['maximum'][i] = max(chunk)
        chunk_range['range'][i] = (max(chunk) - min(chunk))

    return chunk_range


# Fractal Analysis Functions
def standard_fractal_sections(x, y):
    """
    This is the classic way of looking at the rescaled range data, breaking the picture into easily understandable chunks
    of 1/2 and 1/3

    Parameters
    ----------
    x      :list
            list of log10 values for each chunk in scale
    y      :list
            list of log10 values for each chunk in scale

    Returns
    -------
    dict broken into the arbitrary scales listed above
    """
    if len(x) != len(y):
        return "X and Y values contain disproportionate counts"

    half = int(len(x) / 2)
    third = int(len(x) / 3)

    fractalScales = {
        'pastHalfSeries': {
            'x': list(chunks(x, half))[0],
            'y': list(chunks(y, half))[0]
        },
        'currentHalfSeries': {
            'x': list(chunks(x, half))[1],
            'y': list(chunks(y, half))[1]
        },
        'pastThirdSeries': {
            'x': list(chunks(x, third))[0],
            'y': list(chunks(y, third))[0]
        },
        'middleThirdSeries': {
            'x': list(chunks(x, third))[1],
            'y': list(chunks(y, third))[1]
        },
        'currentThirdSeries': {
            'x': list(chunks(x, third))[2],
            'y': list(chunks(y, third))[2]
        },
    }
    return fractalScales


def trading_fractal_sections(x, y):
    """
    This is an arbitrary way of looking at the data, but it's being organized in a way that may give a better impression
    of the short run., making it potentially more optimized for trading. The way in which you want to view the data is completely
    dependent on the user's motives.

    'trade': periods of 3 weeks
    'month': periods of one month
    'trend': periods of 3 months
    'tail':  periods of 3 years

    Parameters
    ----------
    x      :list
            list of log10 values for each chunk in scale
    y      :list
            list of log10 values for each chunk in scale

    Returns
    -------
    dict broken into the arbitrary scales listed above
    """
    if len(x) != len(y):
        return "X and Y values contain disproportionate counts"

    fractal_scales = {
        'trade': {
            'x': list(backward_chunks(x, 2))[-1],
            'y': list(backward_chunks(y, 2))[-1],
        },
        'month': {
            'x': list(backward_chunks(x, 3))[-1],
            'y': list(backward_chunks(y, 3))[-1],
        },
        'trend': {
            'x': list(backward_chunks(x, 4))[-1],
            'y': list(backward_chunks(y, 4))[-1],
        },
        'tail': {
            'x': list(backward_chunks(x, 5))[-1],
            'y': list(backward_chunks(y, 5))[-1],
        },
    }
    print(json.dumps(fractal_scales, indent=1))
    sys.exit()
    return fractal_scales


def quarter_sections(x, y):
    """

    Parameters
    ----------
    x      :list
            list of log10 values for each chunk in scale
    y      :list
            list of log10 values for each chunk in scale

    Returns
    -------
    dict broken into the arbitrary scales listed above
    """
    if len(x) != len(y):
        return "X and Y values contain disproportionate counts"

    half = int(len(x) / 2)
    fourth = int(len(x) / 4)

    fractalScales = {
        'pastHalfSeries': {
            'x': list(chunks(x, half))[0],
            'y': list(chunks(y, half))[0]
        },
        'currentHalfSeries': {
            'x': list(chunks(x, half))[1],
            'y': list(chunks(y, half))[1]
        },
        'Q1': {
            'x': list(chunks(x, fourth))[0],
            'y': list(chunks(y, fourth))[0]
        },
        'Q2': {
            'x': list(chunks(x, fourth))[1],
            'y': list(chunks(y, fourth))[1]
        },
        'Q3': {
            'x': list(chunks(x, fourth))[2],
            'y': list(chunks(y, fourth))[2]
        },
        'Q4': {
            'x': list(chunks(x, fourth))[3],
            'y': list(chunks(y, fourth))[3]
        },
    }
    return fractalScales
