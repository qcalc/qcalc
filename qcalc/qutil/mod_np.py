import numpy
import pandas as pd

def np2df(np_arr):
    # restricted to internal use
    if isinstance(np_arr, numpy.ndarray):
        cols = [f'C{j + 1}' for j in range(np_arr.shape[1])]
        return pd.DataFrame(np_arr, columns=cols)
    else:
        return np_arr


def np2qtbl(np_arr):
    """Convert a numpy array to qtbl format with generated ``C1..Cn`` columns."""
    if isinstance(np_arr, numpy.ndarray):
        cols = [f'C{j + 1}' for j in range(np_arr.shape[1])]
        return {'columns': cols, 'data': np_arr}
    else:
        return np_arr
