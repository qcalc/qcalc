import copy
import inspect

import pytest

import qsett

qsett.init()

from calculators.all.business.finance import finstate, finstate2
from calculators.all.business.finance.cal_fin_statements import _fin2_rows


def _table(**overrides):
    inputs = copy.deepcopy(inspect.signature(finstate2).parameters['inputs'].default)
    for label, column, value in overrides.get('cells', []):
        row = next(r for r in inputs['data'] if r[0] == label)
        row[inputs['columns'].index(column)] = value
    return inputs


def test_default_columns_match_finstate():
    result = finstate2()
    expected = finstate()
    for name, table in expected.items():
        out = result[name]
        assert list(out.columns) == list(table.columns[:-1]) + ['Company A', 'Company B']
        assert out['Company A'].tolist() == table.iloc[:, -1].tolist()
        assert out['Company B'].tolist() == table.iloc[:, -1].tolist()


def test_columns_use_their_own_inputs():
    inputs = _table(cells=[('Sales', 'Company B', 20000)])
    result = finstate2(inputs=inputs)
    expected = finstate(sales_period=20000)
    assert result['Income Statement']['Company B'].tolist() == expected['Income Statement']['Period'].tolist()
    assert result['Ratios']['Company B'].tolist() == expected['Ratios']['Value'].tolist()


def test_same_basis_uses_first_column_basis():
    inputs = _table(cells=[('Tax Rate', 'Company B', 0.10), ('Tax Rate', 'Company A', 0.30)])
    same = finstate2(inputs=inputs, same_basis=True)
    own = finstate2(inputs=inputs, same_basis=False)
    assert same['Income Statement']['Company B'].tolist() == finstate(tax_rate=0.30)['Income Statement']['Period'].tolist()
    assert own['Income Statement']['Company B'].tolist() == finstate(tax_rate=0.10)['Income Statement']['Period'].tolist()
    assert own['Income Statement']['Company A'].tolist() == same['Income Statement']['Company A'].tolist()


def test_row_order_and_label_case_are_tolerated():
    inputs = _table(cells=[('Sales', 'Company B', 20000)])
    inputs['data'] = inputs['data'][::-1]
    inputs['data'][0][0] = inputs['data'][0][0].upper()
    assert finstate2(inputs=inputs)['Income Statement']['Company B'].tolist() == finstate2(
        inputs=_table(cells=[('Sales', 'Company B', 20000)]))['Income Statement']['Company B'].tolist()


def test_added_column():
    inputs = _table()
    inputs['columns'].append('Company C')
    for row in inputs['data']:
        row.append(row[1])
    assert list(finstate2(inputs=inputs)['Balance Sheet'].columns)[-3:] == ['Company A', 'Company B', 'Company C']


@pytest.mark.parametrize('change, message', [
    (lambda t: t['data'][3].__setitem__(0, 'Revenue'), 'not found in'),
    (lambda t: t['data'].pop(), 'not found in'),
    (lambda t: t['data'].append(['', 1, 1]), 'extra blank rows'),
    (lambda t: t['data'].append(list(t['data'][0])), 'duplicate'),
    (lambda t: t['columns'].__setitem__(2, 'Company A'), 'different from each other'),
    (lambda t: t['columns'].__setitem__(2, ' '), 'needs a name'),
    (lambda t: t['columns'].__setitem__(2, 'Acronym'), 'not allowed'),
    (lambda t: t['columns'].__setitem__(0, 'Item'), 'missing required column'),
    (lambda t: t['data'][3].__setitem__(1, '40%'), 'not a number'),
])
def test_invalid_inputs_are_rejected(change, message):
    inputs = _table()
    change(inputs)
    with pytest.raises(Exception, match=message):
        finstate2(inputs=inputs)


def test_figures_in_is_information_only():
    assert finstate(figures_in='1 BDT')['Ratios'].equals(finstate()['Ratios'])
    assert finstate2(figures_in='1000000 BDT')['Ratios'].equals(finstate2()['Ratios'])
    assert 'Figures In' not in [label for label, _ in _fin2_rows()]
    assert inspect.signature(finstate2).parameters['figures_in'].default == '1000 USD'
    assert inspect.signature(finstate).parameters['figures_in'].default == '1000 USD'


def test_every_finstate_parameter_has_a_row():
    assert sorted(name for _, name in _fin2_rows()) == sorted(set(finstate.__code__.co_varnames[:finstate.__code__.co_argcount]) - {'figures_in'})


