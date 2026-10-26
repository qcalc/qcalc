from django import forms

from qconst import TOK_INDEX_SEP
from qcore.mod_anno import qcode, qhtml
from qcore.mod_qjfield import QJField
from qcore.mod_qforms import QFieldHandler
from qcore.mod_qwidgets import CodeWidget_codemirror, QtyWidget


def test_qhtml_value_creates_display_only_html_field():
    field = QJField('note', arg_value=qhtml('<p>Between fields</p>'))

    assert field.jf['type'] == 'html'
    assert field.jf['initial'] == '<p>Between fields</p>'
    assert field.s2f == {'type': 'x'}


def test_qhtml_annotation_creates_display_only_html_field():
    field = QJField('note', arg_type=qhtml, arg_value='<p>Between fields</p>')

    assert field.jf['type'] == 'html'
    assert field.s2f == {'type': 'x'}


def test_html_field_ignores_posted_data_and_keeps_initial_html():
    schema = [{
        'name': 'note',
        'type': 'html',
        'initial': '<p>Between fields</p>',
        'required': False,
    }]
    handler = QFieldHandler('x', schema, 'cid', [{'type': 'x'}], {}, {})
    form_class = type('DynaForm', (forms.Form,), handler.formfields)
    form = form_class({'note': 'posted value'})

    assert form.is_valid()
    assert form.cleaned_data['note'] == '<p>Between fields</p>'
    assert '<p>Between fields</p>' in str(form['note'])
    assert 'posted value' not in str(form['note'])


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


def _code_field_html(**schema_overrides):
    qjf = QJField('markdown_text', qcode, 'x', 'id_c_', False, '')
    meta = {**qjf.jf, **schema_overrides}  # what the schema entry of __info() adds on top of the field
    handler = QFieldHandler('x', [meta], 'c', [qjf.s2f], {}, {})
    form = type('DynaForm', (forms.Form,), handler.formfields)()
    return form['markdown_text']


def test_code_field_is_required_by_default():
    bound = _code_field_html()

    assert bound.field.required
    assert ' required' in str(bound)


def test_code_field_schema_can_make_it_optional():
    bound = _code_field_html(required=False)

    assert not bound.field.required
    assert ' required' not in str(bound)


def test_code_field_stays_required_through_qjfield():
    assert QJField('code', qcode, '', 'id_c_', False, '').jf['required'] is True
    assert QJField('code', 'codeedit', '', 'id_c_', False, '').jf['required'] is True


def test_code_field_uses_standard_field_options():
    bound = _code_field_html(help_text='Some help', disabled=True)

    assert bound.label == 'Markdown Text'
    assert bound.help_text == 'Some help'
    assert bound.field.disabled


def test_code_widget_loads_find_and_replace_assets():
    media = CodeWidget_codemirror(id_='id_code').media

    assert any(path.endswith('/dialog.min.css') for path in media._css['all'])
    assert any(path.endswith('/dialog.min.js') for path in media._js)
    assert any(path.endswith('/searchcursor.min.js') for path in media._js)
    assert any(path.endswith('/search.min.js') for path in media._js)


def test_code_widget_renders_find_and_replace_actions():
    html = str(CodeWidget_codemirror(id_='id_code').render('code', 'print("hello")'))

    assert "codeMirrorWidgetMenuAction('id_code', 'find')" in html
    assert "codeMirrorWidgetMenuAction('id_code', 'replace')" in html
    assert '>Find (Ctrl+F)<' in html
    assert '>Replace (Ctrl+Shift+F)<' in html
