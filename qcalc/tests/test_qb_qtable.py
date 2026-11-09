# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha
# Tests generated with AI assistance. Reviewed and validated by the author.

import inspect

import pandas as pd
import pytest
import qconst
from qcore import to_cast, QTable
from qcore.qb_qtable import _looks_like_alias
from qutil.mod_code_security import UnsafeCodeError, dangerous_attributes, validate_expression_security
from calc import QThread


def _df_table(df, name):
    return QTable(df, name=name)


def test_assert_columns_renames_dataframe_columns_case_insensitive():
    df = pd.DataFrame({' source ': ['P1'], 'CAPACITY': [10]})

    table = _df_table(df, 'supply')
    table.assert_columns(['Source', 'Capacity'])
    df.columns = table.columns

    assert list(df.columns) == ['Source', 'Capacity']


def test_assert_columns_renames_qtbl_columns_case_insensitive():
    table = {
        'columns': [' source ', 'CAPACITY'],
        'data': [['P1', 10]],
    }

    qt = QTable(table, name='supply')
    qt.assert_columns(['Source', 'Capacity'])
    table['columns'] = qt.columns

    assert table['columns'] == ['Source', 'Capacity']


def test_assert_columns_is_always_case_insensitive_even_when_values_are_case_sensitive():
    df = pd.DataFrame({'SOURCE': ['P1'], 'Capacity': [10]})

    table = QTable(df, name='supply', case_sensitive=True)
    resolved = table.assert_columns(['Source', 'Capacity'])

    assert resolved == {'Source': 'Source', 'Capacity': 'Capacity'}
    assert table.columns == ['Source', 'Capacity']


def test_assert_columns_rejects_headers_differing_only_by_case():
    df = pd.DataFrame({'ID': [1], 'id': [2]})

    with pytest.raises(Exception, match='Ambiguous column names'):
        QTable(df, name='t', case_sensitive=True).assert_columns(['id'])


def test_case_sensitive_property_controls_value_comparison():
    df = pd.DataFrame({'Project': ['P1', 'p1']})

    with pytest.raises(Exception, match='duplicate'):
        QTable(df, name='projects').assert_unique('Project')

    assert QTable(df, name='projects', case_sensitive=True).assert_unique('Project') == ['P1', 'p1']


def test_case_sensitive_foreign_key_rejects_case_mismatch():
    child = pd.DataFrame({'Source': ['p1']})
    parent = pd.DataFrame({'Source': ['P1']})

    QTable(child, name='child').assert_foreign_key(QTable(parent, name='parent'), 'Source', 'Source')
    with pytest.raises(Exception, match='not found'):
        QTable(child, name='child', case_sensitive=True).assert_foreign_key(
            QTable(parent, name='parent'), 'Source', 'Source')


def test_assert_foreign_key_is_case_insensitive():
    child = pd.DataFrame({'Source': ['p1', 'P2']})
    parent = pd.DataFrame({'source': ['P1', 'p2']})

    child_qt = _df_table(child, 'child')
    parent_qt = _df_table(parent, 'parent')
    child_qt.assert_foreign_key(parent_qt, 'Source', 'Source')


def test_assert_columns_match_domain_renames_and_returns_values():
    cost = pd.DataFrame({
        'location': ['L1', 'L2'],
        'demand': [10, 20],
        'bo': [1, 2],
        'Na': [3, 4],
    })
    facility = pd.DataFrame({
        'Location': ['BO', 'NA'],
        'Capacity': [100, 100],
        'Fixed Cost': [1, 1],
    })

    cost_qt = _df_table(cost, 'cost')
    facility_qt = _df_table(facility, 'facility')
    result = cost_qt.assert_columns_match_domain(
        master=facility_qt,
        master_value_col='Location',
        matrix_reserved_cols=['Location', 'Demand'],
    )
    cost.columns = cost_qt.columns

    assert 'BO' in cost.columns and 'NA' in cost.columns
    assert result['master_values'] == ['BO', 'NA']


