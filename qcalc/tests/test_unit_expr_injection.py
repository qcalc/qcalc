# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha
# Tests generated with AI assistance. Reviewed and validated by the author.

import pytest

from qcore import Qty, UnitRegistry, QtyRegistry
from qutil.mod_code_security import validate_expression_security, UnsafeCodeError


@pytest.mark.parametrize("code", [
    "UnitRegistry._add('zzz', '1*m')",
    "UnitRegistry._load()",
    "UnitRegistry._table.clear()",
    "UnitRegistry._add_currencies({}, 1, {})",
    "QtyRegistry._add('zzz', '1 m', '')",
    "QtyRegistry._info.clear()",
])
def test_sandbox_cannot_reach_registry_mutators(code):
    with pytest.raises(UnsafeCodeError):
        validate_expression_security(code)


def test_registry_data_is_read_only():
    with pytest.raises(TypeError):
        UnitRegistry.table['zzz'] = UnitRegistry.table['m']
    with pytest.raises(TypeError):
        UnitRegistry.info['m']['long_name'] = 'x'
    with pytest.raises(TypeError):
        QtyRegistry.info['th_hair'] = None
    assert isinstance(UnitRegistry.tree['L'], tuple)
    assert 'zzz' not in UnitRegistry.table


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
        UnitRegistry.find(expr)
    assert not UnitRegistry.is_uom(expr)
    assert '__builtins__' not in UnitRegistry.table


def test_injection_via_qty_string_rejected():
    with pytest.raises(Exception):
        Qty("5 m*(__import__('os').getpid()*0+1)")


def test_valid_unit_exprs_still_work():
    assert UnitRegistry.find('kg*m/s^2').dimension == 'LMT-2'
    assert UnitRegistry.find('m**-1').dimension == 'L-1'
    assert UnitRegistry.find('m^0.5').powers[0] == 0.5
    assert Qty('5 ft').unit.dimension == 'L'
    assert UnitRegistry.is_uom('ft/s')
