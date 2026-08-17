# source: https://stackoverflow.com/questions/56482639/design-pattern-for-relational-and-optional-parameters
from .qc_qty import Qty, str_type
from qutil import css2strs


class SmartCalc:

    def __init__(self, **kwargs):
        self.params = {}
        for k, v in kwargs.items():
            if v is not None:
                if isinstance(v, str):
                    value = v.strip()
                    otype, sunit, ln = str_type(value)
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
