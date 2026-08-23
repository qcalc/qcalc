# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from qcore import Qty, qtexta, qchar
from qutil import cal_link, page_link, calurl
from calc import gender_choice, list2options
# from calculators.all.general.mod_chart import pie
from datetime import date


def demo_addx__info():
    return {
        'title': 'Add two numbers',
        'inserts': {
            'form_bottom':
                page_link('/page/about/', caption='add about page') + '<br>' +
                cal_link(calurl('demo_addx', 'x/-20.1/y/12'), caption='add first', target='f') + '<br>' +
                cal_link(calurl('demo_addx', 'x/-10.1/y/12'), caption='add before', target='b') + '<br>' +
                cal_link(calurl('demo_addx', 'x/0.1/y/13'), caption='replace', target='r') + '<br>' +
                cal_link(calurl('demo_addx', 'x/10.1/y/10'), caption='add after', target='a') + '<br>' +
                cal_link(calurl('demo_addx', 'x/20.1/y/10'), caption='add last', target='l') + '<br>' +
                cal_link(calurl('demo_addx', 'x/-2/y/12'), caption='add first', target='f', button=True) + '<br>' +
                cal_link(calurl('demo_addx', 'x/-1/y/12'), caption='add before', target='b', button=True) + '<br>' +
                cal_link(calurl('demo_addx', 'x/0/y/13'), caption='replace', target='r', button=True) + '<br>' +
                cal_link(calurl('demo_addx', 'x/1/y/11'), caption='add after', target='a', button=True) + '<br>' +
                cal_link(calurl('demo_addx', 'x/2/y/10'), caption='add last', target='l', button=True),
        },
        'schema': {
            'x': {'required': True, 'help_text': 'returns x+y and a+b', 'initial': 2.5},
            'dummy': {
                'required': True,
                'help_text':
                    '''
                    Hello World, dummy is going to be a , what can i say, very very long sentence.
                    And there are multiple lines as well.
                    '''
            },
        },
    }


def demo_addx(x: float = 2.0, y=3.0, a='3 ft', b='20 inch', dummy: qchar = 'ok', dummy_part=5):
    z = x + y
    t = Qty(a) + Qty(b)
    return z, t


def demo_fldgrp__info():
    return {}


def demo_fldgrp(xqty='5 ft', xqty_part='3 inch', yqty='30 kg',
           zval=10, zval_1_part=20, zval_2_part=30,
           tval='100 m', tval_1_part='20 cm', tval_2_part='5 mm',
           wval=1200):
    return wval


def demo_multipart__info():
    return {}


def demo_multipart(length='@yd, @ft, @inch'):
    lengthq = Qty(length, 'ft')
    return lengthq


# --------------------------------------------------------------
# def myaddx(addx: qfunc, y=13): return  # recommended approach

# qCalc functions are not supportive of recursive calling or
# forming an expression using multiple functions
# because the data (json*) is common to all functions
# it is possible though to build static functions based on local data class
# at the moment no urgent requirement of that kind
# def mymyaddx(myaddx: qfunc): return  # not feasible
# def myaddx2(y=13): return addx(y=y)  # may work but not recommended

# def mymyaddx2():return myaddx2()  # not feasible
# def myinvlevel(invlevel: qfunc): return

# def myinvlevel2(myinvlevel: qfunc):return myinvlevel  # not feasible
# --------------------------------------------------------------

# def mygold(gold: qfunc): return

# def mypareq(pareq: qfunc, variations=10): return

# def demo_estyn(proceed=True):
#     return proceed


def demo_estfrm__info():
    return {
        'newcol': ['m1', 'm4'],
        'endcol': ['m3', 'm6'],
        'newrow': ['x', 'vtext', 'vcheck', 'vchoice'],
        'inarow': ['y', 'vfloat'],
        'endrow': ['z', 'vinteger', 'vfalse', 'vradio'],
        'schema': {
            'wt_uom_type': {'type': 'uom', 'initial': 'kg'},
            'length_uom_type': {'type': 'uom', 'initial': 'ft'},
            'vdate': {'type': 'date', 'initial': date(2020, 1, 20)},
            'vtext': {'type': 'text'},
            'vfloat': {'type': 'float'},
            'vinteger': {'type': 'integer'},
            'vchoice': {'type': 'choice',
                        'choices': [{'name': 'choice 1', 'value': 'value 1'},
                                    {'name': 'choice 2', 'value': 'value 2'}]},
            'vradio': {'type': 'radio',
                       'choices': [{'name': 'choice 1', 'value': 'value 1'},
                                   {'name': 'choice 2', 'value': 'value 2'}]},
            'vcheck': {'type': 'checkbox'},
        },
    }


def demo_estfrm(
    x=1,
    y=1.0,
    z='Hello World',
    t=1,
    velocity=100, velocity_uom='mph',
    wt=10, wt_uom='g',
    wt_uom_type=None,
    length_uom_type=None,
    vdate=None,
    vtext=None,
    vfloat=None,
    vinteger=None,
    vchoice=None,
    vradio=None,
    vcheck=None,
    vfalse=False,
    m1=1,
    m2=2,
    m3=3,
    m4='4 ft',
    m5='6 ft',
    m6=6,
    tx: qtexta = "Hello World!"
):
    return x, y, z, velocity, velocity_uom, wt, wt_uom, wt_uom_type, length_uom_type, vdate, \
        vtext, vfloat, vinteger, vchoice, vradio, vcheck, vfalse, m1, m2, m3, m4, m5, m6, tx


def demo_chkl__info():
    return {}


def demo_chkl(sex=list2options(gender_choice, initial='M', type='choice')):
    return sex


def demo_lay4__info():
    return {
        'title': 'Layout Testing Row and Column',
        'row': ["4-v", "q-s"],
        'col': ["b-d", "e-g"]
    }


def demo_lay4(x='99 g', y=1, z=2,
          t=3, u='4 ft', v=5,
          w='6g', p=7,
          q=8, r='5 ft', s='',
          a='', b='', c='', d='', e='', f='', g='', h=''):
    return x


def demo_lay3__info():
    return {
        'title': 'Layout Multielement Row',
        'row': ["t-v", "q-s"],
    }


def demo_lay3(x='99 g', y=1, z=2,
          t=3, u='4 ft', v=5,
          w='6g', p=7,
          q=8, r='5 ft', s='',
          a='', b='', c='', d='', e='', f='', g='', h=''):
    return x


def demo_lay2__info():
    return {
        'title': 'Layout Multielement Column',
        'col': ["t-v", "w-s"],
    }


def demo_lay2(x='99 g', y=1, z=2,
          t=3, u='4 ft', v=5,
          w='6g', p=7,
          q=8, r='5 ft', s='',
          a='', b='', c='', d='', e='', f='', g='', h=''):
    return x


def demo_lay1__info():
    return {
        'title': 'Test Column laytout with UOM',
        'col': ['x-y', 'z-t'],
    }


def demo_lay1(x=5, y='6 ft', z=7, t='8 ft'):
    return x, y, z, t


def demo_lay0__info():
    return {
        'title': 'Test Column laytout no UOM',
        'col': ['x-y', 'z-t'],
    }


def demo_lay0(x=5, y=6, z=7, t=8):
    return x, y, z, t
