# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import pandas as pd
from .qd_datetime import QDateTime
from .qc_qty import Qty
from .mod_qfile import QFile
from django.core.serializers.json import DjangoJSONEncoder
from .mod_qimage import QImage
from .mod_qchart import QChart
import json
from .qf_anno import qchat, qhtml, qerror, qinfo, qwarn
import datetime
import decimal
import math
import numpy as np

_UNSERIALIZED = object()

_TAG = '__qcalc_type'
_LEGACY_FRAME_TAG = '__shared_kind'  # | shared-data frames saved before the 'frame' profile used this tag
_CHART_RUNTIME_KEYS = {'chart', 'fig', 'ax'}

API_COMPACT_MAX_ROWS = 20
# | most specific first; all of these are str subclasses
_API_MESSAGE_TYPES = ((qerror, 'error'), (qwarn, 'warning'), (qinfo, 'info'), (qhtml, 'html'), (qchat, 'html'))
_TEXT_KINDS = {kind for _, kind in _API_MESSAGE_TYPES} | {'file', 'image'}

# | json: lossy, one level, unknown objects are left to the JSON encoder; variant: recursive, strict, round-trips
_PLAIN_POLICIES = {
    'json': {
        'recursive': False,
        'q_object_mode': 'string',
        'unknown_mode': 'sentinel',
        'allow_type_name': True,
        'allow_user': True,
    },
    'variant': {
        'recursive': True,
        'q_object_mode': 'none',
        'unknown_mode': 'raise',
        'allow_type_name': False,
        'allow_user': False,
    },
}
# | tagged profiles keep tables, quantities and charts as ``__qcalc_type`` objects
_TAGGED_PROFILES = {'step2', 'api'}
# | 'frame' only turns DataFrames into tagged tables and back, everything else passes through untouched
_PROFILES = set(_PLAIN_POLICIES) | _TAGGED_PROFILES | {'frame'}


def _api_number(value):
    """Return a JSON-safe float: NaN/inf become None, binary noise is trimmed to 12 significant digits."""
    if math.isnan(value) or math.isinf(value):
        return None
    return float(f'{value:.12g}')


def _datetime_str(value):
    return str(value) if isinstance(value, QDateTime) else str(QDateTime(value))


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


