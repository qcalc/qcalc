import pytest

from qcore import Qty, find_unit, is_str_uom
from qcore.qc_units import _unit_table


@pytest.mark.parametrize("expr", [
    "__import__('os').getpid()",
    "m*(__import__('os').getpid()*0+1)",
    "().__class__",
    "m.__class__",
    "[x for x in (1,)]",
    "lambda: 1",
    "'a'*3",
    "m**9**9**9",
    "m**(1j)",
    "m" * 300,
])
def test_unit_expr_injection_rejected(expr):
    with pytest.raises(Exception):
        find_unit(expr)
    assert not is_str_uom(expr)
    assert '__builtins__' not in _unit_table


def test_injection_via_qty_string_rejected():
    with pytest.raises(Exception):
        Qty("5 m*(__import__('os').getpid()*0+1)")


def test_valid_unit_exprs_still_work():
    assert find_unit('kg*m/s^2').dimension == 'LMT-2'
    assert find_unit('m**-1').dimension == 'L-1'
    assert find_unit('m^0.5').powers[0] == 0.5
    assert Qty('5 ft').unit.dimension == 'L'
    assert is_str_uom('ft/s')
