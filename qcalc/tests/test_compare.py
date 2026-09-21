import qsett

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
        table_columns='Result 1',
        chart_columns='Result 1',
    )

    assert list(result['table'].columns) == ['Variation', 'x', 'y', 'z', 'Result 1']
    assert result['table']['Variation'].tolist() == ['V1', 'V2', 'V3']
    assert result['table'][['x', 'y', 'z']].values.tolist() == [
        [1, 2, 3], [2, 3, 4], [3, 4, 5],
    ]
    assert result['table']['Result 1'].tolist() == [7, 14, 23]
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

    assert list(result['table'].columns) == [
        'Variation', 'x', 'y', 'Distance (m)', 'Weight (kg)',
    ]
    assert result['table']['Variation'].tolist() == ['V1', 'V2', 'V3']
    assert result['table']['Distance (m)'].tolist() == [1, 2, 3]
    assert result['table']['Weight (kg)'].tolist() == [4, 5, 6]
    assert result['chart'] is not None
