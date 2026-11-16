# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

import pytest

import qapi
from qutil import safe_execute
from qutil.mod_code_security import dangerous_keywords, UnsafeCodeError

# helpers that reach network, threads, request/settings, or hand out raw pandas objects
NEVER_EXPORT = [
    'QThread', 'fetch_url', 'url2text', 'url2html', 'soup2text', 'qaddr', 'qdomain', 'is_loggedin',
    'local_ip', 'user_process',
    'validate_schema_if_needed', 'list2table', 'df2normalized', 'as_qtable', 'qtable', 'csv2df', 'np2df',
]


def test_exported_names_resolve_and_are_unique():
    assert len(qapi.__all__) == len(set(qapi.__all__))
    assert [name for name in qapi.__all__ if not hasattr(qapi, name)] == []
    assert not set(qapi.__qtypes__) & set(qapi.__evacon__)


def test_unsafe_helpers_are_not_exported():
    assert not set(NEVER_EXPORT) & set(qapi.__all__)
    assert not set(dangerous_keywords) & set(qapi.__all__)


def test_exported_helpers_run_in_sandbox():
    code = (
        "r = (nzv(None), nzs(None), truncate('abcdef', 3), word_count('a b c')[0],\n"
        "     to_python_expr('2x^2'), xpr_coeffs('3x-2y'), step2_spec('f', 'Go')['step'],\n"
        "     QTimezone.from_offset('+06:00') is not None)"
    )
    result = safe_execute(code)['r']
    assert result == (0, '', 'abc... Truncated', 3, '2*x**2', [3.0, -2.0], 'run', True)


@pytest.mark.parametrize("name", ['QThread', 'fetch_url', 'as_qtable'])
def test_unsafe_helpers_are_unavailable_in_sandbox(name):
    with pytest.raises((UnsafeCodeError, NameError)):
        safe_execute(f"{name}")
