# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

"""Narrow public API for restricted user calculators."""
from .qcalc_security import validate_expression_security, safe_execute
from qcore import Qty, base_units, base_dims, unit_desc, prefixes, \
    uname2lmt as unit2lmt, lmt_title as lmt_desc, str_type, \
    lmt2categ as lmt2cat, lmt2ulist, lmt2qlist, find_unit
from qcore import isMeasureUnit as is_unit, isMeasureQuantity as is_qty, read_unit
from qcore import (
    oqfunc, qchar, qcode, qdate, qdict, qdatetime, qemail, qfl, qfile, qfunc, qhide,
    qhidex, qhtml, qin, qimage, qlist, qpage, qread, qregex, qsel2, qtbl, qtc,
    qtc2, qtext, qtexta, qtexte, qtime, qt, qt2, qtx, quom, quom2, quomx,
    qurl, qvstr, is_str_qty
)
from .mod_np import np_names, np
from .mod_qtbl import *
from qutil import QDateTime, iif
from qcore import qx, qxi
import datetime


def minimum(*args, key=None):
    # defined locally (not imported from calc.conflicts) to avoid a
    # qapi <-> calc circular import at package-load time
    return min(*args, key=key)


pylib_dict = {
    'QDateTime': QDateTime, 'qdt': QDateTime,
    'datetime': datetime.datetime, 'date': datetime.date, 'time': datetime.time,
    'Qty': Qty, 'q': Qty, 'qx': qx, 'qxi': qxi,
    # 'QGeo': QGeo, 'geo': QGeo,
    # 'QCals': QCals, 'call': QCals.addr, 'UCals': UCals, 'QFav': QFav,
    'minimum': minimum,
}  # specials and conflicts

__qtypes__ = [
    "oqfunc", "qchar", "qcode", "qdate", "qdict", "qdatetime", "qemail",
    "qfl", "qfile", "qfunc", "qhide", "qhidex", "qhtml", "qin", "qimage", "qlist", "qpage",
    "qread", "qregex", "qsel2", "qtbl", "qtc", "qtc2", "qtext", "qtexta",
    # | qtable (real pd.DataFrame) deliberately excluded: safe_execute()'s AST check
    # | doesn't block attribute calls like .eval()/.query()/.to_pickle() on it - use qtbl instead
    "qtexte", "qtime", "qt", "qt2", "qtx", "quom", "quom2", "quomx", "qurl", "qvstr",
]

# for eva() and console.
__evacon__ = [
    "is_qty", "is_unit", "base_units", "base_dims", "unit_desc", "prefixes", "unit2lmt",
    "lmt_desc", "str_type", "read_unit", "lmt2cat", "lmt2ulist", "lmt2qlist", "find_unit",
    "iif",
    "np", "qdf", "qcol", "qrow", "qsum", "qadd", "qsub", "qmul", "qdiv",
    "qlib", "qtypes",  # qlib(), qtypes() are defined below
]


def qlib():
    names = set(pylib_dict) | set(__evacon__)
    names |= qdf_names()
    names |= np_names()
    return sorted(names)


def qtypes():
    return sorted(__qtypes__)


# for cal()
__all__ = __qtypes__ + __evacon__
