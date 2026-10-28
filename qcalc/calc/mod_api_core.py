# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

"""Transport-neutral core of the calculator API.

HTTP views (views_api.py) and any future adapter (e.g. MCP) call these functions and never touch forms or
sessions. Only standard calculators whose ``__info()`` sets ``'api': True`` are exposed.
"""

import inspect
import logging
import time

from qcore import (
    api_pack_value, api_unpack_value, QJField, qerror, qtable, qtbl, qlist, qdict, as_qtable, is_qtbl,
)
from qutil import to_bool
from qvars import qc_gpref as gs
from .mod_mfunc import func_meta, q0164_execute_qfunc
from .mod_qcals import QCals
from .mod_api_quota import consume_api_quota, ApiQuotaExceeded

logger = logging.getLogger(__name__)

API_VERSION = 1
MODES = ('full', 'compact')
_MAX_LIMIT = 200

_api_flag_cache: dict[str, bool] = {}


class ApiError(Exception):
    def __init__(self, code: str, message: str, status: int = 400, field: str | None = None,
                 headers: dict | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status
        self.field = field
        self.headers = headers or {}

    def to_dict(self):
        err = {'code': self.code, 'message': self.message}
        if self.field:
            err['field'] = self.field
        return err


def api_enabled(func_id: str) -> bool:
    """True for a standard calculator that opted in through ``'api': True`` in its ``__info()``."""
    if func_id not in QCals.qc_dict:
        return False
    flag = _api_flag_cache.get(func_id)
    if flag is None:
        try:
            # flag = bool(QCals.run_func_info(func_id, None, 'q').get('api'))
            flag = bool(QCals.run_func_info(func_id, 'q').get('api'))
        except Exception:
            flag = False
        _api_flag_cache[func_id] = flag
    return flag


def _resolve(func_id):
    if not isinstance(func_id, str) or not api_enabled(func_id):
        raise ApiError('not_found', f"Calculator '{func_id}' not found", 404)
    addr = QCals.addr(func_id, 'q')
    if addr is None:
        raise ApiError('not_found', f"Calculator '{func_id}' not found", 404)
    return addr


def _summary(func_id):
    title, desc, tags = QCals.func_title_desc_tags(func_id, 'q')
    return {'id': func_id, 'title': title, 'desc': desc, 'tags': tags}


def list_calculators(query: str = '', limit: int = 50, offset: int = 0) -> dict:
    """Opted-in calculators whose id, title, description or tags contain every word of ``query``."""
    limit = max(1, min(int(limit), _MAX_LIMIT))
    offset = max(0, int(offset))
    words = (query or '').lower().split()

    found = []
    for func_id in QCals.qc_list:
        if not api_enabled(func_id):
            continue
        item = _summary(func_id)
        haystack = ' '.join((item['id'], item['title'], item['desc'], item['tags'])).lower()
        if all(word in haystack for word in words):
            found.append(item)

    return {'version': API_VERSION, 'total': len(found), 'offset': offset, 'calculators': found[offset:offset + limit]}


def _field_schema(name, default, annotation, parameter, info_schema):
    ann_name = None if annotation is None else getattr(annotation, '__name__', str(annotation))
    try:
        qjf = QJField(name, annotation, default)
        field_type, kind = qjf.jf.get('type', ''), qjf.s2f.get('type', '')
    except Exception:
        field_type, kind = '', ''

    field = {
        'name': name,
        'type': field_type or ann_name or 'any',
        'annotation': ann_name,
        'quantity': kind in ('qty', 'c'),
        'required': parameter is not None and parameter.default is inspect.Parameter.empty,
        'default': api_pack_value(default),
    }
    spec = info_schema.get(name)
    if isinstance(spec, dict):
        for key in ('label', 'help_text'):
            if spec.get(key):
                field[key] = spec[key]
        choices = spec.get('choices')
        if choices and not callable(choices):
            field['choices'] = api_pack_value(choices)
    return field


def get_schema(func_id: str) -> dict:
    addr = _resolve(func_id)
    fargs, fanns, finfs = func_meta(addr, func_id)
    info_schema = finfs.get('schema', {}) or {}
    parameters = inspect.signature(addr).parameters
    info = _summary(func_id)
    info['doc'] = inspect.getdoc(addr) or ''
    info['arguments'] = [
        _field_schema(name, default, fanns.get(name), parameters.get(name), info_schema)
        for name, default in fargs.items()
    ]
    return {'version': API_VERSION, **info}


def _coerce(name, value, parameter):
    annotation = None if parameter.annotation is inspect.Parameter.empty else parameter.annotation
    default = parameter.default

    try:
        if annotation is qtable:
            return as_qtable(value)
        if annotation is qtbl:
            if not is_qtbl(value):
                raise TypeError("Expected {'columns': [...], 'data': [[...]]}")
            return value
        if annotation is qlist and not isinstance(value, list):
            raise TypeError('Expected a list')
        if annotation is qdict and not isinstance(value, dict):
            raise TypeError('Expected an object')
        if value is None or default is inspect.Parameter.empty or default is None:
            return value
        # | a plain string default (e.g. '132 lb') accepts numbers and strings as they are
        if isinstance(default, bool):
            return to_bool(value) if isinstance(value, str) else bool(value)
        if isinstance(default, int):
            if isinstance(value, bool):
                raise TypeError('Expected an integer')
            if isinstance(value, float) and not value.is_integer():
                raise TypeError('Expected an integer')
            return int(float(value)) if isinstance(value, (int, float, str)) else value
        if isinstance(default, float):
            # | a float default may still receive 'value unit' text, which the calculator parses
            if isinstance(value, str):
                try:
                    return float(value)
                except ValueError:
                    return value
            if isinstance(value, bool):
                raise TypeError('Expected a number')
            return float(value) if isinstance(value, (int, float)) else value
    except (TypeError, ValueError) as e:
        raise ApiError('invalid_argument', f"Invalid value for '{name}': {e}", 422, name)
    return value


def decode_inputs(addr, raw) -> dict:
    """Turn the JSON ``inputs`` object into keyword arguments. Omitted arguments keep the function's default."""
    if raw is None:
        raw = {}
    if not isinstance(raw, dict):
        raise ApiError('bad_request', "'inputs' must be an object", 400)

    parameters = inspect.signature(addr).parameters
    for key in raw:
        if key not in parameters:
            raise ApiError('unknown_argument', f"Unknown argument '{key}'", 422, key)

    args = {}
    for name, parameter in parameters.items():
        if parameter.kind in (parameter.VAR_POSITIONAL, parameter.VAR_KEYWORD):
            continue
        if name in raw:
            args[name] = _coerce(name, api_unpack_value(raw[name]), parameter)
        elif parameter.default is inspect.Parameter.empty:
            raise ApiError('missing_argument', f"Missing required argument '{name}'", 422, name)
    return args


def enforce_quota(api_key) -> None:
    """Count one run against the key's rate limits; raises ApiError 429 when a limit is reached."""
    try:
        consume_api_quota(api_key)
    except ApiQuotaExceeded as e:
        raise ApiError('rate_limited', str(e), 429, headers={'Retry-After': str(e.retry_after)})


def run_calculator(func_id: str, inputs=None, mode: str = 'full', request=None) -> dict:
    if mode not in MODES:
        raise ApiError('bad_request', f"'mode' must be one of: {', '.join(MODES)}", 400)

    addr = _resolve(func_id)
    args = decode_inputs(addr, inputs)

    pref = dict(gs)
    try:
        timeout = min(900, max(1, int(float(pref.get('execution_timeout', 60)))))
    except (TypeError, ValueError):
        timeout = 60

    started = time.time()
    try:
        result = q0164_execute_qfunc(func_id, args, timeout=timeout, pref=pref, request=request)
    except TimeoutError as e:
        raise ApiError('timeout', str(e), 504)
    except ApiError:
        raise
    except Exception as e:
        logger.info('API: %s failed: %s', func_id, e)
        raise ApiError('calc_error', str(e) or type(e).__name__, 422)

    if isinstance(result, qerror):
        raise ApiError('calc_error', str(result), 422)

    return {
        'version': API_VERSION,
        'function': func_id,
        'mode': mode,
        'result': api_pack_value(result, compact=(mode == 'compact')),
        'elapsed_ms': int((time.time() - started) * 1000),
    }
