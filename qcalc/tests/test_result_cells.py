import pandas as pd
import pytest

import qsett

qsett.init()

from calc import flatten_tables, ResultCellsError
from calculators.all.analytics import redo, compare, monte_carlo, monte_carlo2
from calculators.all.business.finance import finstate
from qvars import qc_gpref as gs


def _tables():
    return {
        'Income Statement': pd.DataFrame(
            [['Sales', '', 100.0], ['Selling, General and Administrative', 'SG&A', 10.0],
             ['', '', ''], ['Earnings Before Interest and Taxes', 'EBIT', 30.0]],
            columns=['Line Item', 'Acronym', 'Period']),
        'Ratios': pd.DataFrame(
            [['Gross Margin', '', '45.50%'], ['Return on Equity', 'ROE', '8.28%']],
            columns=['Metric', 'Acronym', 'Value']),
        'Multi': pd.DataFrame([['A', 1, 2], ['B', 3, 4]], columns=['Item', 'Y1', 'Y2']),
    }


def test_blank_cells_do_not_flatten():
    result = _tables()
    assert flatten_tables(result, '') is result


def test_result_without_tables_is_unchanged():
    assert flatten_tables(5.0, 'Ratios: ROE') == 5.0


def test_cell_by_row_name_acronym_and_percent_parsing():
    flat = flatten_tables(_tables(), 'Income Statement: Sales, Income Statement: EBIT, ratios: roe')
    assert flat == {
        'Income Statement: Sales': 100.0,
        'Income Statement: Earnings Before Interest and Taxes': 30.0,
        'Ratios: Return on Equity': pytest.approx(0.0828),
    }


def test_row_index_range_wildcard_and_exclusion():
    assert list(flatten_tables(_tables(), 'Income Statement: 1-2')) == [
        'Income Statement: Sales', 'Income Statement: Selling, General and Administrative']
    assert list(flatten_tables(_tables(), 'Ratios: *margin*')) == ['Ratios: Gross Margin']
    assert list(flatten_tables(_tables(), 'Income Statement: ~Sales')) == [
        'Income Statement: Selling, General and Administrative',
        'Income Statement: Earnings Before Interest and Taxes']


def test_spacer_rows_are_skipped_for_whole_table():
    assert len(flatten_tables(_tables(), 'Income Statement')) == 3


def test_multiple_value_columns_are_named_and_selectable():
    assert flatten_tables(_tables(), 'Multi: B') == {'Multi: B: Y1': 3, 'Multi: B: Y2': 4}
    assert flatten_tables(_tables(), 'Multi: *: Y2') == {'Multi: A: Y2': 2, 'Multi: B: Y2': 4}


def test_unknown_table_yields_no_cells():
    assert flatten_tables(_tables(), 'Nope: Sales') == {}


def test_cell_count_is_capped_by_range_limit(monkeypatch):
    monkeypatch.setitem(gs, 'range_limit', 2)
    with pytest.raises(ResultCellsError):
        flatten_tables(_tables(), 'Income Statement')


FIN_XPR = "finstate(sales_period=x)"


def test_redo_finstate_cells_table_and_chart_columns():
    result = redo(
        variation_target='v', xpr=FIN_XPR, variable='x',
        variation_start=10000, variation_stop=16000, variation_step=2000,
        result_cells='Income Statement: Net Income, Ratios: ROE',
        table_columns='Income Statement: Net Income', chart_columns='Income Statement: Net Income',
    )
    assert list(result['table'].columns) == ['X', 'Income Statement: Net Income']
    assert result['chart'] is not None


def test_redo_finstate_cell_order_follows_spec():
    result = redo(
        variation_target='v', xpr=FIN_XPR, variable='x',
        variation_start=10000, variation_stop=16000, variation_step=2000,
        result_cells='Ratios: ROE, Income Statement: EBIT', show='table',
    )
    assert list(result['table'].columns) == [
        'X', 'Ratios: Return on Equity', 'Income Statement: Earnings Before Interest and Taxes']
    assert result['table']['Ratios: Return on Equity'].between(-1, 1).all()