def test_assert_columns_match_domain_can_be_one_way_only():
    cost = pd.DataFrame({
        'Location': ['L1'],
        'Demand': [10],
        'BO': [1],
        'NA': [2],
        'EXTRA': [3],
    })
    facility = pd.DataFrame({'Location': ['BO', 'NA']})

    cost_qt = _df_table(cost, 'cost')
    facility_qt = _df_table(facility, 'facility')
    cost_qt.assert_columns_match_domain(
        master=facility_qt,
        master_value_col='Location',
        matrix_reserved_cols=['Location', 'Demand'],
        require_master_in_matrix=True,
        require_matrix_in_master=False,
    )


def test_assert_unique_raises_on_duplicate():
    projects = pd.DataFrame({'Project': ['P1', 'p1']})

    with pytest.raises(Exception, match='duplicate'):
        _df_table(projects, 'projects').assert_unique('Project')


def test_assert_unique_pairs_raises_on_duplicate_pair():
    pair_table = pd.DataFrame({
        'Source': ['S1', 'S1'],
        'Destination': ['D1', 'd1'],
    })

    with pytest.raises(Exception, match='duplicate pair'):
        _df_table(pair_table, 'ship_cost').assert_unique_pairs('Source', 'Destination')


def test_assert_complete_cross_join_raises_on_missing_pair():
    ship_cost = pd.DataFrame({
        'Source': ['S1', 'S1', 'S2'],
        'Destination': ['D1', 'D2', 'D1'],
    })

    with pytest.raises(Exception, match='missing Source-Destination pair'):
        _df_table(ship_cost, 'ship_cost').assert_complete_cross_join(
            left_col='Source',
            right_col='Destination',
            left_values=['S1', 'S2'],
            right_values=['D1', 'D2'],
            left_label='Source',
            right_label='Destination',
        )


def test_to_cast_behaves_for_blank_valid_and_invalid():
    assert to_cast('', 'budget_limit', float) is None
    assert to_cast(None, 'budget_limit', float) is None
    assert to_cast('12.5', 'budget_limit', float) == 12.5
    assert to_cast('7', 'max_selected', int) == 7

    with pytest.raises(Exception, match='Invalid numeric value'):
        to_cast('x7', 'max_selected', int)


def test_assert_columns_strict_table_input_raises_for_suspicious_optional_alias():
    QThread.set_pref({'strict_table_input': True})
    df = pd.DataFrame({
        'Material': ['A'],
        'Unit Cost': [1.0],
        'Minimum Quantity': [0],
    })

    with pytest.raises(Exception, match='suspicious column name'):
        _df_table(df, 'blend_materials').assert_columns(['Material', 'Unit Cost'], optional_cols=['Min Qty', 'Max Qty'])


def test_assert_columns_non_strict_allows_suspicious_optional_alias():
    QThread.set_pref({'strict_table_input': False})
    df = pd.DataFrame({
        'Material': ['A'],
        'Unit Cost': [1.0],
        'Minimum Quantity': [0],
    })

    _df_table(df, 'blend_materials').assert_columns(['Material', 'Unit Cost'], optional_cols=['Min Qty', 'Max Qty'])


def test_assert_columns_strict_rejects_unexpected_columns_for_fixed_schema():
    QThread.set_pref({'strict_table_input': True})
    df = pd.DataFrame({
        'Location': ['BO'],
        'Capacity': [100],
        'Unexpected': [1],
    })

    with pytest.raises(Exception, match='unexpected column'):
        _df_table(df, 'facility').assert_columns(
            ['Location', 'Capacity'],
            columns_can_grow=False,
        )


def test_assert_columns_strict_allows_unexpected_columns_for_open_schema():
    QThread.set_pref({'strict_table_input': True})
    df = pd.DataFrame({
        'Location': ['L1'],
        'Demand': [10],
        'BO': [1],
        'NA': [2],
        'CustomDynamic': [3],
    })

    _df_table(df, 'cost').assert_columns(
        ['Location', 'Demand'],
        columns_can_grow=True,
    )


