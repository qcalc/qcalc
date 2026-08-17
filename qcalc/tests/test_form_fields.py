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

    handler = QFieldHandler('x', schema, 'cid', [{'type': 'c'}], {})
    field = handler.formfields['qty']

    assert field.help_text == 'Enter a quantity'
