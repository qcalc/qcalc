# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import inspect

from django.core.exceptions import ValidationError

from .timed_thread import QThread


def _schema_from_info_function(func_id: str, caller):
    module = inspect.getmodule(caller)
    if module is None:
        return {}

    info_fn = getattr(module, f'{func_id}__info', None)
    if not callable(info_fn):
        return {}
    return (info_fn() or {}).get('schema', {}) or {}


def validate_schema_if_needed(func_id: str):
    req = QThread.get_req()

    schema = None
    if req is not None:
        json_doc = getattr(req, 'json_doc', None) or {}
        info = json_doc.get('info', {}) or {}
        req_func_name = info.get('name', '')
        req_schema = info.get('schema', {}) or {}
        req_clean = bool(json_doc.get('clean'))

        if req_func_name == func_id:
            if req_clean:
                return
            schema = req_schema

    frame = inspect.currentframe()
    caller = frame.f_back if frame is not None else None
    if caller is None:
        return

    if schema is None:
        schema = _schema_from_info_function(func_id, caller)

    values = dict(caller.f_locals)

    errors = []
    for field, spec in schema.items():
        if not isinstance(spec, dict):
            continue

        validators = spec.get('validators', []) or []
        if not validators:
            continue

        value = values.get(field)
        for validator in validators:
            try:
                validator(value)
            except ValidationError as e:
                msg = '; '.join(getattr(e, 'messages', [str(e)]))
                errors.append(f'{field}: {msg}')
            except Exception as e:
                errors.append(f'{field}: {e}')

    if errors:
        raise Exception('Input validation failed: ' + ' | '.join(errors))
