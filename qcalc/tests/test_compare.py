import pytest
import qsett
import qconst

qsett.init()

from calculators.all.analytics import compare


def test_compare_evaluates_discrete_multi_variable_rows():
    result = compare(
        variation_target='v',
        xpr='x + y * z',
        inputs={
            'columns': ['Variable', 'V1', 'V2', 'V3'],
            'data': [['x', 1, 2, 3], ['y', 2, 3, 4], ['z', 3, 4, 5]],
        },
        table_columns='Result',
        chart_columns='Result',
    )

    assert list(result['table'].columns) == ['Variation', 'x', 'y', 'z', 'Result']
    assert result['table']['Variation'].tolist() == ['V1', 'V2', 'V3']
    assert result['table'][['x', 'y', 'z']].values.tolist() == [
        [1, 2, 3], [2, 3, 4], [3, 4, 5],
    ]
    assert result['table']['Result'].tolist() == [7, 14, 23]
    assert result['chart'] is not None


def test_compare_selects_result_columns_by_units():
    result = compare(
        xpr="{'Distance': q('x m'), 'Weight': q('y kg')}",
        inputs={
            'columns': ['Variable', 'V1', 'V2', 'V3'],
            'data': [['x', 1, 2, 3], ['y', 4, 5, 6]],
        },
        table_units='m',
        chart_units='kg',
    )

    distance_col = f'Distance {qconst.TBL_UOM_SEP} m'
    weight_col = f'Weight {qconst.TBL_UOM_SEP} kg'

    assert list(result['table'].columns) == [
        'Variation', 'x', 'y', distance_col, weight_col,
    ]
    assert result['table']['Variation'].tolist() == ['V1', 'V2', 'V3']
    assert result['table'][distance_col].tolist() == [1, 2, 3]
    assert result['table'][weight_col].tolist() == [4, 5, 6]
    assert result['chart'] is not None


def _run(target, xpr, columns, data):
    return compare(variation_target=target, xpr=xpr, inputs={'columns': columns, 'data': data})['table']


def test_compare_variables_relative_to_first_column():
    table = _run(
        'v', 'x + y',
        ['Variable', 'V1', 'V2', 'V3', 'V4', 'V5', 'V6'],
        [['x', 10, '+10%', '50%', '5(+)', '2(x)', '4(/)'], ['y', 1, 7, '-50%', '2(-)', '0.5(*)', '1(%)']],
    )
    assert table['x'].tolist() == [10, 11, 5, 15, 20, 2.5]
    assert table['y'].tolist() == [1, 7, 0.5, -1, 0.5, 0.01]
    assert table['Variation'].tolist() == ['V1', 'V2', 'V3', 'V4', 'V5', 'V6']


def test_compare_variables_base_column_must_be_plain():
    with pytest.raises(Exception, match='base column'):
        _run('v', 'x', ['Variable', 'V1', 'V2'], [['x', '5%', 3]])


def test_compare_variables_division_by_zero_and_missing_base():
    with pytest.raises(Exception, match='divide'):
        _run('v', 'x', ['Variable', 'V1', 'V2'], [['x', 4, '0(/)']])
    with pytest.raises(Exception, match='no numeric base'):
        _run('v', 'x', ['Variable', 'V1', 'V2'], [['x', 'abc', '5(+)']])


def test_compare_parameters_relative_to_expression_values():
    table = _run(
        'p', "dict(a=2, b='4 kg')",
        ['Variable', 'V1', 'V2', 'V3'],
        [['a', '+50%', '2(x)', 7], ['b', '1(+)', '25%', '-10%']],
    )
    assert table['a'].tolist() == [3, 4, 7]
    assert table['b'].tolist() == [5, 1, 3.6]


def test_compare_parameters_without_base_fail():
    with pytest.raises(Exception, match='no numeric base'):
        _run('p', "dict(a=2)", ['Variable', 'V1'], [['c', '5(+)']])
