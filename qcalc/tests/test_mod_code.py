# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha
# Tests generated with AI assistance. Reviewed and validated by the author.

import pytest

from qutil.mod_code import ensure_calculator_info, extract_calculator_name


def test_extract_calculator_name_allows_helper_functions():
    functions = [
        'calculate',
        'normalize',
        'validate',
        'calculate__info',
        'calculate__help',
    ]

    assert extract_calculator_name(functions) == 'calculate'


def test_extract_calculator_name_rejects_multiple_info_functions():
    with pytest.raises(Exception, match='Multiple calculator info functions'):
        extract_calculator_name([
            'calculate',
            'calculate__info',
            'convert',
            'convert__info',
        ])


def test_ensure_calculator_info_rejects_ambiguous_functions():
    code = (
        "def calculate(value):\n"
        "    return normalize(value)\n\n"
        "def normalize(value):\n"
        "    return float(value)\n"
    )

    with pytest.raises(Exception, match='Cannot determine the main calculator'):
        ensure_calculator_info(code)


def test_ensure_calculator_info_uses_explicit_calculator_name():
    code = (
        "def calculate(value):\n"
        "    return normalize(value)\n\n"
        "def normalize(value):\n"
        "    return float(value)\n"
    )

    modified_code, functions = ensure_calculator_info(code, 'calculate')

    assert 'def calculate__info():' in modified_code
    assert functions[-1] == 'calculate__info'


def test_ensure_calculator_info_generates_info_from_the_function():
    code = (
        "def addlen(x='7 ft', mode='sum', use_extra=False):\n"
        '    """Add two lengths."""\n'
        "    if mode == 'diff':\n"
        "        return x\n"
        "    return x\n"
    )

    modified_code, functions = ensure_calculator_info(code)
    spec = {}
    exec(modified_code, {}, spec)
    info = spec['addlen__info']()

    assert info['title'] == 'Addlen' and info['desc'] == 'Add two lengths.'
    assert info['schema']['mode']['choices'] == {'sum': 'Sum', 'diff': 'Diff'}
    assert functions[-1] == 'addlen__info'


def test_ensure_calculator_info_keeps_code_with_qcalc_marker():
    code = "@qcalc\ndef addlen(x=1.0):\n    return x\n"

    assert ensure_calculator_info(code)[0] == code


def test_ensure_calculator_info_empty_code_gets_a_generated_template():
    modified_code, functions = ensure_calculator_info('')

    assert 'def newcal(' in modified_code and functions[-1] == 'newcal__info'
