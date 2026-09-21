# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from __future__ import annotations

import pandas as pd

from .mod_cache import QData


def _pack_payload(payload):
    if isinstance(payload, pd.DataFrame):
        return {
            '__shared_kind': 'dataframe',
            'columns': [str(col) for col in payload.columns],
            'data': payload.values.tolist(),
        }
    return payload


def _unpack_payload(payload):
    if isinstance(payload, dict) and payload.get('__shared_kind') == 'dataframe':
        return pd.DataFrame(payload.get('data', []), columns=payload.get('columns', []))
    return payload


def _dataset_slot(dataset_key: str) -> str:
    return f'shared_dataset:{dataset_key.strip().lower()}'


def _type_slot(dataset_type: str) -> str:
    return f'shared_dataset_type:{dataset_type.strip().lower()}'


def publish_shared_dataset(
    dataset_type: str,
    payload,
    dataset_key: str | None = None,
    producer_func: str = '',
    schema_info: dict | None = None,
) -> dict:
    dataset_type = (dataset_type or '').strip().lower()
    if dataset_type == '':
        raise ValueError('dataset_type is required')

    dataset_key = (dataset_key or dataset_type).strip().lower()

    record = {
        'dataset_key': dataset_key,
        'dataset_type': dataset_type,
        'producer_func': producer_func,
        'schema_info': schema_info or {},
        'payload': _pack_payload(payload),
    }

    QData.setp1(_dataset_slot(dataset_key), record)
    QData.setp1(_type_slot(dataset_type), {
        'dataset_key': dataset_key,
        'dataset_type': dataset_type,
        'producer_func': producer_func,
    })

    return {
        'dataset_key': dataset_key,
        'dataset_type': dataset_type,
    }


def _resolve_dataset_key(dataset_type: str = '', dataset_key: str = '') -> str:
    dataset_key = (dataset_key or '').strip().lower()
    if dataset_key:
        return dataset_key

    dataset_type = (dataset_type or '').strip().lower()
    if dataset_type == '':
        return ''

    index = QData.getp1(_type_slot(dataset_type), {})
    if isinstance(index, dict):
        return (index.get('dataset_key') or '').strip().lower()
    return ''


def get_shared_dataset(dataset_type: str = '', dataset_key: str = '') -> dict | None:
    resolved_key = _resolve_dataset_key(dataset_type, dataset_key)
    if resolved_key == '':
        return None

    record = QData.getp1(_dataset_slot(resolved_key), None)
    if not isinstance(record, dict):
        return None

    out = record.copy()
    out['payload'] = _unpack_payload(out.get('payload'))
    return out
