# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from .qd_data import str2type, time2float, is_blank
from .qd_datetime import QDateTime
from datetime import date, datetime, time as dt_time
from qutil import css2strs


def nzv(nval):
    return 0 if nval is None else nval


def vals2css(vals: list, separator=', '):
    """Serialize iterable values into a separated string."""
    return separator.join(map(str, vals))


def css2values(cs_string, separator=',', time2val='hr'):  # '', ('hr','min','s', 'ms', or 'mics')
    """
    Parse separated values and return ``(values, data_type)``.

    Supported inferred types are float, int, date, datetime, time, and str.
    Time values return ``datetime.time`` objects when ``time2val == ''``,
    otherwise they are converted to float using ``time2float`` with
    ``time2val`` units ('hr', 'min', 's', 'ms', or 'mics').
    """
    if isinstance(cs_string, list): return cs_string, type(cs_string[0]) if len(cs_string) > 0 else float
    cs_string = cs_string.strip()
    if cs_string == '': return [], float
    list_values = []
    try:
        list_strings = [x.strip() for x in cs_string.split(separator)]
        data_type = str2type(list_strings[0])
        if data_type == float:
            list_values = [float(x) for x in list_strings]
        elif data_type == int:
            list_values = [int(x) for x in list_strings]
        elif data_type == date:
            list_values = []
            for x in list_strings:
                parsed = QDateTime(x).val
                if not (isinstance(parsed, date) and not isinstance(parsed, datetime)):
                    raise ValueError(f"Error (C2V): Invalid date value: {x}")
                list_values.append(parsed)
        elif data_type == datetime:
            list_values = []
            for x in list_strings:
                parsed = QDateTime(x).val
                if not isinstance(parsed, datetime):
                    raise ValueError(f"Error (C2V): Invalid datetime value: {x}")
                list_values.append(parsed)
        elif data_type == dt_time:
            parsed_times = []
            for x in list_strings:
                parsed = QDateTime(x).val
                if not isinstance(parsed, dt_time):
                    raise ValueError(f"Error (C2V): Invalid time value: {x}")
                parsed_times.append(parsed)
            if time2val == '':
                list_values = parsed_times
            else:
                list_values = [time2float(x, time2val) for x in parsed_times]
                data_type = float
        elif data_type == str:
            list_values = list_strings
    except ValueError as e:
        raise ValueError(f"Error (C2V): Input issue: {e}")
    # print('l', list_values, data_type)
    return list_values, data_type


def css2list(cs_string, separator=','):
    """Tolerant ``css2strs``: separated text, or a list/tuple, to a list of non-empty stripped strings.

    Unlike ``css2strs`` it returns ``[]`` for blank-like input (None, nan, 'none', ...), also splits on
    newlines, skips empty items (``'a, ,b'`` gives ``['a', 'b']``) and converts list items to ``str``.
    """
    if is_blank(cs_string): return []
    if isinstance(cs_string, str):
        items = css2strs(cs_string.replace('\n', separator), separator)
    else:
        items = cs_string
    return [text for text in (str(item).strip() for item in items) if text]


def css2dict(cs_string, separator=',', pair_separator='='):
    """Parse ``"key=value,key2=value2"`` text into a dict of stripped strings.

    Empty items and items with an empty key are skipped; an item without ``pair_separator`` maps to ``''``.
    A later duplicate key overrides an earlier one. Returns the input as-is when a dict is provided
    and ``{}`` for blank/None input.
    """
    if isinstance(cs_string, dict): return cs_string
    if cs_string is None: return {}
    result = {}
    for item in str(cs_string).split(separator):
        key, _, value = item.partition(pair_separator)
        key = key.strip()
        if key == '': continue
        result[key] = value.strip()
    return result


def css2set(cs_string, separator=','):
    """Convert separated text to a normalized lowercase string set.

    Empty-like tokens (``'', none, null, nan, na``) produce an empty set.
    """
    if cs_string is None:
        return set()
    text = str(cs_string).strip().lower()
    if text in {'', 'none', 'null', 'nan', 'na'}:
        return set()
    if isinstance(cs_string, set):
        return {str(item).strip().lower() for item in cs_string if str(item).strip()}
    return {item.strip().lower() for item in css2strs(cs_string, separator) if item.strip()}


def css2floats(cs_string, separator=','):
    """Parse separated numeric text into a list of floats.

    Returns ``[]`` for blank input and passes through a provided list.
    """
    if isinstance(cs_string, list): return cs_string
    cs_string = cs_string.strip()
    if cs_string == '': return []
    list_floats = [float(x.strip()) for x in cs_string.split(separator)]
    return list_floats


def css2ints(cs_string, separator=','):
    """Parse separated numeric text into a list of ints.

    Each token is converted via ``int(float(token))`` to accept values such as
    ``"2.0"``.
    """
    if isinstance(cs_string, list): return cs_string
    cs_string = cs_string.strip()
    if cs_string == '': return []
    list_ints = [int(float(x.strip())) for x in cs_string.split(separator)]
    return list_ints
