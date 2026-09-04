# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

"""Narrow public API for restricted user calculators."""

import datetime
# imports from qcore, qutil, qapi and standard python
# for imports from calc see inside the package itself

from qcore import (
    # | Qty class and related functions
    Qty, base_units, base_dims, unit_desc, prefixes, \
    uname2lmt as unit2lmt, lmt_title as lmt_desc, str_type, \
    lmt2categ as lmt2cat, lmt2ulist, lmt2qlist, find_unit, is_str_qty, qx, qxi, \
    isMeasureUnit as is_unit, isMeasureQuantity as is_qty, read_unit, \
    # | Keep the following annotations
    oqfunc, qchar, qcode, qdate, qdict, qdatetime, qemail, qfl, qfile, qfunc, qhide,
    qhidex, qhtml, qin, qimage, qlist, qpage, qread, qregex, qsel2, qtbl, qtc,
    qtc2, qtext, qtexta, qtexte, qtime, qt, qt2, qtx, quom, quom2, quomx,
    qurl, qvstr,
    # | Other classes and related functions
    QFile, qf2bio,
    QImage, qf2img, nparray_to_bio,
    QChart, QGeo, QMap, SmartCalc
)
from qutil import QDateTime, DotDict, user_name, user_process, \
    page_link, calurl, cal_link, command_button, addcal_button, \
    iif, joinx, css2floats, css2ints, css2values, css2strs, vals2css
from .mod_np import np_names, np
from .mod_qtbl import *
from .mod_autil import qsymbols, qsymstat, qsymhelp


def minimum(*args, key=None):
    # defined locally (not imported from calc.conflicts) to avoid a
    # qapi <-> calc circular import at package-load time
    return min(*args, key=key)


qlib_dict = {
    'QDateTime': QDateTime, 'qdt': QDateTime, 'DotDict': DotDict, 'dd': DotDict,
    'datetime': datetime.datetime, 'date': datetime.date, 'time': datetime.time,
    'Qty': Qty, 'q': Qty, 'qx': qx, 'qxi': qxi,
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
    "minimum", "iif", "joinx", "css2floats", "css2ints", "css2values", "css2strs", "vals2css",
    "np", "qdf", "qcol", "qrow", "qsum", "qadd", "qsub", "qmul", "qdiv",
    "qtypes", "qmodules", "qsymbols", "qsymstat", "qsymhelp",
    "QFile", "qf2bio",
    "QImage", "qf2img", "nparray_to_bio",
    "QChart", "QGeo", "QMap", "SmartCalc",
    "user_name", "user_process", "page_link", "calurl", "cal_link", "command_button", "addcal_button",
]


def _qapis():
    names = set(qlib_dict) | set(__evacon__)
    # names |= qdf_names()
    # names |= np_names()
    return names


def qtypes():
    return sorted(__qtypes__)


def qmodules():
    from qutil.mod_code_security import allowed_modules
    return sorted(allowed_modules)


# for cal()
__all__ = __qtypes__ + __evacon__
