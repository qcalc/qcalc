# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import pandas as pd
from qutil import QDateTime, qc_str_to_datetime
from .qc_qty import Qty
from .mod_qfile import QFile
from django.core.serializers.json import DjangoJSONEncoder
from .mod_qimage import QImage
from .mod_qchart import QChart
import json
from qcore import qhtml
import datetime
import decimal

# from qcore import qhtml, qpage
# from datetime import date, datetime, time as dt_time


class QEncoderBase(DjangoJSONEncoder):

    def default(self, obj):
        if isinstance(obj, (Qty, QDateTime, QFile, QImage, QChart)):
            return str(obj)
        if isinstance(obj, (datetime.date, datetime.datetime, datetime.time)):
            return str(QDateTime(obj))
        elif isinstance(obj, pd.DataFrame):
            # return obj.columns.to_list()
            return obj.to_dict(orient="records")
        elif isinstance(obj, type):
            return obj.__name__  # | str(obj) or obj.__name__ if you only want the class name
        # elif isinstance(obj, User):
        #     return str(obj)
        else:
            from qsite.users.models import User # Lazy import
            if isinstance(obj, User):
                return str(obj)

            try:
                return super().default(obj)
            except Exception as e:
                return str(e)  # | don't return e (exception)


class QEncoderShort(QEncoderBase):
    def encode(self, obj):
        # Preprocess the dictionary to truncate strings
        obj = truncate_strings(obj)
        return super().encode(obj)


def truncate_strings(d, max_length=256):
    if isinstance(d, dict):
        return {k: truncate_strings(v, max_length) for k, v in d.items()}
    elif isinstance(d, list):
        return [truncate_strings(i, max_length) for i in d]
    elif isinstance(d, qhtml):
        return 'html... (TRUNCATED)'
    elif isinstance(d, pd.DataFrame):
        return d.columns.to_list()
    elif isinstance(d, str):
        return (d[:max_length] + '... (TRUNCATED)') if len(d) > max_length else d
    return d


def qjson_dumps(dict_):
    return json.dumps(dict_, cls=QEncoderBase).replace('null', '""')


def qpretty_json(dict_):
    return json.dumps(dict_, cls=QEncoderShort, indent=4, sort_keys=False).replace('null', '""')


def prepare_for_json(value):
    """
    Prepares a value for storage in a JSON field.

    If the value is a Pandas DataFrame, it converts it to a list of dictionaries.
    If the value is a dictionary or a list, it recursively checks each value.

    Args:
        value: The value to be prepared.

    Returns:
        The prepared value in a JSON-compatible format.
    """
    if isinstance(value, pd.DataFrame):
        # Convert DataFrame to a list of dictionaries
        return value.to_dict(orient='records')
    elif isinstance(value, dict):
        # If it's a dictionary, recursively process each value
        return {key: prepare_for_json(val) for key, val in value.items()}
    elif isinstance(value, list):
        # If it's a list, recursively process each item
        return [prepare_for_json(item) for item in value]
    elif isinstance(value, (datetime.date, datetime.time, datetime.datetime)):
        # Convert datetime, date, or time to ISO format string
        return str(QDateTime(value))
    elif isinstance(value, decimal.Decimal):
        # Convert Decimal to a float
        return float(value)
    elif isinstance(value, datetime.timedelta):
        # Convert timedelta to total seconds for storage
        return value.total_seconds()
    elif isinstance(value, (str, int, float, bool)):
        # If it's a primitive type (str, int, float, bool), return as is
        return value
    elif isinstance(value, (QFile, QImage, QChart)):
        # ignore
        return None
    else:
        # Raise an exception for unsupported types
        raise ValueError(f"Unsupported type: {type(value)}")


def reverse_prepare_for_json(value):
    """
    Converts JSON-compatible data back into its original Python types.

    If a list of dictionaries is detected, it attempts to convert it back into a DataFrame.
    Otherwise, it recursively processes dictionaries and lists.

    Args:
        value: The JSON-compatible value to be converted back.

    Returns:
        The converted value in its original Python format.
    """
    # Check if it's a list of dictionaries, convert back to DataFrame
    if isinstance(value, list) and all(isinstance(item, dict) for item in value):
        # Assuming all dictionaries have the same keys, try converting to DataFrame
        try:
            return pd.DataFrame(value)
        except ValueError:
            # In case of conversion failure, return the original list
            return value
    elif isinstance(value, dict):
        # If it's a dictionary, recursively process each value
        return {key: reverse_prepare_for_json(val) for key, val in value.items()}
    elif isinstance(value, list):
        # If it's a list, recursively process each item
        return [reverse_prepare_for_json(item) for item in value]
    elif isinstance(value, str):
        dt = qc_str_to_datetime(value)
        return dt if dt else value
    else:
        # If it's a primitive type (str, int, float, bool), return as is
        return value
