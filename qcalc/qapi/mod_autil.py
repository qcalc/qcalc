import numpy as _np
import pandas as _pd

def to_plain(value):
    """Convert pandas/numpy result types to plain Python so nothing with extra
    methods (eval/query/to_pickle/ctypes/...) ever escapes to sandboxed code."""
    if isinstance(value, (_pd.Series, _pd.DataFrame)):
        return value.to_dict()
    if isinstance(value, _pd.Index):
        return value.tolist()
    if isinstance(value, _np.ndarray):
        return value.tolist()
    if isinstance(value, _np.generic):
        return value.item()
    return value
