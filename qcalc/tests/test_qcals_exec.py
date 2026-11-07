# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha
# Tests generated with AI assistance. Reviewed and validated by the author.

import pytest

import qconst
from qcore import Qty
from qutil import safe_execute


@pytest.mark.parametrize(
    "module_name",
    [
        "qapi", "math", "cmath", "statistics", "decimal",
        "datetime", "calendar", "random", "itertools", "collections", "re", "json",
    ],
)
def test_safe_execute_allows_allowlisted_import(module_name):
    local_dict = safe_execute(f"import {module_name}\nresult = 3")

    assert local_dict["result"] == 3


@pytest.mark.parametrize("module_name", ["qcore", "calc", "qutil", "pathlib", "os"])
def test_safe_execute_rejects_non_allowlisted_import(module_name):
    with pytest.raises(ImportError):
        safe_execute(f"import {module_name}")


def test_safe_execute_explains_how_to_find_allowed_modules():
    with pytest.raises(
        ImportError,
        match=r"Remove it or use qmodules\(\) to see the allowed modules\.",
    ):
        safe_execute("import pathlib")


def test_safe_execute_exposes_qapi_symbols():
    local_dict = safe_execute(
        "from qapi import Qty, qtexta\nresult = (Qty('2 m').to('cm').value, qtexta.__name__)"
    )

    assert local_dict["result"] == (200, "qtexta")


def test_safe_execute_exposes_qlist():
    local_dict = safe_execute(
        "from qapi import QList\n"
        "result = (\n"
        "    QList(['2', '30']).add(1),\n"
        "    QList([1, 2]).mul([3, 4]).sum(),\n"
        "    QList([]).sum(),\n"
        "    QList([4, 8]).div(2),\n"
        "    QList([1, 2]).binary(10, lambda a, b: b - a, reverse=False),\n"
        ")"
    )

    assert local_dict["result"] == ([3, 31], 11, 0, [2, 4], [9, 8])


def test_qlist_quantities_and_errors():
    from qcore import QList
    import operator

    assert QList(['2 m', '30 cm']).sum() == Qty('2.3 m')
    assert QList([]).sum() == 0
    assert QList([1, 2]).binary(10, operator.sub, reverse=True) == [9, 8]
    assert QList(['2', '30']).apply(lambda a: a + 50) == [52, 80]
    with pytest.raises(ValueError):
        QList([1, 2]).add([1])
    with pytest.raises(TypeError):
        QList('abc')
    with pytest.raises(TypeError):
        QList([1]).apply(5)


def test_safe_execute_exposes_qapi_annotations_as_globals():
    local_dict = safe_execute(
        "def addlen(x: qtc2 = '7 ft'):\n    return Qty(x)\nresult = addlen.__annotations__['x']"
    )

    assert local_dict["result"].__name__ == "qtc2"


def test_safe_execute_functions_can_call_helpers():
    local_dict = safe_execute(
        "def normalize(value):\n"
        "    return value + 1\n\n"
        "def calculate(value=1):\n"
        "    return normalize(value)\n"
    )

    assert local_dict["calculate"]() == 2


def test_retirement_sustainability_reports_zero_return_zero_inflation_depletion():
    from calculators.all.family import retirement_sustainability

    result = retirement_sustainability(
        portfolio='1000 USD',
        withdrawal='200 USD/yr',
        investment_return='0 pct/yr',
        inflation='0 pct/yr',
        retirement_period='10 yr',
    )

    assert result['Depletion Period (0% Return, 0% Inflation)'] == Qty('5 yr')


def test_safe_execute_allows_legacy_imports_when_explicitly_enabled(monkeypatch):
    monkeypatch.setattr(qconst, "ALLOW_UNSAFE_USER_CALCULATOR_IMPORTS", True)

    local_dict = safe_execute("import statistics\nresult = statistics.mean([1, 2, 3])")

    assert local_dict["result"] == 2
