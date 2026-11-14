# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import logging
import warnings

import qapi
from asteval import make_symbol_table
from qcore import Qty, UnitRegistry, QtyRegistry
from qutil import to_python_expr, safe_execute

logger = logging.getLogger(__name__)


class CalcSandbox:
    """Evaluates qcalc expressions and calculator code against the qcalc symbol table."""

    symbols: dict = {}  # qfunction names/addresses plus uoms/Qty plus py/asteval syms

    @classmethod
    def build_symbols(cls, qfunc_dict, excluded=()):
        # | symbols = (qfunc_dict - excluded cals) + UnitRegistry.table + QtyRegistry.info + __evacon__ + make_symbol_table
        # | qfunc_dict = (all calculators + auxiliaries) + (qlib_dict + calc_dict)
        assert len(set(qfunc_dict).intersection(UnitRegistry.table)) == 0
        qsyms = {key: val for key, val in qfunc_dict.items() if key not in excluded}
        qsyms.update({k: Qty(1, v) for k, v in UnitRegistry.table.items()})
        qsyms.update({k: v['qty'] for k, v in QtyRegistry.info.items()})
        qsyms.update({name: getattr(qapi, name) for name in qapi.__evacon__})

        psyms = make_symbol_table(use_numpy=False)
        assert (len(set(qsyms).intersection(psyms)) <= 1)  # 'min'
        # | py symbols first, then qcalc symbols overriding 1 conflict
        cls.symbols = {**psyms, **qsyms}

    @classmethod
    def eval(cls, qxpr, gdict=None, ldict=None):
        xpr = to_python_expr(qxpr)
        if ldict is None:
            ldict = {}
        # | merge dictionaries doesn't involve copying overhead.
        return eval(xpr, {**cls.symbols} if gdict is None else {**gdict}, ldict)  # direct eval() on purpose

    @classmethod
    def exec(cls, code, gdict=None, ldict=None):
        code = to_python_expr(code)
        if ldict is None:
            ldict = {}
        return safe_execute(code, cls.symbols.copy() if gdict is None else gdict, ldict)

    @classmethod
    def exec_with_context(cls, code, scope, username='', item_id=''):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", SyntaxWarning)
            local_dict = cls.exec(code)

        for warning_item in caught:
            if issubclass(warning_item.category, SyntaxWarning):
                logger.warning(
                    "SyntaxWarning in calculator code | scope=%s user=%s item_id=%s line=%s msg=%s",
                    scope,
                    username or '',
                    item_id or '',
                    getattr(warning_item, 'lineno', '?'),
                    str(warning_item.message),
                )
        return local_dict
