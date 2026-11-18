# source: https://stackoverflow.com/questions/56482639/design-pattern-for-relational-and-optional-parameters
from .qc_qty import Qty
from qutil import css2strs


class SmartCalc:
    """Calculate derived values only when a calculator asks for them.

    Supply known values as keyword arguments. Quantity strings are converted to
    ``Qty`` objects, and arguments whose value is ``None`` are ignored. Define
    ``inferred()`` in a subclass to provide calculations for derived names;
    each result is calculated on first access and then reused.

    For example, a subclass can return ``{'profit': calculate_profit}`` from
    ``inferred()``, where ``calculate_profit`` uses the supplied ``revenue``
    and ``cost`` values. Accessing ``calc.profit`` then returns the result.
    """
    def __init__(self, **kwargs):
        self.params = {}
        for k, v in kwargs.items():
            if v is not None:
                if isinstance(v, str):
                    value = v.strip()
                    otype, sunit, ln = Qty.kind(value)
                    if otype == 'qty':
                        qt = Qty(sunit)
                        if qt.val is not None:
                            self.params[k] = qt
                        else:
                            pass
                    else:
                        self.params[k] = v
                else:
                    self.params[k] = v
            else:
                pass

    def __getattr__(self, name):
        if name in self.params:
            return self.params[name]
        if name in self.inferred():
            calc = self.inferred()[name]
            if isinstance(calc, dict):
                for calfunc_params, calfunc in calc.items():
                    # if isinstance(names, str): names = [names]
                    names = css2strs(calfunc_params)
                    if all(name in self.params for name in names):
                        calc = calfunc
                        break
            value = calc()
            self.params[name] = value
            return value
