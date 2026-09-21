# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import pandas as pd
import pytest

from qutil import (
    QThread,
    parse_optional_number,
    require_columns,
    require_complete_pair_grid,
    require_unique_pairs,
    require_unique_values,
    require_values_subset,
    validate_value_columns_against_master,
)


def test_require_columns_renames_dataframe_columns_case_insensitive():
    df = pd.DataFrame({' source ': ['P1'], 'CAPACITY': [10]})

    require_columns(df, 'supply', ['Source', 'Capacity'])

    assert list(df.columns) == ['Source', 'Capacity']


def test_require_columns_renames_qtbl_columns_case_insensitive():
    table = {
        'columns': [' source ', 'CAPACITY'],
        'data': [['P1', 10]],
    }

    require_columns(table, 'supply', ['Source', 'Capacity'])

    assert table['columns'] == ['Source', 'Capacity']


def test_require_values_subset_is_case_insensitive():
    child = pd.DataFrame({'Source': ['p1', 'P2']})
    parent = pd.DataFrame({'source': ['P1', 'p2']})

    require_values_subset(child, 'child', 'Source', parent, 'parent', 'Source')


def test_validate_value_columns_against_master_renames_and_returns_values():
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

    result = validate_value_columns_against_master(
        matrix_table=cost,
        matrix_table_name='cost',
        master_table=facility,
        master_table_name='facility',
        master_value_col='Location',
        matrix_reserved_cols=['Location', 'Demand'],
    )

    assert 'BO' in cost.columns and 'NA' in cost.columns
    assert result['master_values'] == ['BO', 'NA']


def test_validate_value_columns_against_master_can_be_one_way_only():
    cost = pd.DataFrame({
        'Location': ['L1'],
        'Demand': [10],
        'BO': [1],
        'NA': [2],
        'EXTRA': [3],
    })
    facility = pd.DataFrame({'Location': ['BO', 'NA']})

    validate_value_columns_against_master(
        matrix_table=cost,
        matrix_table_name='cost',
        master_table=facility,
        master_table_name='facility',
        master_value_col='Location',
        matrix_reserved_cols=['Location', 'Demand'],
        require_master_in_matrix=True,
        require_matrix_in_master=False,
    )


def test_require_unique_values_raises_on_duplicate():
    projects = pd.DataFrame({'Project': ['P1', 'p1']})

    with pytest.raises(Exception, match='duplicate'):
        require_unique_values(projects, 'projects', 'Project')


def test_require_unique_pairs_raises_on_duplicate_pair():
    pair_table = pd.DataFrame({
        'Source': ['S1', 'S1'],
        'Destination': ['D1', 'd1'],
    })

    with pytest.raises(Exception, match='duplicate pair'):
        require_unique_pairs(pair_table, 'ship_cost', 'Source', 'Destination')


def test_require_complete_pair_grid_raises_on_missing_pair():
    ship_cost = pd.DataFrame({
        'Source': ['S1', 'S1', 'S2'],
        'Destination': ['D1', 'D2', 'D1'],
    })

    with pytest.raises(Exception, match='missing Source-Destination pair'):
        require_complete_pair_grid(
            pair_table=ship_cost,
            pair_table_name='ship_cost',
            left_col='Source',
            right_col='Destination',
            left_values=['S1', 'S2'],
            right_values=['D1', 'D2'],
            left_label='Source',
            right_label='Destination',
        )


def test_parse_optional_number_behaves_for_blank_valid_and_invalid():
    assert parse_optional_number('', 'budget_limit', float) is None
    assert parse_optional_number(None, 'budget_limit', float) is None
    assert parse_optional_number('12.5', 'budget_limit', float) == 12.5
    assert parse_optional_number('7', 'max_selected', int) == 7

    with pytest.raises(Exception, match='Invalid numeric value'):
        parse_optional_number('x7', 'max_selected', int)


def test_require_columns_strict_table_input_raises_for_suspicious_optional_alias():
    QThread.set_pref({'strict_table_input': True})
    df = pd.DataFrame({
        'Material': ['A'],
        'Unit Cost': [1.0],
        'Minimum Quantity': [0],
    })

    with pytest.raises(Exception, match='suspicious column name'):
        require_columns(df, 'blend_materials', ['Material', 'Unit Cost'], optional_cols=['Min Qty', 'Max Qty'])


def test_require_columns_non_strict_allows_suspicious_optional_alias():
    QThread.set_pref({'strict_table_input': False})
    df = pd.DataFrame({
        'Material': ['A'],
        'Unit Cost': [1.0],
        'Minimum Quantity': [0],
    })

    require_columns(df, 'blend_materials', ['Material', 'Unit Cost'], optional_cols=['Min Qty', 'Max Qty'])


def test_require_columns_strict_rejects_unexpected_columns_for_fixed_schema():
    QThread.set_pref({'strict_table_input': True})
    df = pd.DataFrame({
        'Location': ['BO'],
        'Capacity': [100],
        'Unexpected': [1],
    })

    with pytest.raises(Exception, match='unexpected column'):
        require_columns(
            df,
            'facility',
            ['Location', 'Capacity'],
            columns_can_grow=False,
        )


def test_require_columns_strict_allows_unexpected_columns_for_open_schema():
    QThread.set_pref({'strict_table_input': True})
    df = pd.DataFrame({
        'Location': ['L1'],
        'Demand': [10],
        'BO': [1],
        'NA': [2],
        'CustomDynamic': [3],
    })

    require_columns(
        df,
        'cost',
        ['Location', 'Demand'],
        columns_can_grow=True,
    )