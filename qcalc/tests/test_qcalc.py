# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import os
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

import pytest

import qapi
from calc import CalcSandbox
from qcore import qcalc, registered
from qutil.mod_code import get_functions, qcalc_names


@qcalc(title='Doubler', tags='demo')
def dbl(x=2.0):
    """Double a number."""
    return {'result': x * 2}


def secret():
    return 1


def test_qcalc_names_cover_every_declaration_form():
    code = (
        "@qcalc\ndef a(x=1): return x\n"
        "@qcalc(name='c', title='T')\ndef b(): pass\n"
        "def d(): pass\nqcalc(d)\n"
        "qcalc(qconvert, name='conv')\n"
    )
    assert sorted(qcalc_names(code)) == ['a', 'c', 'conv', 'd']
    assert {'a__info', 'c', 'c__info', 'conv', 'conv__info', 'd__info'} <= set(get_functions(code))


def test_backend_module_function_gets_generated_info():
    module = sys.modules[__name__]
    entries = registered(vars(module), vars(module))
    info = entries['dbl__info']()
    assert entries['dbl'] is dbl
    assert info['title'] == 'Doubler' and info['tags'] == 'demo' and info['desc'] == 'Double a number.'
    info['title'] = 'changed'
    assert entries['dbl__info']()['title'] == 'Doubler'  # | callers get a copy of the cached spec


def test_sandbox_registers_own_renamed_and_api_functions():
    code = (
        "@qcalc(name='conv')\n"
        "def addlen(x='7 ft', y='8 m'):\n"
        "    return x\n"
        "qcalc(qconvert)\n"
    )
    local = CalcSandbox.exec_with_context(code, 'test')
    assert local['conv'].__name__ == 'addlen' and local['conv__info']()['title'] == 'Conv'
    assert local['qconvert'] is qapi.qconvert and local['qconvert__info']()['title'] == 'Qconvert'


def test_explicit_info_wins_over_marker():
    code = "@qcalc(title='Generated')\ndef f(): pass\ndef f__info(): return {'title': 'Mine'}\n"
    assert CalcSandbox.exec_with_context(code, 'test')['f__info']()['title'] == 'Mine'


def test_a_misspelled_hint_suggests_the_right_one():
    with pytest.raises(TypeError, match="unknown qcalc hint 'out_schemax', did you mean 'out_schema'"):
        qcalc(secret, out_schemax={'result': 'map'})


def test_every_hint_build_info_reads_is_a_known_qcalc_hint():
    import re
    import qconst
    source = open(sys.modules['qcore.mod_info'].__file__, encoding='utf-8').read()
    read = set(re.findall(r"hints(?:\.get\(|\[)'(\w+)'", source)) | {'func_name'}

    assert read <= qconst.QCALC_HINTS


@pytest.mark.parametrize('code', [
    "qcalc(secret)",  # | a host function that is not exported through qapi
    "qcalc(Qty)",  # | not a function
    "@qcalc\n@qcalc\ndef f(): pass",  # | declared twice
    "g = qconvert\nqcalc(g)",  # | not given by its own name
    "@qcalc(name='a__b')\ndef f(): pass",
    "@qcalc(title=Qty)\ndef f(): pass",  # | hints must be literals
    "@qcalc(out_schemax={'result': 'map'})\ndef f(): pass",  # | a misspelled hint
    "def conv(): pass\n@qcalc(name='conv')\ndef f(): pass",  # | name of another function
])
def test_sandbox_rejects(code, monkeypatch):
    monkeypatch.setitem(CalcSandbox.symbols, 'secret', secret)
    with pytest.raises(Exception, match='QCM'):
        CalcSandbox.exec_with_context(code, 'test')