def test_result_titles_keep_acronyms():
    result = redo(
        variation_target='v', xpr="{'Ratios: ROE': x, 'Income Statement: EBIT': x * 2}", variable='x',
        variation_start=1, variation_stop=3, variation_step=1, show='table',
    )
    assert list(result['table'].columns) == ['X', 'Ratios: ROE', 'Income Statement: EBIT']


def test_redo_tables_without_cells_hints_result_cells():
    with pytest.raises(Exception, match='result_cells'):
        redo(variation_target='v', xpr=FIN_XPR, variable='x',
             variation_start=10000, variation_stop=12000, variation_step=2000)


def test_compare_finstate_cells():
    result = compare(
        variation_target='v',
        xpr='finstate(sales_period=s)',
        inputs={'columns': ['Variable', 'Low', 'High'], 'data': [['s', 10000, 16000]]},
        result_cells='Income Statement: Net Income',
    )
    assert result['table']['Variation'].tolist() == ['Low', 'High']
    assert result['table']['Income Statement: Net Income'].tolist() == [-1464.0, 2136.0]


def test_compare_tables_without_cells_hints_result_cells():
    with pytest.raises(Exception, match='result_cells'):
        compare(
            variation_target='v', xpr='finstate(sales_period=s)',
            inputs={'columns': ['Variable', 'Low'], 'data': [['s', 10000]]},
        )


def test_monte_carlo_finstate_cell():
    result = monte_carlo(
        variation_target='v', xpr=FIN_XPR, variable='x', distribution='uniform',
        param1=10000, param2=16000, trials=20, result_cells='Income Statement: Net Income',
        show='table',
    )
    stats = dict(result['Statistics']['data'])
    assert stats['Trials used'] == 20
    assert stats['Min'] >= -1464.0 and stats['Max'] <= 2136.0


def test_monte_carlo2_finstate_cell():
    result = monte_carlo2(
        variation_target='v', xpr='finstate(sales_period=s, cogs_period=c)',
        variables='s, c', distributions='uniform, uniform', param1s='10000, 8000',
        param2s='16000, 12000', trials=20, result_cells='Income Statement: Net Income',
        show='table',
    )
    assert dict(result['Statistics']['data'])['Trials used'] == 20


def _goods():
    return {'x': pd.DataFrame(
        [['sugar', 130, 'medium', 13], ['tea', 50, 'large', 10],
         ['condensed milk', 90, 'large', 2], ['milk', 80, 'small', 5]],
        columns=['item', 'price', 'size', 'qty'])}


def _rows(spec):
    return sorted({key.split(': ')[1] for key in flatten_tables(_goods(), spec)})


def test_category_column_matches_all_rows_sharing_the_value():
    assert _rows('x:large') == ['condensed milk', 'tea']
    assert _rows('x:small') == ['milk']
    assert _rows('x:~large') == ['milk', 'sugar']
    assert _rows('x:large:qty') == ['condensed milk', 'tea']


def test_row_numbers_never_match_label_values():
    assert _rows('x:2') == ['tea']
    assert _rows('x:1-2') == ['sugar', 'tea']
    assert flatten_tables(_goods(), 'x:130') == {}


def test_non_value_column_and_unknown_column_select_nothing():
    assert flatten_tables(_goods(), 'x:milk:size') == {}
    assert flatten_tables(_goods(), 'x:milk:small') == {}


def test_duplicate_row_labels_match_all_and_stay_addressable():
    table = {'d': pd.DataFrame([['Total', 1], ['Tax', 2], ['Total', 3]], columns=['item', 'v'])}
    assert flatten_tables(table, 'd:Total') == {'d: Total': 1, 'd: Total (2)': 3}
    assert flatten_tables(table, 'd:Total (2)') == {'d: Total (2)': 3}


def test_scalars_are_kept_and_cells_appended():
    result = {'Total': 5, 'Rate': 0.1, **_tables()}
    flat = flatten_tables(result, 'Income Statement: Sales')
    assert flat == {'Total': 5, 'Rate': 0.1, 'Income Statement: Sales': 100.0}
    assert list(flat) == ['Total', 'Rate', 'Income Statement: Sales']


def test_cell_name_colliding_with_scalar_key_does_not_overwrite():
    result = {'Income Statement: Sales': 1, **_tables()}
    assert flatten_tables(result, 'Income Statement: Sales') == {
        'Income Statement: Sales': 1, 'Income Statement: Sales (2)': 100.0}


