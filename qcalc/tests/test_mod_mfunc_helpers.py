# SPDX-License-Identifier: MIT
# Tests moved from qcalc/calc/mod_mfunc.py — improved assertions based on original examples

import qsett
from qcore import qfunc
from qcalc.calc.mod_mfunc import (
    func_meta,
    q0162_dictify_fargs,
    flatten_fargs,
    get_fdef,
)

from calculators.all.health import bodyfat
from calculators.all.family import gold
DO_PRINT = False


def test_flatten_and_dictify_roundtrip_simple():
    # simple nested function-reference structure (mirrors original examples)
    fa = {'a': 1, 'b': 2, 'c': 3}
    ff = flatten_fargs(fa)
    uf = q0162_dictify_fargs(ff)
    assert fa == uf

    fb = {'x': 11, 'y': 12, 'z': 13, 'f1': {'func': 'fa', 'args': fa}}
    fc = {'u': 21, 'f2': {'func': 'fb', 'args': fb}, 'v': 22, 'w': 23}
    fd = {
        'xx': 31,
        'f3': {'func': 'fc', 'args': fc},
        'yy': 32,
        'zz': 33,
        'f2': {'func': 'fb', 'args': fb},
        'tt': 34,
    }

    flat = flatten_fargs(fd)
    unflat = q0162_dictify_fargs(flat)
    flat2 = flatten_fargs(unflat)
    unflat2 = q0162_dictify_fargs(flat2)
    # round-trip should preserve the flattened mapping
    assert flat2 == flat
    assert unflat2 == unflat


def test_flatten_and_dictify_roundtrip_simple_minimal():
    fa = {'a': 1, 'b': 2}
    flat = flatten_fargs(fa)
    unflat = q0162_dictify_fargs(flat)
    flat2 = flatten_fargs(unflat)
    assert flat2 == flat


def test_call_f_with_simple_function():
    def simple(a=1, b=2):
        return a + b

    # call_f should call the function using its default args
    assert call_f(simple) == 3


def call_f(fadr):
    def call_func(fadr, fk, fa):
        for arg in fa:
            # print(arg, fa[arg], type(fa[arg]), type(fa[arg]) == dict)
            if isinstance(fa[arg], dict):
                # print(fk)
                res = call_func(fk[arg]['func'], fk[arg]['args'], fa[arg])
                # print(res)
                fk[arg] = res
                fa[arg] = None
        # print(fk)
        # res = f(**fk)
        res = fadr(**fk)
        return res

    fk, fa, fi = get_fdef(fadr, fadr.__name__)
    res = call_func(fadr, fk, fa)
    return res

def tst_func(faddr, func_id):
    flat_fargs, flat_fanns, flat_finfs = func_meta(faddr, func_id)
    unflat_flat_fargs = q0162_dictify_fargs(flat_fargs)
    flat_unflat_flat_fargs = flatten_fargs(unflat_flat_fargs)
    if DO_PRINT:
        print('flat_fargs: ', flat_fargs)
        print('unflat_flat_fargs: ', unflat_flat_fargs)
        print('flat_unflat_flat_fargs', flat_unflat_flat_fargs)
        print('---')
    assert (flat_unflat_flat_fargs == flat_fargs)


def test_flat_unflat_flat():
    tst_func(callf1, 'callf1')
    tst_func(callf2, 'callf2')
    tst_func(callf3, 'callf3')
    tst_func(callf4, 'callf4')


def callf1(x=10, bf: qfunc = bodyfat, y='3ft'):
    # args={'age': 35, 'sex': 'F'}
    # res = call_f(f) #, args)
    return bf['Body Fat Average (%)']


def callf2__info():
    return {
        'title': 'callf2',
        'schema': {
            'age': {'label': 'Age in years'},
            'sex': {'label': 'Gender'}
        }
    }


def callf2(age: float = 35.0, sex='F'):
    kwargs = {'age': 35, 'sex': 'F'}
    return bodyfat(**kwargs)


def callf3__info():
    return {
        'title': 'callf3',
        'schema': {
            'x': {'label': 'Mars'},
            'y': {'label': 'Venus'}
        },
        'autofill': {
            'fill': {
                'fields': ['x', 'email'],
                'autofill': {'1': [10, 'hello@there.com'], '2': [20, 'hi@there.net']}
            }
        },
        'showhide': {'__': {'fields': ['fg--making_charge_pct']}},
    }


def callf3(fill=1, x=100, email='', f1: qfunc = callf1, fg: qfunc = gold):
    # res3 = call_func(f3) > call_f1, gold > bodyfat
    # print(res3)
    # res2 = call_f(f2)
    return fg['Gold Weight'], f1


def callf4__info():
    return {
        'title': 'callf4',
        'schema': {
            'x': {'label': 'Factor'},
            'y': {'label': 'Multiplier'}
        }
    }


def callf4(f3: qfunc = callf3, f1: qfunc = callf1, x='5 ft', y='100.0'):
    return f3, f1


def tst1():
    res = get_fdef(bodyfat, 'bodyfat')
    print(res)
    res = get_fdef(gold, 'gold')
    print(res)
    res = get_fdef(callf1, 'calf1')
    print(res)
    print(callf2())
    print(call_f(callf2))  # no qfunc - still works
    res = get_fdef(callf2, 'callf2')
    print(res)
    # print(callf)  # has qfunc - hence don't work
    print(call_f(callf1))  # has qfunc - works
    print(call_f(callf3))  # has qfunc - works
    print(call_f(callf4))


