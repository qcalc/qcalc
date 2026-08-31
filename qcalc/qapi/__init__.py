# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

"""Narrow public API for restricted user calculators."""

import datetime
# imports from qcore, qutil, qapi and standard python
# for imports from calc see inside the package itself

from qcore import (
    Qty, base_units, base_dims, unit_desc, prefixes, \
    uname2lmt as unit2lmt, lmt_title as lmt_desc, str_type, \
    lmt2categ as lmt2cat, lmt2ulist, lmt2qlist, find_unit, is_str_qty, qx, qxi, \
    isMeasureUnit as is_unit, isMeasureQuantity as is_qty, read_unit, \
    # | Keep the following annotations
    oqfunc, qchar, qcode, qdate, qdict, qdatetime, qemail, qfl, qfile, qfunc, qhide,
    qhidex, qhtml, qin, qimage, qlist, qpage, qread, qregex, qsel2, qtbl, qtc,
    qtc2, qtext, qtexta, qtexte, qtime, qt, qt2, qtx, quom, quom2, quomx,
    qurl, qvstr
)
from qutil import QDateTime, iif, DotDict, list_symbols
from .mod_np import np_names, np
from .mod_qtbl import *


def minimum(*args, key=None):
    # defined locally (not imported from calc.conflicts) to avoid a
    # qapi <-> calc circular import at package-load time
    return min(*args, key=key)


qlib_dict = {
    'QDateTime': QDateTime, 'qdt': QDateTime, 'DotDict': DotDict, 'dd': DotDict,
    'datetime': datetime.datetime, 'date': datetime.date, 'time': datetime.time,
    'Qty': Qty, 'q': Qty, 'qx': qx, 'qxi': qxi,
    # 'QGeo': QGeo, 'geo': QGeo,
    # 'QCals': QCals, 'UCals': UCals, 'QFav': QFav,
    # 'call': QCals.addr, (circular)
}

__qtypes__ = [
    "oqfunc", "qchar", "qcode", "qdate", "qdict", "qdatetime", "qemail",
    "qfl", "qfile", "qfunc", "qhide", "qhidex", "qhtml", "qin", "qimage", "qlist", "qpage",
    "qread", "qregex", "qsel2", "qtbl", "qtc", "qtc2", "qtext", "qtexta",
    # | qtable (real pd.DataFrame) deliberately excluded: safe_execute()'s AST check
    # | doesn't block attribute calls like .eval()/.query()/.to_pickle() on it - use qtbl instead
    "qtexte", "qtime", "qt", "qt2", "qtx", "quom", "quom2", "quomx", "qurl", "qvstr",
]

# for eva(), mycal() and console
__evacon__ = [
    "is_qty", "is_unit", "base_units", "base_dims", "unit_desc", "prefixes", "unit2lmt",
    "lmt_desc", "str_type", "read_unit", "lmt2cat", "lmt2ulist", "lmt2qlist", "find_unit",
    "iif", 'minimum', 'list_symbols',
    "np", "qdf", "qcol", "qrow", "qsum", "qadd", "qsub", "qmul", "qdiv",
    "qlib", "qtypes",
]


def qlib():
    names = set(qlib_dict) | set(__evacon__)
    names |= qdf_names()
    names |= np_names()
    return sorted(names)


def qtypes():
    return sorted(__qtypes__)


# for cal()
__all__ = __qtypes__ + __evacon__
