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
