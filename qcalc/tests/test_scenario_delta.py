import pytest
import qsett

qsett.init()

from calculators.all.analytics import scenario


def _row_by_variation(df):
    return {row['Variation']: row for _, row in df.iterrows()}


def test_scenario_delta_absolute_baseline():
    result = scenario(
        scenarios={
            'columns': ['Variation', 'x', 'y', 'Result 1'],
            'data': [['V1', 1, 2, 10], ['V2', 2, 3, 16], ['V3', 3, 4, 7]],
        },
        metric_columns='Result 1',
        variable_columns='x, y',
        baseline_variation='V1',
        delta_type='absolute',
    )

    table = result['table']
    assert list(table.columns) == ['Variation', 'x', 'y', 'Result 1', 'Result 1 Delta']
    assert table['Result 1 Delta'].tolist() == [0.0, 6.0, -3.0]
    assert result['chart'] is not None


def test_scenario_delta_percent():
    result = scenario(
        scenarios={
            'columns': ['Variation', 'Revenue (USD)'],
            'data': [['V1', 100], ['V2', 120], ['V3', 80]],
        },
        metric_columns='Revenue',
        variable_columns='',
        baseline_variation='V1',
        delta_type='percent',
    )

    table = result['table']
    assert 'Revenue Delta (%)' in table.columns
    assert table['Revenue Delta (%)'].tolist() == [0.0, 20.0, -20.0]


def test_scenario_delta_metric_units_filter():
    result = scenario(
        scenarios={
            'columns': ['Variation', 'Cost (USD)', 'Weight (kg)'],
            'data': [['V1', 100, 10], ['V2', 120, 12], ['V3', 90, 11]],
        },
        metric_units='kg',
        variable_columns='',
        baseline_variation='V1',
        delta_type='index',
    )

    table = result['table']
    assert list(table.columns) == ['Variation', 'Weight (kg)', 'Weight Index']
    assert table['Weight Index'].tolist() == [1.0, 1.2, 1.1]


def test_scenario_rank_mode_orders_by_selected_metric_and_top_n():
    result = scenario(
        scenarios={
            'columns': ['Variation', 'x', 'y', 'ROI (%)', 'Cost (USD)'],
            'data': [
                ['V1', 1, 2, 10, 80],
                ['V2', 2, 3, 20, 90],
                ['V3', 3, 4, 15, 70],
            ],
        },
        mode='rank',
        metric_columns='ROI, Cost',
        variable_columns='x, y',
        rank_by='ROI',
        rank_order='desc',
        top_n=2,
        show='table',
    )

    table = result['table']
    assert list(table['Variation']) == ['V2', 'V3']
    assert list(table['Rank']) == [1, 2]


def test_scenario_filter_mode_keeps_expected_rows():
    result = scenario(
        scenarios={
            'columns': ['Variation', 'x', 'y', 'ROI (%)', 'Cost (USD)'],
            'data': [
                ['V1', 1, 2, 10, 80],
                ['V2', 2, 3, 20, 90],
                ['V3', 3, 4, 15, 70],
            ],
        },
        mode='filter',
        metric_columns='ROI, Cost',
        variable_columns='x, y',
        filter_by='Cost',
        filter_operator='>=',
        filter_value='80',
        show='table',
    )

    table = result['table']
    assert list(table['Variation']) == ['V1', 'V2']
    assert list(table['Rank']) == [1, 2]


def test_scenario_score_mode_computes_weighted_ranking():
    result = scenario(
        scenarios={
            'columns': ['Variation', 'x', 'y', 'ROI (%)', 'Cost (USD)'],
            'data': [
                ['V1', 1, 2, 10, 80],
                ['V2', 2, 3, 20, 90],
                ['V3', 3, 4, 15, 70],
            ],
        },
        mode='score',
        metric_columns='ROI, Cost',
        variable_columns='x, y',
        score_weights='ROI:0.7, Cost:0.3',
        score_directions='ROI:high, Cost:low',
        score_column='Decision Score',
        show='table',
    )

    table = result['table']
    rows = _row_by_variation(table)
    assert list(table['Variation']) == ['V2', 'V3', 'V1']
    assert list(table['Rank']) == [1, 2, 3]
    assert float(rows['V2']['Decision Score']) == pytest.approx(0.7)
    assert float(rows['V3']['Decision Score']) == pytest.approx(0.65)
    assert float(rows['V1']['Decision Score']) == pytest.approx(0.15)


def test_scenario_rank_mode_with_non_numeric_metric_does_not_crash_chart():
    result = scenario(
        scenarios={
            'columns': ['Variation', 'Category'],
            'data': [['V1', 'A'], ['V2', 'B'], ['V3', 'C']],
        },
        mode='rank',
        metric_columns='Category',
        variable_columns='',
        rank_by='Category',
        show='both',
        chart_type='bars',
    )

    table = result['table']
    assert list(table['Variation']) == ['V1', 'V2', 'V3']
    assert list(table['Rank']) == [1, 2, 3]
    assert result['chart'] is None


def test_scenario_filter_mode_with_non_numeric_metrics_does_not_crash_chart():
    result = scenario(
        scenarios={
            'columns': ['Variation', 'Category'],
            'data': [['V1', 'A'], ['V2', 'B'], ['V3', 'A']],
        },
        mode='filter',
        metric_columns='Category',
        variable_columns='',
        filter_by='Category',
        filter_operator='contains',
        filter_value='A',
        show='both',
        chart_type='bars',
    )

    table = result['table']
    assert list(table['Variation']) == ['V1', 'V3']
    assert list(table['Rank']) == [1, 2]
    assert result['chart'] is None


def test_scenario_rank_mode_defaults_to_first_numeric_metric_when_not_specified():
    result = scenario(
        scenarios={
            'columns': ['Variation', 'Label', 'x', 'ROI (%)', 'Cost (USD)'],
            'data': [
                ['V1', 'A', 1, 10, 80],
                ['V2', 'B', 2, 20, 90],
                ['V3', 'C', 3, 15, 70],
            ],
        },
        mode='rank',
        variable_columns='x',
        show='both',
    )

    table = result['table']
    assert list(table['Variation']) == ['V2', 'V3', 'V1']
    assert list(table['Rank']) == [1, 2, 3]
    assert result['chart'] is not None


def test_scenario_filter_mode_defaults_to_first_numeric_metric_when_not_specified():
    result = scenario(
        scenarios={
            'columns': ['Variation', 'Label', 'x', 'ROI (%)', 'Cost (USD)'],
            'data': [
                ['V1', 'A', 1, 10, 80],
                ['V2', 'B', 2, 20, 90],
                ['V3', 'C', 3, 15, 70],
            ],
        },
        mode='filter',
        variable_columns='x',
        filter_operator='>=',
        filter_value='15',
        show='both',
    )

    table = result['table']
    assert list(table['Variation']) == ['V2', 'V3']
    assert list(table['Rank']) == [1, 2]
    assert result['chart'] is not None


def test_scenario_filter_mode_rejects_unmatched_filter_selector():
    with pytest.raises(Exception, match="filter_by 'Result 12' did not match any selected metric column"):
        scenario(
            scenarios={
                'columns': ['Variation', 'x', 'y', 'Result 1'],
                'data': [['V1', 1, 2, 3], ['V2', 2, 3, 4], ['V3', 3, 4, 5]],
            },
            mode='filter',
            filter_by='Result 12',
            filter_operator='>=',
            filter_value='0',
            show='both',
        )