def test_scalars_only_result_is_unchanged_with_cells():
    result = {'Total': 5}
    assert flatten_tables(result, 'Income Statement: Sales') is result


def test_redo_mixes_scalars_and_cells_for_table_and_chart_filters():
    xpr = "{'Total': x * 2, 'Fin': finstate(sales_period=x)['Income Statement']}"
    common = dict(variation_target='v', xpr=xpr, variable='x', variation_start=10000,
                  variation_stop=16000, variation_step=2000, result_cells='Fin: Net Income')
    both = redo(**common, show='table')
    assert list(both['table'].columns) == ['X', 'Total', 'Fin: Net Income']
    assert both['table']['Total'].tolist() == [20000, 24000, 28000, 32000]

    only_scalar = redo(**common, table_columns='Total', chart_columns='Total')
    assert list(only_scalar['table'].columns) == ['X', 'Total']
    assert only_scalar['chart'] is not None

    only_cell = redo(**common, table_columns='Fin: Net Income')
    assert list(only_cell['table'].columns) == ['X', 'Fin: Net Income']


def _fin_redo(cells, **kw):
    return redo(
        variation_target='v', variable='x', variation_start=10000, variation_stop=12000, variation_step=2000,
        xpr="{'Total': x * 2, 'Fin': finstate(sales_period=x)['Income Statement']}",
        result_cells=cells, show='table', **kw)


def test_table_columns_accept_acronym_alias_together_with_scalars():
    full = 'Fin: Earnings Before Interest and Taxes'
    for spec in ('Total, Fin: EBIT', 'total, fin: ebit', 'Fin: EBIT, Total', 'Total, ' + full):
        out = _fin_redo('Fin: EBIT', table_columns=spec)
        assert list(out['table'].columns) == ['X', 'Total', full], spec


def test_alias_resolves_labels_containing_commas_and_negation():
    cells = 'Fin: SG&A, Fin: Net Income'
    out = _fin_redo(cells, table_columns='Fin: SG&A')
    assert list(out['table'].columns) == ['X', 'Fin: Selling, General & Administrative Expenses']
    out = _fin_redo(cells, table_columns='~Fin: SG&A')
    assert 'Fin: Selling, General & Administrative Expenses' not in out['table'].columns


def test_chart_columns_accept_acronym_alias():
    out = redo(
        variation_target='v', variable='x', variation_start=10000, variation_stop=12000, variation_step=2000,
        xpr="{'Total': x * 2, 'Fin': finstate(sales_period=x)['Income Statement']}",
        result_cells='Fin: EBIT', chart_columns='Fin: EBIT')
    assert out['chart'] is not None


def test_aliases_survive_flatten_and_collisions():
    flat = flatten_tables(_tables(), 'Income Statement: EBIT, Ratios: ROE')
    assert flat.aliases == {
        'Income Statement: Earnings Before Interest and Taxes': ['Income Statement: EBIT'],
        'Ratios: Return on Equity': ['Ratios: ROE'],
    }


def test_shared_text_value_alias_selects_all_matching_columns_in_filters():
    from calc import QResults, flatten_tables as _flatten
    goods = pd.DataFrame(
        [['sugar', 130, 'medium', 13], ['tea', 50, 'large', 10],
         ['condensed milk', 90, 'large', 2], ['milk', 80, 'small', 5]],
        columns=['item', 'price', 'size', 'qty'])
    result = _flatten({'Total': 1, 'Stock': goods}, 'Stock')
    qr = QResults([result], xvals=[1], variable='x', table_columns='Stock: large: price', show='table')
    assert list(qr.objects()['table'].columns) == [
        'X', 'Stock: Tea: Price', 'Stock: Condensed Milk: Price']
    qr = QResults([result], xvals=[1], variable='x', table_columns='~Stock: large: qty', show='table')
    assert 'Stock: Tea: Qty' not in qr.objects()['table'].columns
    assert 'Stock: Condensed Milk: Qty' not in qr.objects()['table'].columns
    assert 'Stock: Sugar: Qty' in qr.objects()['table'].columns