def test_assert_columns_rejects_header_unit_without_required_col_uoms():
    df = pd.DataFrame({
        'Capacity | unit/mo': [100],
        'Location': ['L1'],
    })

    with pytest.raises(Exception, match=f"{qconst.TBL_UOM_SEP}"):
        _df_table(df, 'facility').assert_columns(['Location', 'Capacity'])


def test_assert_columns_validates_header_unit_compatibility_and_trims_spaces():
    df = pd.DataFrame({
        'Machine Time   |   min/unit': [5],
        'Product': ['A'],
    })

    table = _df_table(df, 'products')
    resolved = table.assert_columns(
        ['Product', 'Machine Time'],
        required_col_uoms={'Machine Time': 'hr/unit'},
    )
    df.columns = table.columns

    assert resolved['Machine Time'] == 'Machine Time | min/unit'
    assert list(df.columns) == ['Machine Time | min/unit', 'Product']


def test_assert_columns_rejects_header_unit_for_unknown_base_column_mapping():
    df = pd.DataFrame({
        'Custom Metric | hr/mo': [1],
        'Product': ['A'],
    })

    with pytest.raises(Exception, match='does not allow units'):
        _df_table(df, 'products').assert_columns(
            ['Product'],
            required_col_uoms={'Machine Time': 'hr/unit'},
        )


def test_assert_columns_qtbl_validates_and_normalizes_header_uom_spacing():
    table = {
        'columns': ['Product', 'Machine Time   |   min/unit'],
        'data': [['A', 5]],
    }

    qt = QTable(table, name='products')
    resolved = qt.assert_columns(
        ['Product', 'Machine Time'],
        required_col_uoms={'Machine Time': 'hr/unit'},
    )
    table['columns'] = qt.columns

    assert resolved['Machine Time'] == 'Machine Time | min/unit'
    assert table['columns'] == ['Product', 'Machine Time | min/unit']


def _employees():
    return QTable(pd.DataFrame({
        'Name': ['Ann', 'Bob', 'Cy', 'Dee'],
        'Dept': ['Sales', 'IT', 'IT', 'HR'],
        'Salary': [50, 70, 65, 55],
    }), name='employees')


def test_select_subset_of_columns_in_requested_order():
    # SELECT Salary, Name FROM employees
    rows = _employees().select(['Salary', 'Name'])

    assert rows == [
        {'Salary': 50, 'Name': 'Ann'},
        {'Salary': 70, 'Name': 'Bob'},
        {'Salary': 65, 'Name': 'Cy'},
        {'Salary': 55, 'Name': 'Dee'},
    ]


def test_select_unknown_column_raises():
    with pytest.raises(KeyError, match='Unknown column'):
        _employees().select(['Name', 'Missing'])


def test_where_equality_filters_rows():
    # SELECT * FROM employees WHERE Dept = 'IT'
    rows = _employees().select(Dept='IT')

    assert [r['Name'] for r in rows] == ['Bob', 'Cy']
    assert all(set(r) == {'Name', 'Dept', 'Salary'} for r in rows)


def test_where_with_multiple_criteria_is_and():
    # WHERE Dept = 'IT' AND Salary = 65
    assert _employees().select(Dept='IT', Salary=65) == [{'Name': 'Cy', 'Dept': 'IT', 'Salary': 65}]
    assert _employees().select(Dept='HR', Salary=65) == []


def test_where_unknown_column_raises():
    with pytest.raises(KeyError, match='Unknown column'):
        _employees().select(Missing=1)


def test_select_columns_with_where_condition():
    # SELECT Name, Salary FROM employees WHERE Dept = 'IT'
    selected = _employees().select(['Name', 'Salary'], Dept='IT')

    assert selected == [{'Name': 'Bob', 'Salary': 70}, {'Name': 'Cy', 'Salary': 65}]


def test_select_columns_with_range_where_condition():
    # SELECT Name FROM employees WHERE Salary >= 60 (non-equality predicate)
    names = _employees().select(['Name'], where=lambda r: r['Salary'] >= 60)

    assert names == [{'Name': 'Bob'}, {'Name': 'Cy'}]


