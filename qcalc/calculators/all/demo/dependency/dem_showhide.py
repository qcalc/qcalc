# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from qcore import Qty, qfunc, qtc2, qtc, qt, qtx


def demo_showhide2__info():  # val
    return {
        'title': 'Show Hide (controls)',
        'schema':{
            'control_to_hide': {'type':'choice', 'choices':['x', 'y', 'z', 't', 'u']},
            'u': {'type': 'choice', 'choices': ['any', 'thing', 'goes']},
        },
        'showhide': {
            'control_to_hide': {'fields': ['y', 'z', 't', 'u'], 'callback':'sh2cb'},
            '__': {'fields': ['x', 'y']}
        },
        'script': """
        function sh2cb(v){
            //return [v!='x',v!='y',v!='z',v!='t',v!='u']
            return [v!='y', v!='z',v!='t',v!='u']
        }
        """
    }


def demo_showhide2(control_to_hide='x', x:float=5, y='5ft', z='5ft, 6inch',t='UNC',u='any'):
    '''hide selected controls'''
    return x, y, z, t, u


def demo_showhide__info():  # val
    return {
        'title': 'Show Hide (val)',
        'showhide': {
            'x': {'fields': ['y', 'z', 't']}
        },
        'row': ['x-y', 'z-t'],
    }


def demo_showhide(x=5, y=2, z='3', t='4', u=10):
    '''if x=empty show y,z,t else hide y,z,t'''
    return x, y, z, t


def demo_sh0__info():  # val+callback
    return {
        'title': 'Show Hide (val+callback)',
        'showhide': {
            'x': {'fields': ['y', 'z', 't'], 'callback': 'fcall'}
        },
        'script':
            'function fcall(v)'
            '{'
            'return v>2;'
            '}',
        'row': ['x-y', 'z-t'],
    }


def demo_sh0(x=5, y=2, z='3', t='4', u=10):
    '''if x>2 show y,z,t else hide y,z,t'''
    return x, y, z, t


def demo_sh1__info():  # qty+callback
    return {
        'title': 'Show Hide (qty+callback)',
        'showhide': {
            'x': {'fields': ['y', 'z', 't'], 'callback': 'fcall'}
        },
        'script':
            'function fcall(v)'
            '{'
            'return v>2;'
            '}',
        'row': ['x-y', 'z-t'],
    }


def demo_sh1(x=5, y=2, z = '3 ft', t = '4 kg,5 g, 6 mg', u=10):
    '''if x>2 show y,z,t else hide y,z,t'''
    z = Qty(z, 'ft')
    t = Qty(t, 'kg')
    return x, y, z, t


def demo_sh2__info():  # func (val+callback)
    return {
        'title': 'Show Hide (func+val)',
    }


def demo_sh2(shf: qfunc = demo_showhide):
    '''if shf--x=empty show y,z,t else hide y,z,t'''
    return shf


def demo_sh3__info():
    return {
        'title': 'Show Hide (func+val+callback)',
    }


def demo_sh3(shf: qfunc = demo_sh0):
    '''if shf--x>2 show y,z,t else hide y,z,t'''
    return shf
