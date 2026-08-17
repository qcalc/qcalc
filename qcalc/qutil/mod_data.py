# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import json
from datetime import date, datetime, time as dt_time
from .mod_datetime import QDateTime


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
        return total_seconds/3600  # Return in hours
    elif time2val == 'min':
        return total_seconds/60  # Return in minutes
    elif time2val == 's':
        return total_seconds  # Return in seconds
    elif time2val == 'ms':
        return total_seconds * 1000  # Convert to milliseconds
    elif time2val == 'mics':
        return total_seconds * 1_000_000  # Convert to microseconds
    else:
        raise ValueError("Invalid time2val argument. Use 's', 'ms', or 'mics'.")


def _test():
    t = dt_time(1, 30, 15, 500000)  # 1 hour, 30 minutes, 15 seconds, and 500 milliseconds
    print(time2float(t, 's'))    # Output: 5415.5 seconds
    print(time2float(t, 'ms'))   # Output: 5415500 milliseconds
    print(time2float(t, 'mics'))  # Output: 5415500000 microseconds


if __name__ == '__main__':
    _test()
