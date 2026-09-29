# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import json
import re
from datetime import date, datetime, time as dt_time
from .mod_datetime import QDateTime


def to_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return value != 0
    text = str(value).strip().lower()
    if text in ('1', 'true', 'yes', 'y', 'on'):
        return True
    if text in ('0', 'false', 'no', 'n', 'off', ''):
        return False
    return bool(value)


def is_blank(value) -> bool:
    if value is None:
        return True
    text = str(value).strip().lower()
    return text in {'', 'none', 'null', 'nan', 'na'}


def to_float(value, field_name="value", required=True) -> None | float:
    if is_blank(value):
        if required:
            raise Exception(f"{field_name} cannot be blank")
        else:
            return None

    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip()
    text = text.replace(',', '')
    text = text.replace('%', '')
    match = re.search(r'[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?', text)
    if not match:
        raise Exception(f"Invalid numeric value for {field_name}: {value}")
    return float(match.group(0))


def to_cast(value, field_name, cast=float, required=False) -> None | float:
    """Parse optional scalar number, returning None for blank input.

    `cast` can be `float`, `int`, or any callable that accepts one value.
    """
    if is_blank(value):
        if required:
            raise Exception(f"{field_name} cannot be blank")
        else:
            return None
    try:
        return cast(value)
    except Exception as e:
        raise Exception(f"Invalid numeric value for {field_name}: {value}")


def as_float(value, field_name='value', required=False) -> None | float:
    def _as_float_or_none(value, field_name="value"):
        if isinstance(value, bool):
            return None
        if isinstance(value, (int, float)):
            return float(value)
        if value in ('', None):
            return None
        if isinstance(value, str):
            text = value.strip()
            if text == '':
                return None
            try:
                return float(text)
            except Exception:
                return None
        return None

    number = _as_float_or_none(value)
    if number is None:
        if required:
            raise Exception(f"{field_name} must be numeric")
        else:
            return None
    return number


def to_fraction(value, field_name, required=True):
    raw = to_float(value, field_name, required=required)
    if raw is None:
        return None
    return raw / 100.0


def normalize_name(name):
    text = str(name).strip().lower()
    text = text.replace('%', '')
    text = text.replace('_', ' ')
    return ' '.join(text.split())


def pretty_json(json_data):
    return json.dumps(json_data, indent=4, sort_keys=False)


def val2type(arg_value):
    if isinstance(arg_value, float):
        return float
    elif type(arg_value) is int:
        # | isinstance(True, int) = True!
        return int
    elif isinstance(arg_value, date) and not isinstance(arg_value, datetime):
        return date
    elif isinstance(arg_value, dt_time):
        return dt_time
    elif isinstance(arg_value, datetime):
        return datetime
    elif isinstance(arg_value, QDateTime):
        if arg_value.is_date:
            return date
        elif arg_value.is_datetime:
            return datetime
        elif arg_value.is_time:
            return dt_time
    elif isinstance(arg_value, str):
        return str
    return float


def str2type(value):
    def num_type(value: str):
        try:
            _ = int(value)
            return int
        except ValueError:
            pass

        try:
            _ = float(value)
            return float
        except ValueError:
            pass

        return str

    value = value.strip()
    # | if string length is >96 it will quickly return as a non-qty string
    if not (5 <= len(value) <= 32):
        return num_type(value)
    else:
        # | a potential iso datetime string can be between 5-32 characters
        qdate = QDateTime(value)
        if qdate.dt_value is None:
            return num_type(value)
        elif qdate.is_date:
            return date
        elif qdate.is_time:
            return dt_time
        elif qdate.is_datetime:
            return datetime

    return num_type(value)


def time2float(tm: dt_time, time2val: str) -> float:
    """Convert a datetime-time value to a float based on specified units.

    Args:
        tm (time): The datetime-time object to convert.
        time2val (str): The unit for conversion ('hr','min','s', 'ms', or 'mics').

    Returns:
        float: The converted time value.
    """
    # Get total seconds, milliseconds, or microseconds from the time object
    total_seconds = tm.hour * 3600 + tm.minute * 60 + tm.second + tm.microsecond / 1_000_000

    if time2val == 'hr':
        return total_seconds / 3600  # Return in hours
    elif time2val == 'min':
        return total_seconds / 60  # Return in minutes
    elif time2val == 's':
        return total_seconds  # Return in seconds
    elif time2val == 'ms':
        return total_seconds * 1000  # Convert to milliseconds
    elif time2val == 'mics':
        return total_seconds * 1_000_000  # Convert to microseconds
    else:
        raise ValueError("Invalid time2val argument. Use 's', 'ms', or 'mics'.")
