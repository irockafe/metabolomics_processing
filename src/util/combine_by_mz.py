import numpy as np


def ppm_matrix(series1, series2):
    '''
    GOAL - create a matrix of pairwise ppm differences
    INPUT - 2 pandas Series, with index
    OUTPUT - numpy array containing pairrwise ppm comparisons
        format: rows are series1, columns are series2
            you can convert back to dataframe if you want after the
            fxn (numpy's broadcasting is too dope not to use, and
            dataframes take up too much memory for the HMDB set)
    '''
    # do series1-series2 using numpy's broadcasting
    # This is faster than using a loop
    diff_matrix = abs(series1.values[:, np.newaxis] - series2.values)
    # Get max of pairwise comparisons
    max_matrix = np.maximum(series1.values[:, np.newaxis],
                            series2.values)
    return (diff_matrix / max_matrix)*10**6
