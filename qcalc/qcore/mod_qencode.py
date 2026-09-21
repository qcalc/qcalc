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


_UNSERIALIZED = object()

_SERIALIZE_POLICIES = {
    'json': {
        'recursive': False,
        'q_object_mode': 'string',
        'unknown_mode': 'sentinel',
        'cycle_mode': 'sentinel',
        'allow_type_name': True,
        'allow_user': True,
    },
    'variant': {
        'recursive': True,
        'q_object_mode': 'none',
        'unknown_mode': 'raise',
        'cycle_mode': 'raise',
        'allow_type_name': False,
        'allow_user': False,
    },
}


class QEncoderBase(DjangoJSONEncoder):

    def default(self, obj):
        encoded = serialize_value(obj, profile='json')
        if encoded is not _UNSERIALIZED:
            return encoded

        try:
            return super().default(obj)
        except Exception as e:
            return str(e)  # | don't return e (exception)


def serialize_value(value, profile='json', _seen=None):
    if profile == 'step2':
        return step2_pack_value(value, _seen)

    policy = _SERIALIZE_POLICIES.get(profile)
    if policy is not None:
        return _serialize_common_profile(value, policy, _seen)

    raise ValueError(f'Unsupported profile: {profile}')


def deserialize_value(value, profile='variant'):
    if profile == 'step2':
        return step2_unpack_for_run(value)

    policy = _SERIALIZE_POLICIES.get(profile)
    if policy is not None:
        return _deserialize_common_profile(value, policy)

    raise ValueError(f'Unsupported profile: {profile}')


def _serialize_common_profile(value, policy, _seen=None):
    if _seen is None:
        _seen = set()

    if policy.get('recursive') and isinstance(value, dict):
        value_id = id(value)
        if value_id in _seen:
            cycle_mode = policy.get('cycle_mode', 'raise')
            if cycle_mode == 'none':
                return None
            if cycle_mode == 'sentinel':
                return _UNSERIALIZED
            raise ValueError('Cyclic reference detected while serializing dict')

        _seen.add(value_id)
        try:
            return {key: _serialize_common_profile(val, policy, _seen) for key, val in value.items()}
        finally:
            _seen.discard(value_id)

    if policy.get('recursive') and isinstance(value, list):
        value_id = id(value)
        if value_id in _seen:
            cycle_mode = policy.get('cycle_mode', 'raise')
            if cycle_mode == 'none':
                return None
            if cycle_mode == 'sentinel':
                return _UNSERIALIZED
            raise ValueError('Cyclic reference detected while serializing list')

        _seen.add(value_id)
        try:
            return [_serialize_common_profile(item, policy, _seen) for item in value]
        finally:
            _seen.discard(value_id)

    if isinstance(value, pd.DataFrame):
        return {
            '__qcalc_type': 'table',
            'columns': [str(col) for col in value.columns],
            'data': value.values.tolist(),
        }

    if isinstance(value, (datetime.date, datetime.time, datetime.datetime)):
        return str(QDateTime(value))

    if isinstance(value, QDateTime):
        return str(value)

    if isinstance(value, Qty):
        return str(value)

    if isinstance(value, decimal.Decimal):
        return float(value)

    if isinstance(value, datetime.timedelta):
        return value.total_seconds()

    if isinstance(value, (QFile, QImage, QChart)):
        q_object_mode = policy.get('q_object_mode', 'string')
        if q_object_mode == 'string':
            return str(value)
        if q_object_mode == 'none':
            return None

    if policy.get('allow_type_name') and isinstance(value, type):
        return value.__name__

    if policy.get('allow_user'):
        from qsite.users.models import User  # Lazy import
        if isinstance(value, User):
            return str(value)

    if isinstance(value, (str, int, float, bool)):
        return value

    if value is None:
        return None

    unknown_mode = policy.get('unknown_mode', 'raise')
    if unknown_mode == 'sentinel':
        return _UNSERIALIZED

    raise ValueError(f"Unsupported type: {type(value)}")


def _looks_like_legacy_dataframe_records(value):
    if not (isinstance(value, list) and value and all(isinstance(item, dict) for item in value)):
        return False

    keyset = set(value[0].keys())
    if not keyset:
        return False

    for row in value[1:]:
        if set(row.keys()) != keyset:
            return False

    for row in value:
        for cell in row.values():
            if isinstance(cell, (dict, list, tuple, set, pd.DataFrame)):
                return False

    return True


def _deserialize_common_profile(value, policy):
    if policy.get('recursive') and isinstance(value, dict):
        if value.get('__qcalc_type') == 'table':
            return pd.DataFrame(
                data=value.get('data', []),
                columns=value.get('columns', []),
            )
        return {key: _deserialize_common_profile(val, policy) for key, val in value.items()}

    if policy.get('recursive') and isinstance(value, list):
        out = [_deserialize_common_profile(item, policy) for item in value]
        if _looks_like_legacy_dataframe_records(out):
            try:
                return pd.DataFrame(out)
            except ValueError:
                return out
        return out

    if isinstance(value, str):
        dt = qc_str_to_datetime(value)
        return dt if dt else value

    return value


def step2_pack_value(value, _seen=None):
    if _seen is None:
        _seen = set()

    value_id = id(value)
    if value_id in _seen:
        return None

    if isinstance(value, Qty):
        return {'__qcalc_type': 'qty', 'value': str(value)}

    if isinstance(value, QChart):
        _seen.add(value_id)
        chart_data = value.data or {}
        if isinstance(chart_data, dict):
            chart_data = {
                key: val for key, val in chart_data.items()
                if key not in {'chart', 'fig', 'ax'}
            }
        return {
            '__qcalc_type': 'chart',
            'chtype': value.chtype,
            'data': step2_pack_value(chart_data, _seen),
        }

    if isinstance(value, pd.DataFrame):
        return {
            '__qcalc_type': 'table',
            'columns': [str(col) for col in value.columns],
            'data': value.values.tolist(),
        }

    if isinstance(value, dict) and {'columns', 'data'} <= value.keys():
        return {
            '__qcalc_type': 'table',
            'columns': value['columns'],
            'data': value['data'],
        }

    if isinstance(value, (datetime.date, datetime.datetime, datetime.time)):
        return str(QDateTime(value))

    if isinstance(value, dict):
        _seen.add(value_id)
        return {str(key): step2_pack_value(val, _seen) for key, val in value.items()}

    if isinstance(value, (list, tuple, set)):
        _seen.add(value_id)
        return [step2_pack_value(item, _seen) for item in value]

    if isinstance(value, (str, int, float, bool)) or value is None:
        return value

    return str(value)


def step2_unpack_for_run(value):
    if isinstance(value, dict):
        qtype = value.get('__qcalc_type')
        if qtype == 'qty':
            return value.get('value', '')
        if qtype == 'chart':
            return step2_unpack_for_run(value.get('data', {}))
        if qtype == 'table':
            return {
                'columns': value.get('columns', []),
                'data': value.get('data', []),
            }
        return {key: step2_unpack_for_run(val) for key, val in value.items()}

    if isinstance(value, list):
        return [step2_unpack_for_run(item) for item in value]

    return value


def step2_unpack_for_cost(value):
    if isinstance(value, Qty):
        return value

    if isinstance(value, dict) and value.get('__qcalc_type') == 'qty':
        try:
            return Qty(value.get('value', ''))
        except Exception:
            return None

    return value


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
    """Prepare a value for variant JSON storage using the shared serializer."""
    return serialize_value(value, profile='variant')


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
    return deserialize_value(value, profile='variant')
