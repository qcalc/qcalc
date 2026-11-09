# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha
# Tests generated with AI assistance. Reviewed and validated by the author.

import pandas as pd
import pytest
import qconst
from qcore import to_cast, QTable
from qcore.qb_qtable import _looks_like_alias
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
                    'data': [['Name', 'Dept'], [' Ann ', 'IT'], ['', None]]}, name='t')

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