def _ratio(table, acronym):
    return table.loc[table['Acronym'] == acronym].iloc[0, -1]


def test_finstate_reports_cash_conversion_cycle():
    ratios = finstate()['Ratios']
    assert _ratio(ratios, 'CCC') == pytest.approx(_ratio(ratios, 'DIO') + _ratio(ratios, 'DSO') - _ratio(ratios, 'DPO'))


def test_finstate2_reports_cash_conversion_cycle_per_column():
    inputs = _table(cells=[('Accounts Receivable', 'Company B', 6000)])
    ratios = finstate2(inputs=inputs)['Ratios']
    row = ratios.loc[ratios['Acronym'] == 'CCC'].iloc[0]
    assert row['Company A'] == pytest.approx(finstate()['Ratios'].query("Acronym == 'CCC'")['Value'].iloc[0])
    assert row['Company B'] == pytest.approx(
        finstate(accounts_receivable=6000)['Ratios'].query("Acronym == 'CCC'")['Value'].iloc[0])
    assert row['Company B'] > row['Company A']

def test_ratio_groups_and_new_ratios():
    ratios = finstate()['Ratios']
    metrics = ratios['Metric'].tolist()
    groups = [f'=== {g} ===' for g in (
        'PROFITABILITY', 'RETURNS', 'EFFICIENCY & WORKING CAPITAL', 'LIQUIDITY', 'LEVERAGE & SOLVENCY', 'PER SHARE')]
    assert [m for m in metrics if m in groups] == groups
    for group in groups:
        assert ratios.loc[ratios['Metric'] == group, 'Value'].iloc[0] == ''
    assert _ratio(ratios, 'D/E') == pytest.approx(4800 / 5600)
    assert _ratio(ratios, 'NWC') == pytest.approx(5400)
    assert _ratio(ratios, 'BVPS') == pytest.approx(5.6)
    row = ratios.set_index('Metric')['Value']
    assert row['Current Ratio'] == pytest.approx(7.0)
    assert row['Quick Ratio'] == pytest.approx(3500 / 900)
    assert row['Interest Coverage'] == pytest.approx(1800 / 240)
    assert row['Net Debt / EBITDA'] == pytest.approx(4300 / 1800)
    assert row['EBITDA Margin'] == '12.86%'


def test_undefined_ratios_show_na():
    row = finstate(long_term_debt=0, accounts_payable=0, shares_outstanding=0)['Ratios'].set_index('Metric')['Value']
    assert row['Current Ratio'] == row['Quick Ratio'] == row['Interest Coverage'] == row['Book Value Per Share'] == 'n/a'
    assert row['Debt-to-Equity'] == 0


def test_group_headings_are_not_result_cells():
    from calc import flatten_tables
    cells = flatten_tables(finstate2(), 'Ratios')
    assert not any('LIQUIDITY' in key for key in cells)
    assert cells['Ratios: Current Ratio: Company A'] == pytest.approx(7.0)
    assert 'Ratios: Interest Coverage: Company B' in cells
    assert list(flatten_tables(finstate(), 'Ratios: ROE, Ratios: D/E')) == ['Ratios: Return on Equity', 'Ratios: Debt-to-Equity']


def test_finstate2_groups_and_values_per_column():
    inputs = _table(cells=[('Long Term Debt', 'Company B', 0)])
    ratios = finstate2(inputs=inputs)['Ratios']
    assert ratios['Metric'].tolist() == finstate()['Ratios']['Metric'].tolist()
    row = ratios.set_index('Metric')
    assert row.loc['=== LIQUIDITY ===', 'Company A'] == ''
    assert row.loc['Interest Coverage', 'Company B'] == 'n/a'
    assert row.loc['Interest Coverage', 'Company A'] == pytest.approx(7.5)

def test_balance_sheet_has_section_headings():
    from calc import flatten_tables
    expected = ['=== ASSETS ===', '=== LIABILITIES ===', '=== EQUITY ===']
    for sheet in (finstate()['Balance Sheet'], finstate2()['Balance Sheet']):
        items = sheet['Line Item'].tolist()
        assert [i for i in items if i.startswith('===')] == expected
        assert '' not in items
        assert items.index('Total Assets') < items.index('=== LIABILITIES ===') < items.index('Accounts Payable')
        assert items.index('Total Liabilities') < items.index('=== EQUITY ===') < items.index('Common Stock')
    cells = flatten_tables(finstate(), 'Balance Sheet')
    assert not any('===' in key for key in cells)
    assert cells['Balance Sheet: Total Assets'] == 11300