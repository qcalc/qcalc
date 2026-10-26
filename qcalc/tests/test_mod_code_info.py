import pytest

from qutil.mod_code_info import build_info

SOP_SIGNATURE = """
def optima_sop(
    sop_product_master: qtable,
    sop_demand: qtable,
    objective,
    qty_type,
    backlog_policy='allow',
    max_backlog_pct=25.0,
    stability_enabled=False,
    stability_penalty=0.0,
    max_change_pct=0.0,
    sop_previous_plan: qtable = None,
    enable_scenarios=None,
    scenarios_enabled=False,
    sop_scenarios: qtable = None,
    show_zero=False,
    bom_enabled=False,
    sop_material_requirements: qtable = None,
    procurement_enabled=False,
    supplier_master: qtable = None,
    procurement_max_suppliers=0,
    procurement_budget_limit=None,
):
"""

SOP_HELPERS = {
    'table_sop_product_master', 'table_sop_demand', 'table_sop_previous_plan', 'table_sop_scenarios',
    'table_sop_material_requirements', 'table_supplier_master',
}


def _tabs(result):
    return {t['title']: t['fields'] for t in result.spec['input_blocks'][0]['tabs']}


def test_defaults_are_not_repeated_in_schema():
    result = build_info('def calc(x=1.5, n=3, flag=True, name="a"):')

    assert result.func_name == 'calc'
    assert 'schema' not in result.spec  # qcalc derives type and initial from the defaults
    assert 'input_blocks' not in result.spec


def test_explicit_defaults_hint_writes_type_and_initial():
    result = build_info('def calc(x=1.5, n=3, flag=True, name="a"):', hints={'explicit_defaults': True})
    schema = result.spec['schema']

    assert schema['x'] == {'type': 'float', 'initial': 1.5}
    assert schema['n'] == {'type': 'integer', 'initial': 3}
    assert schema['flag'] == {'type': 'checkbox', 'initial': True}
    assert 'name' not in schema


def test_arguments_without_a_default_get_type_and_initial():
    result = build_info('def calc(use_extra, rate_pct, cap=None, label=None, plain=None):')
    schema = result.spec['schema']

    assert schema['use_extra'] == {'type': 'checkbox', 'initial': False}
    assert schema['rate_pct'] == {'type': 'float', 'initial': 0.0}
    assert 'cap' not in schema  # None default with a neutral name: nothing to add
    assert 'plain' not in schema


def test_initial_override_is_ignored_when_signature_has_default():
    overrides = {'x': {'initial': 9.0}, 'y': {'initial': 7.0, 'type': 'float'}}
    result = build_info('def calc(x=1.0, y=None):', overrides=overrides)

    assert 'x' not in result.spec.get('schema', {})
    assert result.spec['schema']['y'] == {'type': 'float', 'initial': 7.0}
    assert any(w.startswith('x: initial override ignored') for w in result.warnings)


@pytest.mark.parametrize('source', [
    'def calc(x, use_extra)',
    'def calc(x, use_extra):',
    'calc(x, use_extra)',
    'calc(x, use_extra):',
    'async def calc(x, use_extra) -> dict',
    'def calc(\n    x,\n    use_extra,\n)',
    'calc(x, use_extra)\n',
    'def calc(x, use_extra):\n    return g(x)',
])
def test_signature_spellings_are_accepted(source):
    result = build_info(source)

    assert result.func_name == 'calc'
    assert result.spec['schema']['use_extra'] == {'type': 'checkbox', 'initial': False}


def test_bare_argument_list_is_accepted():
    result = build_info('x, y=2.0', hints={'func_name': 'my_calc', 'explicit_defaults': True})

    assert result.func_name == 'my_calc'
    assert result.spec['schema']['y']['initial'] == 2.0


def test_annotated_and_hidden_arguments():
    result = build_info('def calc(code: qcode = "x", __info: qhide = None, f: qfunc = None, rate: qfl = 2.0):')

    assert 'code' not in result.spec.get('schema', {})
    assert '__info' not in result.spec.get('schema', {})
    assert 'f' not in result.spec.get('schema', {})


