from django import forms

from qconst import TOK_INDEX_SEP
from qcore.mod_qforms import QFieldHandler
from qcore.mod_qwidgets import QtyWidget


def test_qty_field_keeps_help_text():
    schema = [{
        'name': 'qty',
        'type': 'qty',
        'required': False,
        'label': 'Qty',
        'help_text': 'Enter a quantity',
        'comp': {
            'value': {
                'name': 'value',
                'type': 'text',
                'initial': '1',
                'sufx': '',
                'required': False,
            },
            'unit': {
                'name': 'unit',
                'type': 'text',
                'initial': 'm',
                'sufx': '',
                'required': False,
            },
        },
    }]

    handler = QFieldHandler('x', schema, 'cid', [{'type': 'c'}], {}, {})
    field = handler.formfields['qty']

    assert field.help_text == 'Enter a quantity'


def test_rchoice_field_without_explicit_choices():
    schema = [
        {
            'name': 'option',
            'type': 'rchoice',
            'choices': ['Fastest and ok: FSRCNN-small', 'Fast and accurate: FSRCNN'],
            'initial': 'Fast and accurate: FSRCNN',
        },
        {
            'name': 'scale',
            'type': 'rchoice',
            'initial': '2',
        },
    ]

    handler = QFieldHandler('image_upscale', schema, 'cid', [{'type': 's'}, {'type': 's'}], {}, {})
    assert 'option' in handler.formfields
    assert 'scale' in handler.formfields
    assert handler.formfields['scale'].choices == [('2', '2')]


def test_qty_widget_reads_exact_child_names_with_double_underscore():
    widgets = {
        '': forms.TextInput(),
        'part_uom': forms.TextInput(),
        '2_part': forms.TextInput(),
        '2_part_uom': forms.TextInput(),
    }
    fnames = [
        'qtc_input',
        'qtc_input_part_uom',
        f'qtc_input{TOK_INDEX_SEP}2_part',
        f'qtc_input{TOK_INDEX_SEP}2_part_uom',
    ]
    widget = QtyWidget(widgets, fnames, [None, None, None, None])

    posted = {
        'qtc_input': '2',
        'qtc_input_part_uom': 'ft',
        f'qtc_input{TOK_INDEX_SEP}2_part': '3',
        f'qtc_input{TOK_INDEX_SEP}2_part_uom': 'inch',
        # legacy-style keys that must not be used by QtyWidget extraction
        'qtc_input_2_part': 'WRONG',
        'qtc_input_2_part_uom': 'WRONG',
    }

    values = widget.value_from_datadict(posted, {}, 'qtc_input')

    assert values == ['2', 'ft', '3', 'inch']