class QSerializer:
    """Converts calculator values to and from JSON-safe structures for one named profile.

    Profiles: ``json`` (encoder fallback), ``variant`` (saved inputs), ``step2`` (cached step-2 I/O), ``api``
    (strict API output; ``compact`` truncates tables to ``max_rows`` and omits chart data for LLM tool output) and
    ``frame`` (DataFrames only, used by shared datasets and rates).

    ``serialize``/``deserialize`` are the entry points; ``pack``/``unpack`` are the recursive workers. Tables share
    one tagged shape, ``{'__qcalc_type': 'table', 'columns': [...], 'data': [[...]]}``, in every profile.
    """

    def __init__(self, profile='json', compact=False, max_rows=API_COMPACT_MAX_ROWS):
        if profile not in _PROFILES:
            raise ValueError(f'Unsupported profile: {profile}')
        self.profile = profile
        self.compact = compact
        self.max_rows = max_rows
        self._policy = _PLAIN_POLICIES.get(profile, {})
        self._tagged = profile in _TAGGED_PROFILES

    def serialize(self, value, _seen=None):
        return self.pack(value, set() if _seen is None else _seen)

    def deserialize(self, value):
        return self.unpack(value)

    def pack(self, value, seen):
        if self._policy:
            return self._pack_plain(value, seen)
        return getattr(self, f'_pack_{self.profile}')(value, seen)

    def unpack(self, value):
        if self._tagged:
            return self._unpack_tagged(value)
        if self.profile == 'frame':
            frame = self._as_frame(value)
            return value if frame is None else frame
        return self._unpack_plain(value)

    # | shared helpers

    def _pack_children(self, value, seen):
        # | seen holds only the containers being packed right now, so a value shared in two places is packed twice
        value_id = id(value)
        if value_id in seen:
            if self._policy:
                raise ValueError(f'Cyclic reference detected while serializing {type(value).__name__}')
            return None

        seen.add(value_id)
        try:
            if isinstance(value, dict):
                return {(str(key) if self._tagged else key): self.pack(val, seen) for key, val in value.items()}
            return [self.pack(item, seen) for item in value]
        finally:
            seen.discard(value_id)

    def _pack_table(self, columns, rows, seen):
        rows = list(rows)
        total = len(rows)
        truncated = self.compact and total > self.max_rows
        if truncated:
            rows = rows[:self.max_rows]
        table = {
            _TAG: 'table',
            'columns': [str(col) for col in columns],
            'data': [[self.pack(cell, seen) for cell in row] for row in rows] if self._tagged else rows,
        }
        if truncated:
            table['truncated'] = True
            table['total_rows'] = total
        return table

    @staticmethod
    def _table_parts(value):
        """(columns, rows) of a DataFrame or of a ``{'columns', 'data'}`` dict, otherwise None."""
        if isinstance(value, pd.DataFrame):
            return value.columns, value.values.tolist()
        if isinstance(value, dict) and {'columns', 'data'} <= value.keys():
            return value['columns'], value['data']
        return None

    def _pack_chart(self, chart, seen):
        if self.compact:
            return {_TAG: 'chart', 'chtype': chart.chtype, 'omitted': True}
        data = chart.data if isinstance(chart.data, dict) else {}
        data = {key: val for key, val in data.items() if key not in _CHART_RUNTIME_KEYS}
        return {_TAG: 'chart', 'chtype': chart.chtype, 'data': self.pack(data, seen)}

    @staticmethod
    def _as_frame(value):
        if isinstance(value, dict) and (value.get(_TAG) == 'table' or value.get(_LEGACY_FRAME_TAG) == 'dataframe'):
            return pd.DataFrame(data=value.get('data', []), columns=value.get('columns', []))
        return None

    # | json / variant

    def _pack_plain(self, value, seen):
        policy = self._policy
        if policy['recursive'] and isinstance(value, (dict, list)):
            return self._pack_children(value, seen)

        if isinstance(value, pd.DataFrame):
            return self._pack_table(*self._table_parts(value), seen)

        if isinstance(value, (datetime.date, datetime.time, datetime.datetime,         QDateTime)):
            return _datetime_str(value)

        if isinstance(value, Qty):
            return str(value)

        if isinstance(value, decimal.Decimal):
            return float(value)

        if isinstance(value, datetime.timedelta):
            return value.total_seconds()

        if isinstance(value, (QFile, QImage, QChart)):
            return str(value) if policy['q_object_mode'] == 'string' else None

        if policy['allow_type_name'] and isinstance(value, type):
            return value.__name__

        if policy['allow_user']:
            from qsite.users.models import User  # Lazy import
            if isinstance(value, User):
                return str(value)

        if isinstance(value, (str, int, float, bool)) or value is None:
            return value

        if policy['unknown_mode'] == 'sentinel':
            return _UNSERIALIZED

        raise ValueError(f"Unsupported type: {type(value)}")

    def _unpack_plain(self, value):
        if self._policy['recursive']:
            if isinstance(value, dict):
                frame = self._as_frame(value)
                if frame is not None:
                    return frame
                return {key: self._unpack_plain(val) for key, val in value.items()}

            if isinstance(value, list):
                out = [self._unpack_plain(item) for item in value]
                if _looks_like_legacy_dataframe_records(out):
                    try:
                        return pd.DataFrame(out)
                    except ValueError:
                        return out
                return out

        if isinstance(value, str):
            dt = QDateTime.qc_str_to_datetime(value)
            return dt if dt else value

        return value

    # | frame

    def _pack_frame(self, value, seen):
        if isinstance(value, pd.DataFrame):
            return self._pack_table(*self._table_parts(value), seen)
        return value

    # | step2

    def _pack_step2(self, value, seen):
        if isinstance(value, Qty):
            return {_TAG: 'qty', 'value': str(value)}

        if isinstance(value, QChart):
            return self._pack_chart(value, seen)

        parts = self._table_parts(value)
        if parts:
            return self._pack_table(*parts, seen)

        if isinstance(value, (datetime.date, datetime.datetime, datetime.time)):
            return _datetime_str(value)

        if isinstance(value, (dict, list, tuple, set)):
            return self._pack_children(value, seen)

        if isinstance(value, (str, int, float, bool)) or value is None:
            return value

        return str(value)

    # | api: unlike step2 every nested cell is packed, quantities keep number and unit apart, NaN/inf never escape

    def _pack_api(self, value, seen):
        if value is None or isinstance(value, bool):
            return value

        for message_type, kind in _API_MESSAGE_TYPES:
            if isinstance(value, message_type):
                return {_TAG: kind, 'text': str(value)}

        if isinstance(value, str):
            return str(value)

        if isinstance(value, int):
            return int(value)

        if isinstance(value, float):
            return _api_number(float(value))

        if isinstance(value, np.generic):
            return self.pack(value.item(), seen)

        if isinstance(value, Qty):
            number = value.val
            return {
                _TAG: 'qty',
                'value': _api_number(float(number)) if isinstance(number, (int, float)) else number,
                'unit': value.uom,
                'text': str(value),
            }

        if isinstance(value, decimal.Decimal):
            return _api_number(float(value))

        if isinstance(value, datetime.timedelta):
            return value.total_seconds()

        if isinstance(value, (datetime.date, datetime.time, datetime.datetime, QDateTime)):
            return _datetime_str(value)

        if isinstance(value, QChart):
            return self._pack_chart(value, seen)

        if isinstance(value, (QFile, QImage)):
            return {_TAG: 'image' if isinstance(value, QImage) else 'file', 'text': str(value)}

        parts = self._table_parts(value)
        if parts:
            return self._pack_table(*parts, seen)

        if isinstance(value, (dict, list, tuple, set)):
            return self._pack_children(value, seen)

        return str(value)

    # | step2 / api inputs: tagged quantities become 'value unit' strings and tables become {'columns', 'data'}
    # | dicts, the same shapes calculators already accept

    def _unpack_tagged(self, value):
        if isinstance(value, dict):
            kind = value.get(_TAG)
            if kind == 'qty':
                return value.get('text') or f"{value.get('value', '')} {value.get('unit', '')}".strip()
            if kind == 'table':
                return {
                    'columns': list(value.get('columns', [])),
                    'data': [[self._unpack_tagged(cell) for cell in row] for row in value.get('data', [])],
                }
            if kind in _TEXT_KINDS:
                return value.get('text', '')
            if kind == 'chart':
                return self._unpack_tagged(value.get('data', {}))
            return {key: self._unpack_tagged(val) for key, val in value.items()}

        if isinstance(value, list):
            return [self._unpack_tagged(item) for item in value]

        return value


def serialize_value(value, profile='json', _seen=None):
    return QSerializer(profile).serialize(value, _seen)


def deserialize_value(value, profile='variant'):
    return QSerializer(profile).deserialize(value)


def step2_pack_value(value, _seen=None):
    return QSerializer('step2').serialize(value, _seen)


def step2_unpack_for_run(value):
    return QSerializer('step2').deserialize(value)


def api_pack_value(value, compact=False, max_rows=API_COMPACT_MAX_ROWS, _seen=None):
    return QSerializer('api', compact, max_rows).serialize(value, _seen)


def api_unpack_value(value):
    return QSerializer('api').deserialize(value)


class QEncoderBase(DjangoJSONEncoder):

    def default(self, obj):
        encoded = serialize_value(obj, profile='json')
        if encoded is not _UNSERIALIZED:
            return encoded

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
    elif isinstance(d, (qchat, qhtml)):
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
