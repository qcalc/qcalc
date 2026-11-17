# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

"""Narrow public API for restricted (sandboxed) user calculators.

Everything listed here is injected into user calculator code, so only add a name when it is safe for untrusted
authors: it must not reach the filesystem, network, threads, request/settings objects, the database, or hand out a
raw pandas object (see ``qutil.mod_code_security.dangerous_keywords``).

To expose a new helper:
  1. import it in the matching group below, and
  2. add its name to the ``_api()`` call right under that import.
``tests/test_qapi_exports.py`` fails if a listed name does not resolve or is listed twice.

For imports from calc see inside the package itself (calc imports qapi, so qapi must not import calc).
"""

import datetime

_API = {}  # group title -> exported names, in declaration order
_TYPES = 'field types'  # the group exposed as __qtypes__; every other group is exposed through __evacon__


def _api(group, names):
    _API[group] = tuple(names.split())


# | Calculator field types (annotations)
from qcore import (
    qchar, qcode, qdate, qdict, qdatetime, qemail, qchat, qfl, qfile, qfunc, qhide,
    qhidex, qhtml, qin, qimage, qlist, qpage, qread, qregex, qsel2, qtbl, qtc,
    qtc2, qtext, qtexta, qtexte, qtime, qt, qt2, qtx, quom, quom2, quomx,
    qurl, qvstr, qerror, qwarn, qinfo,
)

# qtable (real pd.DataFrame) is deliberately excluded: safe_execute()'s AST check doesn't block attribute calls
# like .eval()/.query()/.to_pickle() on it - use qtbl instead
_api(_TYPES, """
    qchar qcode qdate qdict qdatetime qemail qchat qfl qfile qfunc qhide qhidex qhtml qin qimage qlist qpage
    qread qregex qsel2 qtbl qtc qtc2 qtext qtexta qtexte qtime qt qt2 qtx quom quom2 quomx qurl qvstr
    qerror qwarn qinfo
""")

# | Quantities, units and currencies
from qcore import (
    Qty, UnitRegistry, QtyRegistry, qconvert, base_dims, prefixes, lmt_desc, QFormatter, QCurrency,
    isMeasureUnit as is_unit, isMeasureQuantity as is_qty,
)

_api('units', """
    Qty UnitRegistry QtyRegistry qconvert base_dims prefixes lmt_desc QFormatter QCurrency is_unit is_qty
""")

# | Tables and containers
from qcore import QTable, QRelation, QBase, QList, qdf, qdf_demo_data, table_columns_validator, csv2qtbl, np2qtbl, \
    validated_col, qnp as np
from qutil import DotDict, dd_list

_api('tables', """
    QTable QRelation QBase QList qdf qdf_demo_data table_columns_validator csv2qtbl np2qtbl validated_col np
    DotDict dd_list
""")

# | Date and time
from qcore import QDateTime, QTimezone, today, now, spellnow, time2float

_api('datetime', 'datetime QDateTime QTimezone today now spellnow time2float')

# | Value parsing and conversion
from qcore import (
    css2floats, css2ints, css2values, css2set, css2dict, css2list, vals2css,
    is_blank, normalize_name, to_float, as_float, to_bool, to_cast, pct2fraction, val2fraction, nzv,
)
from qutil import css2strs, iif, joinx, nzs

_api('parsing', """
    css2floats css2ints css2values css2strs css2set css2dict css2list vals2css
    is_blank normalize_name to_float as_float to_bool to_cast pct2fraction val2fraction nzv nzs iif joinx minimum
""")

# | Expressions and variables
from qutil import (
    specified_args, preprocess_expression, to_python_expr, xpr_coeffs, find_matched_variables,
    variable_to_title, title_to_variable, replace_variables, replace_parameter_values, parameter_values,
)

_api('expressions', """
    specified_args preprocess_expression to_python_expr xpr_coeffs find_matched_variables
    variable_to_title title_to_variable replace_variables replace_parameter_values parameter_values
""")

# | Text, markdown and JSON output
from qcore import br, pretty_json, qpretty_json, QScreen
from qutil import md2html, code2html, escape_markdown, truncate, word_count, text2words

_api('text', 'br md2html code2html escape_markdown truncate word_count text2words pretty_json qpretty_json QScreen')

# | Files and images
from qcore import QFile, qf2bio, QImage, qf2img, nparray_to_bio

_api('files', 'QFile qf2bio QImage qf2img nparray_to_bio')

# | Charts, maps and solvers
from qcore import QChart, QGeo, QMap, SmartCalc, legend_locations, color_schemes

_api('charts', 'QChart QGeo QMap SmartCalc legend_locations color_schemes')

# | Links, buttons and form behaviour
from qcore import ai_prompt_field
from qutil import (
    page_link, calurl, cal_link, callback_button, action_button, action_spec, addcal_button,
    step2_spec, step2_button, when_show, show_when, demo_url,
)

_api('links', """
    page_link calurl cal_link callback_button action_button action_spec addcal_button
    step2_spec step2_button when_show show_when demo_url ai_prompt_field
""")

# | User and environment
from qutil import user_name, user_ip, is_debug

_api('environment', 'user_name user_ip is_debug')

# | Calculator registration
from qcore import qcalc

_api('calculator', 'qcalc')

# | API discovery
from qcore import qsymbols, qsymstat, qsymhelp

_api('discovery', 'qtypes qmodules qsymbols qsymstat qsymhelp')


def minimum(*args, key=None):
    """Return the smallest item from an iterable or argument list.

    This is a safe qapi-exported alias of Python's built-in ``min`` for use in
    calculator expressions.
    """
    # defined locally (not imported from calc.conflicts) to avoid a
    # qapi <-> calc circular import at package-load time
    return min(*args, key=key)


def qtypes():
    """Return sorted qcalc annotation/helper type names available to calculators."""
    return sorted(__qtypes__)


def qmodules():
    """Return sorted module names allowed for calculator creation."""
    from qutil.mod_code_security import allowed_modules
    return sorted(allowed_modules)


qlib_dict = {
    'q': Qty, 'ureg': UnitRegistry, 'qreg': QtyRegistry, 'qdt': QDateTime, 'dd': DotDict,
    # | 'datetime': datetime.datetime, 'date': datetime.date, 'time': datetime.time,
    # | 'timedelta': datetime.timedelta, 'timezone': datetime.timezone,
    # | 'call': QCals.addr, (circular)
}

__qtypes__ = list(_API[_TYPES])

# for eva(), mycal() and console
__evacon__ = [name for group, names in _API.items() if group != _TYPES for name in names]

# for cal()
__all__ = __qtypes__ + __evacon__


def _qapis():
    return set(qlib_dict) | set(__evacon__)
