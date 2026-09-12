from qcore.mod_qforms import QFieldHandler


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