def test_func():
    faddr = callf3
    func_id = "callf3"
    flat_fargs, flat_fanns, flat_finfs = func_meta(faddr, func_id)

    if DO_PRINT:
        print('flat_fargs: ', flat_fargs)
        print('unflat_fargs: ', q0162_dictify_fargs(flat_fargs))
        print('flat_fanns: ', flat_fanns)
        print('unflat_fanns: ', q0162_dictify_fargs(flat_fanns))
        print('flat_finfs: ', flat_finfs)
        print('unflat_finfs: ', q0162_dictify_fargs(flat_finfs))

    assert flat_fargs == {'fill': 1, 'x': 100, 'email': '', 'f1--@': 'callf1', 'f1--x': 10, 'f1--bf--@': 'bodyfat', 'f1--bf--age': '30.0 yr', 'f1--bf--sex': 'M', 'f1--bf--triceps': '7 mm', 'f1--bf--biceps': '5 mm', 'f1--bf--chest': '8 mm', 'f1--bf--subscapular': '4 mm', 'f1--bf--abdominal': '6 mm', 'f1--bf--suprailiac': '10 mm', 'f1--bf--thigh': '8 mm', 'f1--bf--axilla': '3 mm', 'f1--bf--show_details': False, 'f1--y': '3ft', 'fg--@': 'gold', 'fg--gold_weight_intl': '10.0 g', 'fg--gold_weight_india': '@vori, @anna, @roti, @point', 'fg--gold_price': '150 USD', 'fg--gold_price_per': 'g', 'fg--vat_pct': 5.0, 'fg--making_charge_pct': 6.0}
    assert flat_fanns == {'fill': None, 'x': None, 'email': None, 'f1--@': 'callf1', 'f1--x': None, 'f1--bf--@': 'bodyfat', 'f1--bf--age': None, 'f1--bf--sex': None, 'f1--bf--triceps': None, 'f1--bf--biceps': None, 'f1--bf--chest': None, 'f1--bf--subscapular': None, 'f1--bf--abdominal': None, 'f1--bf--suprailiac': None, 'f1--bf--thigh': None, 'f1--bf--axilla': None, 'f1--bf--show_details': None, 'f1--y': None, 'fg--@': 'gold', 'fg--gold_weight_intl': None, 'fg--gold_weight_india': None, 'fg--gold_price': None, 'fg--gold_price_per': None, 'fg--vat_pct': None, 'fg--making_charge_pct': None}
    # assert flat_finfs == {'schema': {'f1--bf--sex': {'type': 'radio', 'initial': 'M', 'choices': {'M': 'Male', 'F': 'Female'}}, 'fg--vat_pct': {'label': 'VAT %'}, 'fg--making_charge_pct': {'label': 'Making Charge %'}}, 'anyof': {'fg--1': {'fields': ['fg--gold_weight_intl', 'fg--gold_weight_india']}}}

    unflat_fargs = {'fill': 1, 'x': 100, 'email': '', 'f1': {'@': 'callf1', 'x': 10, 'bf': {'@': 'bodyfat', 'age': '30.0 yr', 'sex': 'M', 'triceps': '7 mm', 'biceps': '5 mm', 'chest': '8 mm', 'subscapular': '4 mm', 'abdominal': '6 mm', 'suprailiac': '10 mm', 'thigh': '8 mm', 'axilla': '3 mm', 'show_details': False}, 'y': '3ft'}, 'fg': {'@': 'gold', 'gold_weight_intl': '10.0 g', 'gold_weight_india': '@vori, @anna, @roti, @point', 'gold_price': '150 USD', 'gold_price_per': 'g', 'vat_pct': 5.0, 'making_charge_pct': 6.0}}
    unflat_fanns = {'fill': None, 'x': None, 'email': None, 'f1': {'@': 'callf1', 'x': None, 'bf': {'@': 'bodyfat', 'age': None, 'sex': None, 'triceps': None, 'biceps': None, 'chest': None, 'subscapular': None, 'abdominal': None, 'suprailiac': None, 'thigh': None, 'axilla': None, 'show_details': None}, 'y': None}, 'fg': {'@': 'gold', 'gold_weight_intl': None, 'gold_weight_india': None, 'gold_price': None, 'gold_price_per': None, 'vat_pct': None, 'making_charge_pct': None}}
    unflat_finfs = {'f1': {'@': 'callf1', 'bf': {'@': 'bodyfat', 'schema': {'sex': {'type': 'radio', 'initial': 'M', 'choices': {'M': 'Male', 'F': 'Female'}}}}}, 'fg': {'@': 'gold', 'schema': {'vat_pct': {'label': 'VAT %'}, 'making_charge_pct': {'label': 'Making Charge %'}}, 'anyof': {'1': {'fields': ['gold_weight_intl', 'gold_weight_india']}}}}

    assert q0162_dictify_fargs(flat_fargs) == unflat_fargs
    assert q0162_dictify_fargs(flat_fanns) == unflat_fanns
    # assert q0162_dictify_fargs(flat_finfs) == unflat_finfs
