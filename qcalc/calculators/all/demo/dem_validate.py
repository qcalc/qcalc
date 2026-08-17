# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from django.core.validators import validate_email
from qcore import qhide


def demo_vali__info():
    return {
        'title': 'Validation testing',
        'schema': {
            'a_autofill': {'type': 'choice', 'choices': [{'name': '1', 'value': '1'}, {'name': '2', 'value': '2'}]},
            'a_required': {'required': True, 'help_text': 'This field is required'},
            'b_read': {'attrs': {'readonly': True}},
            # 'c_hidden': {'attrs': {'hidden': True}},
            'd_disabled': {'disabled': True},
            'email': {'validators': [validate_email]}
        },
        "col": ['2-4', '5-8'],
        # "row":['8'],
        # "template": 'v4.21',
        'autofill': {
            'a_autofill': {
                'fields': ['a_required', 'email'],
                'autofill': {'1': [10, 'hello@there.com'], '2': [20, 'hi@there.net']}
            }
        }
    }


def demo_vali(a_autofill='1', a_required=5, b_read=1, c_hidden: qhide = 1, d_disabled=1, email='a@b.com', f='1 ft', g=5,
         h=8):
    return a_autofill, a_required, b_read, c_hidden, d_disabled, email, f, g, h