def test_select_where_can_use_unselected_columns_and_combine_with_criteria():
    # SELECT Name FROM employees WHERE Dept = 'IT' AND Salary > 65
    rows = _employees().select(['Name'], where=lambda r: r['Salary'] > 65, Dept='IT')

    assert rows == [{'Name': 'Bob'}]


def test_select_without_arguments_returns_all_rows_and_columns():
    table = _employees()

    assert table.select() == list(table)
    assert table.select()[0] == {'Name': 'Ann', 'Dept': 'Sales', 'Salary': 50}


def test_select_skips_blank_and_header_rows_unless_disabled():
    table = QTable({'columns': ['Name', 'Dept'],
                    'data': [['Name', 'Dept'], [' Ann ', 'IT'], ['', None]]}, name='t', validate=False)

    assert table.select() == [{'Name': 'Ann', 'Dept': 'IT'}]
    assert len(table.select(skip_blank=False, skip_header=False, strip=False)) == 3
    assert table.select(['Name'], Dept='IT') == [{'Name': 'Ann'}]


def test_find_returns_first_raw_record_or_none():
    table = _employees()

    assert table.find(Dept='IT') == {'Name': 'Bob', 'Dept': 'IT', 'Salary': 70}
    assert table.find(Dept='Finance') is None
    with pytest.raises(KeyError, match='Unknown column'):
        table.find(Missing=1)


def test_select_with_no_matching_rows_returns_empty_list():
    assert _employees().select(['Name'], Dept='Finance') == []


def test_select_unknown_column_or_criteria_raises():
    with pytest.raises(KeyError, match='Unknown column'):
        _employees().select(['Missing'])
    with pytest.raises(KeyError, match='Unknown column'):
        _employees().select(['Name'], Missing=1)


def test_select_where_does_not_modify_table():
    table = _employees()
    table.select(Dept='IT')
    table.select(['Name'], where=lambda r: True)

    assert table.shape == (4, 3)
    assert table.columns == ['Name', 'Dept', 'Salary']



@pytest.mark.parametrize('candidate, expected, result', [
    ('Minimum Quantity', 'Min Qty', True),
    ('Max Order Qty', 'Max Qty', True),
    ('Min Quantity Required', 'Min Qty', True),
    ('min qty', ' Min Qty ', False),
    ('Notes', 'Min Qty', False),
    ('Cost', 'A', False),
    ('', 'Min Qty', False),
])
def test_looks_like_alias_flags_near_miss_names_only(candidate, expected, result):
    assert _looks_like_alias(candidate, expected) is result


def test_schema_strips_text_columns_by_default_and_can_opt_out():
    table = QTable(
        {'columns': ['Name', 'Note', 'Qty'], 'data': [[' Ann ', ' keep ', ' 5 ']]},
        schema={'Name': str, 'Note': {'type': str, 'strip': False}, 'Qty': {'cast': float}},
    )
    table.validate(raise_exception=True)

    assert table.row(0) == ['Ann', ' keep ', 5.0]


def test_to_df_returns_a_detached_dataframe_with_current_headers():
    table = QTable({'columns': [' id ', 'Name'], 'data': [[1, 'A']]}, name='t')
    table.assert_columns(['ID', 'Name'])

    df = table.to_df()
    df.loc[0, 'Name'] = 'changed'

    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == ['ID', 'Name']
    assert table.row(0) == [1, 'A']


def test_to_qdf_is_the_restricted_facade_not_a_dataframe():
    qdf_obj = QTable({'columns': ['a'], 'data': [[1]]}).to_qdf()

    assert not isinstance(qdf_obj, pd.DataFrame)


def test_user_code_cannot_call_to_df():
    with pytest.raises(UnsafeCodeError, match='to_df'):
        validate_expression_security("QTable({'columns': ['a'], 'data': [[1]]}).to_df()")
    validate_expression_security("QTable({'columns': ['a'], 'data': [[1]]}).to_qdf()")


