import numpy as _np
from .mod_autil import to_plain

_NP_ALLOWED = dict.fromkeys([
    # Array creation
    'array', 'asarray',  # unsafe: 'zeros', 'ones', 'empty', 'full', 'arange', 'linspace'
    # Mathematical functions
    'sqrt', 'abs', 'sign', 'exp', 'log', 'log10', 'log2', 'power',
    # Trigonometric functions
    'sin', 'cos', 'tan', 'arcsin', 'arccos', 'arctan', 'arctan2',
    'degrees', 'radians',
    # Aggregation / statistics
    'sum', 'prod', 'mean', 'average', 'std', 'var', 'min', 'max',
    'amin', 'amax', 'median',
    # Array / matrix operations
    'dot', 'matmul', 'concatenate', 'stack', 'vstack', 'hstack',
    'reshape', 'transpose', 'ravel', 'flatten', 'where', 'clip',
    # Constants
    'pi', 'e',
], True)


def np_names():
    return {f'np.{n}' for n in _NP_ALLOWED}


class _RestrictedProxy:
    """Generic allowlist proxy (currently used by np). `_allowed` maps a
    permitted attribute name to either True (call/read, convert result to
    plain Python) or a nested allowed-dict (call, wrap result in a new proxy
    exposing only those names). Add entries to _NP_ALLOWED below to expose
    more, one name at a time.
    """

    __slots__ = ('_obj', '_allowed')
    _max_cells = 10_000  # guard against memory-exhaustion via huge frames/arrays

    def __init__(self, obj, allowed):
        self._obj = obj
        self._allowed = allowed

    def __getattr__(self, name):
        if name not in self._allowed:
            raise AttributeError(name)
        spec = self._allowed[name]
        value = getattr(self._obj, name)

        def finalize(result):
            size = getattr(result, 'size', None)
            if size is not None and size > self._max_cells:
                raise ValueError(f"Result too large ({size} cells > {self._max_cells}).")
            if spec is True:
                return to_plain(result)
            return _RestrictedProxy(result, spec)

        if not callable(value):
            return finalize(value)

        def wrapped(*args, **kwargs):
            return finalize(value(*args, **kwargs))

        return wrapped

    def _check_size(self, value):
        size = getattr(value, 'size', None)
        if size is not None and size > self._max_cells:
            raise ValueError(f"Result too large ({size} cells > {self._max_cells}).")
        return value

    def __getitem__(self, key):
        result = self._obj[key]
        return to_plain(self._check_size(result))

    def __repr__(self):
        return repr(self._obj)


np = _RestrictedProxy(_np, _NP_ALLOWED)