def test_toggle_groups_become_tabs_and_showhide():
    result = build_info(SOP_SIGNATURE, hints={'proper': 'BOM'}, table_helpers=SOP_HELPERS)
    tabs = _tabs(result)
    showhide = result.spec['showhide']

    assert tabs['Product Master'] == ['sop_product_master']
    assert tabs['Demand'] == ['sop_demand']
    assert tabs['Stability'] == ['stability_penalty', 'max_change_pct', 'sop_previous_plan']
    assert tabs['Scenarios'] == ['sop_scenarios']
    assert tabs['BOM'] == ['sop_material_requirements']
    assert tabs['Procurement'] == ['supplier_master', 'procurement_max_suppliers', 'procurement_budget_limit']
    assert 'show_zero' in tabs['Settings']
    assert 'enable_scenarios' in tabs['Settings']  # secondary toggle stays in Settings
    assert showhide['stability_enabled']['fields'] == tabs['Stability']
    assert showhide['scenarios_enabled']['callback'] == '@'
    assert 'script' not in result.spec
    assert 'enable_scenarios' not in showhide


def test_table_helpers_are_matched_by_argument_name():
    result = build_info(SOP_SIGNATURE, table_helpers=SOP_HELPERS)

    assert result.spec['schema']['sop_demand'] == "table_sop_demand('sop_demand')"
    assert 'from calc import' in result.code.splitlines()[0]

    without = build_info(SOP_SIGNATURE)
    assert 'sop_demand' not in without.spec['schema']
    assert any('table_sop_demand' in w for w in without.warnings)


def test_choices_are_inferred_from_body_comparisons():
    source = (
        "def calc(policy='allow', calc_mode=None):\n"
        "    if policy == 'cap':\n"
        "        pass\n"
        "    elif str(policy).strip().lower() in ('allow', 'disallow'):\n"
        "        pass\n"
        "    return {'result': 1}\n"
    )
    result = build_info(source)
    entry = result.spec['schema']['policy']

    assert entry['type'] == 'choice'
    assert list(entry['choices']) == ['cap', 'allow', 'disallow']
    assert 'initial' not in entry  # the signature default 'allow' already provides it
    assert any('policy' in w and 'inferred' in w for w in result.warnings)
    assert any('calc_mode' in w for w in result.warnings)


def test_choices_scan_can_be_disabled():
    source = (
        "def calc(policy='allow'):\n"
        "    return policy == 'a' or policy == 'b'\n"
    )

    assert 'policy' not in build_info(source, hints={'scan_body': False}).spec.get('schema', {})


def test_overrides_win_and_accept_table_rows():
    rows = [
        {'Argument': 'objective', 'Choices': 'cost=Minimize Cost, service', 'Help': 'Main goal', 'Label': 'Goal'},
        {'Argument': 'floor_pct', 'Show When': 'objective == cost', 'Group': 'Targets'},
        {'Argument': 'ghost', 'Help': 'unused'},
        {'Argument': 'objective', 'Label': float('nan')},
    ]
    result = build_info('def calc(objective, floor_pct=0.0):', overrides=rows)
    schema = result.spec['schema']

    assert schema['objective']['choices'] == {'cost': 'Minimize Cost', 'service': 'Service'}
    assert schema['objective']['initial'] == 'cost'
    assert schema['objective']['help_text'] == 'Main goal'
    assert schema['objective']['label'] == 'Goal'
    assert any('ghost' in w for w in result.warnings)
    assert result.spec['showhide']['objective'] == {'fields': ['floor_pct'], 'callback': "@==='cost'"}
    assert 'script' not in result.spec
    assert 'Targets' in _tabs(result)


def test_show_when_variants_and_errors():
    overrides = {
        'a': {'show_when': 'mode in x, y'},
        'b': {'show_when': 'nonsense'},
        'c': {'show_when': 'ghost == 1'},
    }
    result = build_info('def calc(mode="x", a=1.0, b=1.0, c=1.0):', overrides=overrides)

    assert result.spec['showhide']['mode'] == {'fields': ['a'], 'callback': "['x', 'y'].indexOf(@) >= 0"}
    assert len(result.warnings) == 2


def test_show_when_rule_forms():
    overrides = {
        'p': {'show_when': 'mode != x'},
        'q': {'show_when': 'mode not in a, b'},
        'r': {'show_when': 'flag == true'},
        's': {'show_when': 'flag == false'},
        't': {'show_when': "name == O'Neil"},
        'u': {'show_when': 'mode == a@b'},
    }
    result = build_info('def calc(mode="x", flag=False, name="", p=1.0, q=1.0, r=1.0, s=1.0, t=1.0, u=1.0):',
                        overrides=overrides)
    showhide = result.spec['showhide']

    assert showhide['mode']['fields'] == ['p', 'q']
    assert showhide['mode']['callback'] == "[@!=='x', ['a', 'b'].indexOf(@) < 0]"
    assert showhide['flag'] == {'fields': ['r', 's'], 'callback': '[@, !@]'}
    assert showhide['name']['callback'] == "@==='O\\'Neil'"
    assert any("cannot contain '@'" in w for w in result.warnings)