def test_public_qtable_members_never_leak_pandas_objects_unless_blocklisted():
    table = QTable({'columns': ['a', 'b'], 'data': [[1, 2]]}, primary_key='a', name='t')
    leaks = []
    for name in dir(table):
        if name.startswith('_'):
            continue
        member = getattr(table, name)
        if callable(member):
            params = inspect.signature(member).parameters.values()
            if any(p.default is p.empty and p.kind in (p.POSITIONAL_OR_KEYWORD, p.POSITIONAL_ONLY) for p in params):
                continue
            member = member()
        if isinstance(member, (pd.DataFrame, pd.Series)) and name not in dangerous_attributes:
            leaks.append(name)

    assert leaks == []


def test_validate_matches_schema_headers_loosely_then_coerces_values():
    table = QTable(
        {'columns': [' plant ', 'CAPACITY '], 'data': [[' P1 ', '100']]},
        name='supply', schema={'Plant': str, 'Capacity': float}, validate=True,
    )

    assert table.columns == ['Plant', 'Capacity']
    assert table.to_map('Plant', 'Capacity') == {'P1': 100.0}


def test_validate_reports_missing_schema_column():
    with pytest.raises(ValueError, match='supply missing required column.*Capacity'):
        QTable({'columns': ['Plant'], 'data': [['P1']]}, name='supply',
               schema={'Plant': str, 'Capacity': float}, validate=True)


def test_validation_drops_spare_blank_rows_but_keeps_blank_cells():
    data = [['x', 1], ['', None], [None, ''], [' ', '  '], ['y', None]]

    table = QTable({'columns': ['a', 'b'], 'data': data}, name='t')
    assert table.column('a') == ['x', 'y']
    assert table.column('b') == [1, None]

    untouched = QTable({'columns': ['a', 'b'], 'data': data}, validate=False)
    assert untouched.nrows == 5


def test_schema_columns_are_required_unless_marked_optional():
    schema = {'a': str, 'b': {'type': float, 'required': False}}

    table = QTable({'columns': ['a', 'b'], 'data': [['P1', 5], ['', None], ['P2', None]]}, schema=schema)
    assert table.to_map('a', 'b') == {'P1': 5.0, 'P2': None}

    with pytest.raises(ValueError, match='row 2: t: a is required'):
        QTable({'columns': ['a', 'b'], 'data': [['P1', 5], ['', 7]]}, name='t', schema=schema)
    with pytest.raises(ValueError, match='row 1: t: b is required'):
        QTable({'columns': ['a', 'b'], 'data': [['P1', None]]}, name='t', schema={'a': str, 'b': float})


def test_schema_dict_reports_the_required_rule():
    table = QTable({'columns': ['a', 'b'], 'data': []},
                   schema={'a': str, 'b': {'type': float, 'required': False}})

    assert table.schema_dict() == {'a': {'type': 'string', 'required': True},
                                   'b': {'type': 'number', 'required': False}}


def test_validate_true_is_the_default_and_false_defers_checks():
    payload = {'columns': ['n'], 'data': [['abc']]}

    with pytest.raises(ValueError, match='invalid n'):
        QTable(payload, schema={'n': int})
    lenient = QTable(payload, schema={'n': int}, validate=False)
    assert lenient.validate()['valid'] is False


def test_assert_in_checks_values_against_allowed_list():
    table = QTable({'columns': ['From'], 'data': [['p1'], [' D1 '], ['']]}, name='cost')

    table.assert_in('from', ['P1', 'D1'])
    with pytest.raises(ValueError, match="cost 'From' has value\\(s\\) not found in nodes: D1"):
        table.assert_in('From', ['P1'], label='nodes')
    with pytest.raises(ValueError, match='not found'):
        QTable({'columns': ['From'], 'data': [['p1']]}, case_sensitive=True).assert_in('From', ['P1'])


def test_optional_schema_columns_may_be_absent_and_blank_numbers_become_none():
    schema = {'Product': str, 'Setup Cost': {'type': float, 'required': False}}

    without = QTable({'columns': ['Product'], 'data': [['A']]}, schema=schema)
    assert without.columns == ['Product']

    table = QTable({'columns': ['Product', ' setup cost '], 'data': [['A', 5], ['B', ''], ['C', None]]}, schema=schema)
    assert table.columns == ['Product', 'Setup Cost']
    assert table.to_map('Product', 'Setup Cost') == {'A': 5.0, 'B': None, 'C': None}


