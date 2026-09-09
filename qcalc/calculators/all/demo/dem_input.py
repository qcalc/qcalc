# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from qcore.mod_anno import *


def demo_input__info():
    ptrn = r'^\w{3,5}$'
    return {
        'title': 'Demonstrating Various Input Types',
        'interactive': True,
        'schema': {
            'bool_input': {'help_text': 'Boolean input.'},
            'float_input': {'help_text': 'Floating-point number input.'},
            'int_input': {'help_text': 'Integer input.'},
            'qchar_input': {
                'help_text': 'Short character input.',
                'attrs': {'placeholder': 'Enter a short string'},
            },
            'qcode_input': {'help_text': 'Source-code editor input.'},
            'qdate_input': {'help_text': 'Date input.'},
            'qdatetime_input': {'help_text': 'Date and time input.'},
            'qdict_input': {'help_text': 'Fixed dictionary input.'},
            'qemail_input': {
                'help_text': 'Email address input.',
                'attrs': {'placeholder': 'Enter a valid email'}
            },
            'qfile_input': {'help_text': 'File upload input.'},
            'qfl_input': {'help_text': 'Floating-point short input.'},
            'qfunc_input': {'help_text': 'qCalc function input.'},
            'qimage_input': {'help_text': 'Image upload input.'},
            'qin_input': {'help_text': 'Integer short input.'},
            'qlist_input': {'help_text': 'Dynamic list input.'},
            'qread_input': {'help_text': 'Read-only text input.'},
            'qregex_input': {'help_text': 'Regular-expression input.'},
            'qsel2_input': {
                'choices': ['A', 'B', 'C'],
                'help_text': 'Enhanced select input.'
            },
            'qt_input': {'help_text': 'Quantity input with a unit.'},
            'qt2_input': {'help_text': 'Quantity input with a unit selector.'},
            'qtable_input': {'help_text': 'Editable table input.'},
            'qtbl_input': {'help_text': 'Safe editable table input.'},
            'qtc_input': {'help_text': 'Composite quantity input.'},
            'qtc2_input': {'help_text': 'Composite quantity input with a unit selector.'},
            'qtext_input': {'help_text': 'Text input.'},
            'qtexta_input': {'help_text': 'Multi-line text input.'},
            # 'qtexte_input': {'help_text': 'Rich text editor input.'},
            'qtime_input': {'help_text': 'Time input.'},
            'qtx_input': {'help_text': 'Quantity input accepting any unit.'},
            'quom_input': {'help_text': 'Compatible unit input.'},
            'quom2_input': {'help_text': 'Compatible unit select input.'},
            'quomx_input': {'help_text': 'Any valid unit input.'},
            'qurl_input': {'help_text': 'URL input.'},
            'str_input': {'help_text': 'Text string input.'},
            'checkbox_input': {
                'type': 'checkbox',
                'help_text': 'Checkbox input configured through schema.',
            },
            'checkboxselectmultiple_input': {
                'type': 'checkboxselectmultiple',
                'choices': ['A', 'B', 'C'],
                'help_text': 'Multiple checkbox choices configured through schema.',
            },
            'choice_input': {
                'type': 'choice',
                'choices': ['A', 'B', 'C'],
                'help_text': 'Single select choice configured through schema.',
            },
            'decimal_input': {
                'type': 'decimal',
                'help_text': 'Decimal number input configured through schema.',
            },
            'duration_input': {
                'type': 'duration',
                'help_text': 'Duration input configured through schema.',
            },
            'multiplechoice_input': {
                'type': 'multiplechoice',
                'choices': ['A', 'B', 'C'],
                'help_text': 'Multiple select choices configured through schema.',
            },
            'nullboolean_input': {
                'type': 'nullboolean',
                'help_text': 'Three-state Boolean input configured through schema.',
            },
            'radio_input': {
                'type': 'radio',
                'choices': ['A', 'B', 'C'],
                'help_text': 'Radio-button choice configured through schema.',
            },
            'range_input': {
                'type': 'range',
                'attrs': {'step': '1', 'min': '1', 'max': '10'},
                'help_text': 'Range input from 1 to 10 configured through schema.',
            },
            'rchoice_input': {
                'type': 'rchoice',
                'choices': ['A', 'B', 'C'],
                'help_text': 'Non-validating choice input configured through schema.',
            },
            'slug_input': {
                'type': 'slug',
                'help_text': 'Slug input configured through schema.',
            },
            'textarea_input': {
                'type': 'textarea',
                'help_text': 'Multi-line text input configured through schema.',
            },
            'typedmultiplechoice_input': {
                'type': 'typedmultiplechoice',
                'choices': ['A', 'B', 'C'],
                'help_text': 'Typed multiple choice input configured through schema.',
            },
            'uuid_input': {
                'type': 'uuid',
                'help_text': 'UUID input configured through schema.',
            },
        },
        'outcol': 'result'
    }


def demo_input(
    bool_input: bool = True,
    float_input: float = 5.67,
    int_input: int = 123,
    qchar_input: qchar = 'Hello',
    qcode_input: qcode = 'print("Hello, qCalc!")',
    qdate_input: qdate = '2026-09-09',
    qdatetime_input: qdatetime = '2026-09-09 11:47:30',
    qdict_input: qdict = {'A': 1, 'B': 2},
    qemail_input: qemail = 'somebody@example.com',
    qfile_input: qfile = None,
    qfl_input: qfl = 5.67,
    qfunc_input: qfunc = 'bmi',
    qimage_input: qimage = None,
    qin_input: qin = 123,
    qlist_input: qlist[qchar] = ['A', 'B', 'C'],
    qread_input: qread = 'Read Only',
    qregex_input: qregex = r'^\w{3,5}$',
    qsel2_input: qsel2 = 'A',
    qt_input: qt = '1 ft',
    qt2_input: qt2 = '5 kg',
    qtable_input: qtable = pd.DataFrame({'Name': ['Dave', 'Arche', 'Mom']}),
    qtbl_input: qtbl = {'columns': ['Name'], 'data': [['Dave'], ['Arche'], ['Mom']]},
    qtc_input: qtc = '23 yd, 2 ft, 6 inch',
    qtc2_input: qtc2 = '5 kg',
    qtext_input: qtext = 'Some text',
    qtexta_input: qtexta = 'Some more text',
    # qtexte_input: qtexte = '<p>Rich text</p>', # not yet implemented fully
    qtime_input: qtime = '23:59:59',
    qtx_input: qtx = '5 kg',
    quom_input: quom = 'ft',
    quom2_input: quom2 = 'm',
    quomx_input: quomx = 'kg',
    qurl_input: qurl = 'https://www.google.com',
    str_input: str = 'A string',
    checkbox_input = True,
    checkboxselectmultiple_input = ['A', 'C'],
    choice_input = 'B',
    decimal_input = '100.50',
    duration_input = '1 02:30:00',
    multiplechoice_input = ['B', 'C'],
    nullboolean_input = None,
    radio_input = 'A',
    range_input = 5,
    rchoice_input = 'B',
    slug_input = 'calculator-input',
    textarea_input = 'Some more text',
    typedmultiplechoice_input = ['A', 'C'],
    uuid_input = '12345678-1234-5678-1234-567812345678',
):
    return locals()