def test_rules_and_toggle_groups_share_one_controller():
    overrides = {'extra_note': {'show_when': 'use_extra == false'}}
    result = build_info('def calc(use_extra=False, extra_cost=1.0, extra_note="", extra_rate=1.0):',
                        overrides=overrides)

    assert result.spec['showhide']['use_extra'] == {
        'fields': ['extra_note', 'extra_cost', 'extra_rate'],
        'callback': '[!@, @, @]',
    }


def test_docstring_gives_description_and_help():
    source = (
        "def calc(x=1.0, y=2.0):\n"
        "    '''Add two numbers.\n\n"
        "    Args:\n"
        "        x: first value\n"
        "        y (float): second value\n"
        "    '''\n"
        "    return x + y\n"
    )
    result = build_info(source)

    assert result.spec['desc'] == 'Add two numbers.'
    assert result.spec['schema']['x']['help_text'] == 'first value'
    assert result.spec['schema']['y']['help_text'] == 'second value'


def test_outputs_are_scanned_from_returned_dict_only_in_own_body():
    source = (
        "def calc(x=1.0):\n"
        "    def inner():\n"
        "        return {'hidden': 1}\n"
        "    out = {'A One': 1}\n"
        "    out['B Two'] = 2\n"
        "    out['C Three'] = 3\n"
        "    out['D Four'] = 4\n"
        "    return out\n"
    )
    result = build_info(source)
    tabs = result.spec['output_blocks'][0]['tabs']

    assert [t['title'] for t in tabs] == ['A One', 'B Two', 'C Three', 'D Four']
    assert 'hidden' not in str(tabs)


def test_output_hint_groups_by_first_word():
    hints = {'outputs': 'Summary, Procurement Summary, Procurement Detail, Chart'}
    result = build_info('def calc(x=1.0):', hints=hints)
    titles = [t['title'] for t in result.spec['output_blocks'][0]['tabs']]

    assert titles == ['Summary', 'Procurement', 'Chart']


def test_titles_use_qcalc_title_casing_and_proper_words():
    source = "def sop_plan(kpi_view='x', price_per_unit_enabled=False, price_per_unit_cap=1.0):"
    result = build_info(source, hints={'proper': 'SOP, qCalc'})
    plain = build_info(source)

    assert result.spec['title'] == 'SOP Plan'
    assert result.spec['proper'] == 'SOP, qCalc'
    assert 'Price per Unit' in _tabs(result)  # small words stay lower case like qcalc's variable_to_title
    assert plain.spec['title'] == 'Sop Plan'
    assert 'proper' not in plain.spec


def test_public_key_hints_and_ordering():
    hints = {
        'calculate': 'Solve', 'layout': 'lr', 'interactive': True, 'remember': False, 'table_out_all': 'yes',
        'kins': 'eva, mycal', 'tags': 'a,  b,, c', 'proper': 'SOP', 'onsubmit': 'alert(1)',
        'images': {'top': 'a.png, b.png', 'bottom': ''},
    }
    result = build_info('def calc(x=1.0)', hints=hints)

    assert list(result.spec) == [
        'title', 'calculate', 'layout', 'interactive', 'images', 'onsubmit', 'kins', 'tags', 'proper',
        'remember', 'table_out_all',
    ]
    assert result.spec['tags'] == 'a, b, c'
    assert result.spec['images'] == {'top': ['a.png', 'b.png']}
    assert result.spec['table_out_all'] is True and result.spec['remember'] is False


def test_remember_true_and_missing_flags_write_nothing():
    spec = build_info('def calc(x=1.0)', hints={'remember': True, 'interactive': False}).spec

    assert not {'remember', 'interactive', 'table_out_all'} & set(spec)


def test_invalid_layout_is_ignored_with_a_note():
    result = build_info('def calc(x=1.0)', hints={'layout': 'diagonal'})

    assert 'layout' not in result.spec
    assert any('layout' in w for w in result.warnings)