def test_schema_default_fills_blank_cells():
    table = QTable({'columns': ['n', 'k'], 'data': [['', 1], [None, 2], [3, 3]]},
                   schema={'n': {'type': float, 'default': 1.0}, 'k': int})

    assert table.column('n') == [1.0, 1.0, 3.0]


def test_nan_from_a_dataframe_counts_as_blank():
    df = pd.DataFrame({'a': ['x', 'y', None], 'n': [1.0, float('nan'), float('nan')]})

    with pytest.raises(ValueError, match='row 2: t: n is required'):
        QTable(df, name='t', schema={'a': str, 'n': float})
    assert QTable(df, schema={'a': str, 'n': {'type': float, 'required': False}}).nrows == 2


def test_sum_by_groups_and_totals_like_sql():
    table = QTable({'columns': ['Period', 'Product', 'Demand'],
                    'data': [[1, 'A', 5], [1, 'A', 7], [2, 'A', 1], [1, 'B', 2], ['', '', '']]},
                   schema={'Period': str, 'Product': str, 'Demand': float})

    assert table.sum_by(['Period', 'Product'], 'Demand') == {('1', 'A'): 12.0, ('2', 'A'): 1.0, ('1', 'B'): 2.0}
    assert table.sum_by('Product', 'Demand') == {'A': 13.0, 'B': 2.0}


def test_foreign_key_rewrites_child_values_to_the_parent_spelling():
    parent = QTable({'columns': ['Plant'], 'data': [['P1'], ['P2']]}, name='supply')
    child = QTable({'columns': ['Plant', 'Cost'], 'data': [['p1', 1], [' P2 ', 2], ['P1', 3]]}, name='cost')

    child.assert_foreign_key(parent, 'Plant', 'Plant')

    assert child.column('Plant') == ['P1', ' P2 ', 'P1']
    assert parent.column('Plant') == ['P1', 'P2']


def test_strict_mode_does_not_rewrite_and_reports_the_mismatch():
    parent = QTable({'columns': ['Plant'], 'data': [['P1']]}, name='supply')
    child = QTable({'columns': ['Plant'], 'data': [['p1']]}, name='cost', case_sensitive=True)

    with pytest.raises(ValueError, match="cost 'Plant' has value.*not found in supply 'Plant': p1"):
        child.assert_foreign_key(parent, 'Plant', 'Plant')
    assert child.column('Plant') == ['p1']


def test_assert_in_keeps_value_types_and_rejects_ambiguous_allowed_values():
    ids = QTable({'columns': ['id', 'tag'], 'data': [[1, 'a'], [2, 'B']]}, name='t')

    ids.assert_in('id', [1, 2, 3])
    ids.assert_in('tag', ['A', 'b'])
    assert ids.column('id') == [1, 2]
    assert ids.column('tag') == ['A', 'b']

    with pytest.raises(ValueError, match='ambiguous when case is ignored: A, a'):
        ids.assert_in('tag', ['A', 'a'])


def test_cross_join_rewrites_pair_columns_to_the_supplied_spelling():
    table = QTable({'columns': ['From', 'To'],
                    'data': [['p1', 'd1'], ['P2', 'D1'], ['p1', 'D2'], ['P2', 'd2'], ['X', 'Y']]}, name='cost')

    table.assert_complete_cross_join('From', 'To', ['P1', 'P2'], ['D1', 'D2'])

    assert table.column('From') == ['P1', 'P2', 'P1', 'P2', 'X']
    assert table.column('To') == ['D1', 'D1', 'D2', 'D2', 'Y']


def test_lookups_after_foreign_key_check_use_one_spelling():
    supply = QTable({'columns': ['Plant', 'Capacity'], 'data': [['P1', 5]]},
                    schema={'Plant': str, 'Capacity': float}, name='supply')
    cost = QTable({'columns': ['Plant', 'Cost'], 'data': [['p1', 7]]},
                  schema={'Plant': str, 'Cost': float}, name='cost')

    cost.assert_foreign_key(supply, 'Plant', 'Plant')

    assert cost.to_map('Plant', 'Cost')[supply.column('Plant')[0]] == 7.0


