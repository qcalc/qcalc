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


def test_safe_execute_exposes_qapi_symbols():
    local_dict = safe_execute(
        "from qapi import Qty, qtexta\nresult = (Qty('2 m').to('cm').value, qtexta.__name__)"
    )

    assert local_dict["result"] == (200, "qtexta")


def test_safe_execute_exposes_qapi_annotations_as_globals():
    local_dict = safe_execute(
        "def addlen(x: qtc2 = '7 ft'):\n    return Qty(x)\nresult = addlen.__annotations__['x']"
    )

    assert local_dict["result"].__name__ == "qtc2"


def test_retirement_sustainability_reports_zero_return_zero_inflation_depletion():
    from calculators.all.finance.cal_retirement import retirement_sustainability

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