def test_multiline_script_is_a_triple_quoted_block():
    script = 'function f(v){\n    return v;\n}\nfunction g(v){\n    return !v;\n}'
    result = build_info('def calc(x=1.0)', hints={'script': script})
    namespace = {}

    assert "'script': \"\"\"" in result.code
    exec(result.code, namespace)
    assert namespace['calc__info']()['script'].split() == script.split()


def test_anyof_groups_are_validated():
    result = build_info('def calc(a=1.0, b=1.0, c=1.0)', hints={'anyof': 'a, b\na, ghost\nc'})

    assert result.spec['anyof'] == {'1': {'fields': ['a', 'b']}}
    assert any("'ghost'" in w for w in result.warnings)
    assert any('at least two' in w for w in result.warnings)


def test_extra_keys_accept_public_keys_only():
    extra = "{'step2': [{'step': 'run'}], 'single_instance': True, 'row': ['x-y'], 'inp1': 0.5, 'xpr': 1, 'foo': 2}"
    result = build_info('def calc(x=1.0)', hints={'extra': extra})

    assert result.spec['step2'] == [{'step': 'run'}] and result.spec['single_instance'] is True
    assert not {'row', 'inp1', 'xpr', 'foo'} & set(result.spec)
    assert sum('legacy' in w for w in result.warnings) == 2
    assert any("'xpr'" in w and 'itself' in w for w in result.warnings)
    assert any("'foo'" in w for w in result.warnings)


def test_extra_must_be_a_dict_literal():
    for bad in ('step2 = 1', '[1, 2]', '{"a": undefined_name}'):
        result = build_info('def calc(x=1.0)', hints={'extra': bad})

        assert any(w.startswith('extra:') for w in result.warnings)
        assert 'a' not in result.spec


def test_extra_overrides_generated_keys():
    result = build_info('def calc(x=1.0)', hints={'tags': 'a', 'extra': "{'tags': 'b, c'}"})

    assert result.spec['tags'] == 'b, c'


def test_extra_dicts_are_merged_into_generated_ones():
    # the '__' showhide key (always hidden fields) as used by the demo calculators
    source = 'def calc(use_extra=False, extra_cost=1.0, secret=1.0, note="")'
    extra = "{'showhide': {'__': {'fields': ['secret']}}, 'schema': {'note': {'help_text': 'A note'}}}"
    result = build_info(source, hints={'extra': extra})

    assert list(result.spec['showhide']) == ['use_extra', '__']
    assert result.spec['showhide']['__'] == {'fields': ['secret']}
    assert result.spec['schema']['note'] == {'help_text': 'A note'}


def test_blank_markers_in_override_cells_and_flag_strings_follow_the_shared_helpers():
    result = build_info(
        'def calc(x=1.0)',
        overrides=[{'arg': 'x', 'help': 'nan', 'label': 'None', 'group': 'null'}],
        hints={'table_out_all': 'no', 'interactive': 'yes', 'tags': 'NA'},
    )

    assert 'schema' not in result.spec and 'input_blocks' not in result.spec
    assert 'table_out_all' not in result.spec and result.spec['interactive'] is True
    assert 'tags' not in result.spec  # a blank marker is not a tag, and no tags are generated


def test_no_tags_are_generated_by_default():
    spec = build_info('def sop_plan(use_extra=False, extra_cost=1.0)').spec

    assert 'tags' not in spec


def test_function_selection_rules():
    module = "def helper(a):\n    return a\n\ndef main(x=1.0):\n    return helper(x)\n\ndef main__info():\n    return {}\n"

    assert build_info(module).func_name == 'main'
    assert build_info(module, hints={'func_name': 'helper'}).func_name == 'helper'
    with pytest.raises(ValueError, match='Cannot determine'):
        build_info('def a(x):\n    return x\n\ndef b(y):\n    return y\n')
    with pytest.raises(ValueError, match='not defined'):
        build_info(module, hints={'func_name': 'missing'})


def test_unparseable_source_is_rejected():
    with pytest.raises(ValueError, match='Cannot parse'):
        build_info('def (:')


def test_generated_code_executes_and_matches_spec():
    result = build_info(SOP_SIGNATURE, table_helpers=SOP_HELPERS)
    namespace = {name: (lambda field_name, _n=name: {'initial': _n}) for name in SOP_HELPERS}

    exec(result.code, namespace)
    info = namespace['optima_sop__info']()

    assert info['title'] == result.spec['title']
    assert info['input_blocks'] == result.spec['input_blocks']
    assert info['showhide'] == result.spec['showhide']
    assert info['schema']['sop_demand'] == {'initial': 'table_sop_demand'}