def test_optional_text_column_blanks_become_empty_strings():
    df = pd.DataFrame({'Worker': ['W1', 'W2', 'W3'], 'Skills': ['a,b', None, float('nan')]})

    table = QTable(df, schema={'Worker': str, 'Skills': {'type': str, 'required': False}})

    assert table.column('Skills') == ['a,b', '', '']


def test_optional_returns_none_for_missing_or_empty_input_else_a_validated_table():
    schema = {'a': str, 'n': float}

    assert QTable.optional(None, name='t', schema=schema) is None
    assert QTable.optional(pd.DataFrame(), name='t', schema=schema) is None
    assert QTable.optional({'columns': ['a', 'n'], 'data': [['', None]]}, name='t', schema=schema) is None

    table = QTable.optional({'columns': ['A', 'n'], 'data': [['x', '2']]}, name='t', schema=schema)
    assert table.to_map('a', 'n') == {'x': 2.0}
    with pytest.raises(ValueError, match='row 1: t: invalid n'):
        QTable.optional({'columns': ['a', 'n'], 'data': [['x', 'bad']]}, name='t', schema=schema)


def test_dataframe_columns_keep_their_own_types():
    df = pd.DataFrame({'Period': [1, 2], 'Capacity': [120.5, 115.0], 'Name': ['a', 'b'], 'Flag': [True, False]})

    table = QTable(df, name='t')

    assert table.column('Period') == [1, 2]
    assert all(type(v) is int for v in table.column('Period'))
    assert table.column('Capacity') == [120.5, 115.0]
    assert table.column('Flag') == [True, False]
    assert QTable(df, schema={'Period': str, 'Capacity': float}).column('Period') == ['1', '2']


def test_is_empty_cell_is_structural_and_keeps_text_codes():
    from qcore.qd_data import is_blank, is_empty_cell

    assert all(is_empty_cell(v) for v in (None, float('nan'), '', '   '))
    assert not any(is_empty_cell(v) for v in (0, False, 'NA', 'none', 'null'))
    assert is_blank('NA') and not is_empty_cell('NA')


def test_sum_by_ignores_blank_values_but_rejects_blank_keys():
    table = QTable({'columns': ['k', 'v'], 'data': [['a', 1], ['a', None], ['b', None], ['c', 5]]}, name='t')

    assert table.sum_by('k', 'v') == {'a': 1, 'b': 0, 'c': 5}
    with pytest.raises(ValueError, match=r"t: blank key \['k'\]"):
        QTable({'columns': ['k', 'v'], 'data': [['a', 1], [None, 2]]}, name='t').sum_by('k', 'v')


def test_to_map_rejects_blank_keys_and_keeps_blank_values():
    ok = QTable({'columns': ['k', 'v'], 'data': [['a', None], ['b', 2]]}, name='t')

    assert ok.to_map('k', 'v') == {'a': None, 'b': 2}
    with pytest.raises(ValueError, match='blank key'):
        QTable({'columns': ['k', 'v'], 'data': [[float('nan'), 1], ['b', 2]]}, name='t').to_map('k', 'v')


def test_assert_unique_treats_none_nan_and_empty_text_as_blank():
    table = QTable({'columns': ['k'], 'data': [['a'], [None], [float('nan')], ['']]}, name='t', validate=False)

    assert table.assert_unique('k', ignore_blank=True) == ['a']
    with pytest.raises(ValueError, match=r'\(blank\)/\(blank\)'):
        table.assert_unique('k')


def test_assert_unique_pairs_ignores_pairs_with_an_empty_side():
    table = QTable({'columns': ['a', 'b'], 'data': [['x', 'y'], ['x', None], ['x', None], [None, 'y'], [None, 'y']]},
                   name='t', validate=False)

    assert table.assert_unique_pairs('a', 'b') == {('x', 'y')}
