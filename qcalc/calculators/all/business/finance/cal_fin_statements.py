# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import inspect

import pandas as pd

from calc import require_columns, require_unique_values, require_values_subset
from qcore import qtbl
from qutil import md2html


DEFAULT_TAX_RATE = 0.40
DEFAULT_INTEREST_RATE = 0.05


def finstate__info():
    return {
        'title': 'Financial Statements Builder',
        'desc': (
            'Build a simple pro-forma income statement, balance sheet, and '
            'profitability ratios from a compact set of financial inputs.'
        ),
        'calculate': 'Build',
        'layout': 'tb',
        'table_out_all': True,
        'input_columns': 1,
        'input_blocks': [
            {
                'column': 1,
                'tabs': [
                    {
                        'title': 'Basis',
                        'fields': [
                            'figures_in',
                            'tax_rate',
                            'interest_rate',
                            'period_months',
                        ],
                    },
                    {
                        'title': 'Operating Inputs',
                        'fields': [
                            'sales_period',
                            'cogs_period',
                            'sga_period',
                            'depreciation_period',
                        ],
                    },
                    {
                        'title': 'Balance Inputs',
                        'fields': [
                            'cash_and_equivalents',
                            'accounts_receivable',
                            'inventories',
                            'net_ppe',
                            'accounts_payable',
                            'long_term_debt',
                            'common_stock',
                            'retained_earnings',
                        ],
                    },
                    {
                        'title': 'Additional Drivers',
                        'fields': [
                            'other_operating_income',
                            'other_operating_expense',
                            'shares_outstanding',
                        ],
                    },
                ],
            },
        ],
        'schema': {
            'figures_in': {
                'label': 'Figures In',
                'help_text': 'Unit and scale of the monetary figures, e.g. 1000 USD for thousands of US dollars. For information only; it does not affect any calculation.',
            },
            'tax_rate': {
                'label': 'Tax Rate',
                'type': 'float',
                'initial': DEFAULT_TAX_RATE,
                'help_text': 'Tax rate as a decimal, e.g. 0.40 for 40%.',
            },
            'interest_rate': {
                'label': 'Interest Rate',
                'type': 'float',
                'initial': DEFAULT_INTEREST_RATE,
                'help_text': 'Interest rate applied to long-term debt, as a decimal.',
            },
            'sales_period': {
                'label': 'Sales',
                'help_text': 'Revenue for the reporting period.',
            },
            'cogs_period': {
                'label': 'Cost of Goods Sold',
                'help_text': 'Direct cost of producing or purchasing the goods sold.',
            },
            'sga_period': {
                'label': 'SG&A Expense',
                'help_text': 'Selling, general, and administrative expense for the period.',
            },
            'depreciation_period': {
                'label': 'Depreciation & Amortization',
                'help_text': 'Non-cash allocation of asset cost recognized in the period.',
            },
            'other_operating_income': {
                'label': 'Other Operating Income',
                'help_text': 'Additional operating income outside the core sales line.',
            },
            'other_operating_expense': {
                'label': 'Other Operating Expense',
                'help_text': 'Additional operating expense outside the core cost lines.',
            },
            'period_months': {
                'label': 'Period (Months)',
                'help_text': 'Number of months in the reporting period used for DSO, DIO, and DPO.',
                'initial': 12,
            },
            'cash_and_equivalents': {
                'label': 'Cash & Equivalents',
                'help_text': 'Liquid cash and near-cash resources.',
            },
            'accounts_receivable': {
                'label': 'Accounts Receivable',
                'help_text': 'Amounts owed by customers.',
            },
            'inventories': {
                'label': 'Inventories',
                'help_text': 'Goods held for sale or production use.',
            },
            'net_ppe': {
                'label': 'Net Property/Plant/Equipment',
                'help_text': 'Net book value of long-lived operating assets.',
            },
            'accounts_payable': {
                'label': 'Accounts Payable',
                'help_text': 'Amounts owed to suppliers and vendors.',
            },
            'long_term_debt': {
                'label': 'Long Term Debt',
                'help_text': 'Interest-bearing borrowings due beyond the near term.',
            },
            'common_stock': {
                'label': 'Common Stock',
                'help_text': 'Paid-in equity capital from shareholders.',
            },
            'retained_earnings': {
                'label': 'Retained Earnings',
                'help_text': 'Cumulative profit retained in the business.',
            },
            'shares_outstanding': {
                'label': 'Shares Outstanding',
                'help_text': 'Number of shares used to compute earnings per share.',
            },
        },
    }


def finstate__help():
    quick_start = r"""
### Quick Start

Enter one reporting period of sales, costs, balance-sheet values, and
a tax and interest basis. Use **Period (Months)** to scale DSO, DIO,
and DPO to the correct time base.

The calculator returns a compact income statement, balance sheet, and
ratio table. For the full interpretation guide, open the separate help
card.
"""
    return md2html(quick_start)


def _num(value):
    return float(value or 0)


def _pct(value):
    return f'{value * 100.0:.2f}%'


def _div(numerator, denominator):
    # undefined (not zero) when the denominator is zero, e.g. interest coverage of a debt-free company
    return numerator / denominator if denominator else 'n/a'


def finstate(
    tax_rate=DEFAULT_TAX_RATE,
    interest_rate=DEFAULT_INTEREST_RATE,
    sales_period=14000,
    cogs_period=11000,
    sga_period=1200,
    depreciation_period=0,
    period_months=12,
    other_operating_income=0,
    other_operating_expense=0,
    cash_and_equivalents=500,
    accounts_receivable=3000,
    inventories=2800,
    net_ppe=5000,
    accounts_payable=900,
    long_term_debt=4800,
    common_stock=4200,
    retained_earnings=1400,
    shares_outstanding=1000,
    figures_in='1000 USD',  # information only
):
    tax_rate = _num(tax_rate)
    interest_rate = _num(interest_rate)

    sales_period = _num(sales_period)
    cogs_period = _num(cogs_period)
    sga_period = _num(sga_period)
    depreciation_period = _num(depreciation_period)
    period_months = _num(period_months)
    other_operating_income = _num(other_operating_income)
    other_operating_expense = _num(other_operating_expense)
    cash_and_equivalents = _num(cash_and_equivalents)
    accounts_receivable = _num(accounts_receivable)
    inventories = _num(inventories)
    net_pp_e = _num(net_ppe)
    accounts_payable = _num(accounts_payable)
    long_term_debt = _num(long_term_debt)
    common_stock = _num(common_stock)
    retained_earnings = _num(retained_earnings)
    shares_outstanding = _num(shares_outstanding)

    gross_profit = sales_period - cogs_period
    ebit = gross_profit - sga_period - depreciation_period + other_operating_income - other_operating_expense
    interest_expense = long_term_debt * interest_rate
    ebt = ebit - interest_expense
    income_taxes = ebt * tax_rate
    net_income = ebt - income_taxes

    total_current_assets = cash_and_equivalents + accounts_receivable + inventories
    total_assets = total_current_assets + net_pp_e
    total_current_liabilities = accounts_payable
    total_liabilities = total_current_liabilities + long_term_debt
    total_equity = common_stock + retained_earnings
    total_liabilities_and_equity = total_liabilities + total_equity
    net_operating_assets = net_pp_e + accounts_receivable + inventories - accounts_payable

    gross_margin = gross_profit / sales_period if sales_period else 0.0
    operating_margin = ebit / sales_period if sales_period else 0.0
    net_margin = net_income / sales_period if sales_period else 0.0
    asset_turnover = sales_period / total_assets if total_assets else 0.0
    inventory_turnover = cogs_period / inventories if inventories else 0.0
    receivables_turnover = sales_period / accounts_receivable if accounts_receivable else 0.0
    payables_turnover = cogs_period / accounts_payable if accounts_payable else 0.0
    period_days = period_months * 365.0 / 12.0
    dso = accounts_receivable / sales_period * period_days if sales_period else 0.0
    dio = inventories / cogs_period * period_days if cogs_period else 0.0
    dpo = accounts_payable / cogs_period * period_days if cogs_period else 0.0
    ccc = dio + dso - dpo
    roa = net_income / total_assets if total_assets else 0.0
    roe = net_income / total_equity if total_equity else 0.0
    nopat = ebit * (1.0 - tax_rate)
    invested_capital = long_term_debt + total_equity
    roic = nopat / invested_capital if invested_capital else 0.0
    ebitda = ebit + depreciation_period
    rona = nopat / net_operating_assets if net_operating_assets else 0.0
    eps = net_income / shares_outstanding if shares_outstanding else 0.0

    ebitda_margin = ebitda / sales_period if sales_period else 0.0
    sga_pct = sga_period / sales_period if sales_period else 0.0
    fixed_asset_turnover = sales_period / net_pp_e if net_pp_e else 0.0
    net_working_capital = total_current_assets - total_current_liabilities
    current_ratio = _div(total_current_assets, total_current_liabilities)
    quick_ratio = _div(cash_and_equivalents + accounts_receivable, total_current_liabilities)
    debt_to_equity = _div(long_term_debt, total_equity)
    liabilities_to_assets = _div(total_liabilities, total_assets)
    equity_multiplier = _div(total_assets, total_equity)
    interest_coverage = _div(ebit, interest_expense)
    net_debt = long_term_debt - cash_and_equivalents
    net_debt_to_ebitda = net_debt / ebitda if ebitda > 0 else 'n/a'
    book_value_per_share = _div(total_equity, shares_outstanding)
    income_statement = pd.DataFrame(
        [
            ['Sales', '', sales_period],
            ['Cost of Goods Sold', '', cogs_period],
            ['Gross Profit', '', gross_profit],
            ['Selling, General & Administrative Expenses', 'SG&A', sga_period],
            ['Other Operating Income', '', other_operating_income],
            ['Other Operating Expense', '', other_operating_expense],
            ['Earnings Before Interest, Taxes, D&A', 'EBITDA', ebitda],
            ['Depreciation & Amortization', '', depreciation_period],
            ['Earnings Before Interest and Taxes', 'EBIT', ebit],
            ['Interest Expense', '', interest_expense],
            ['Earnings Before Taxes', 'EBT', ebt],
            ['Income Taxes', '', income_taxes],
            ['Net Income', '', net_income],
        ],
        columns=['Line Item', 'Acronym', 'Period'],
    )

    balance_sheet = pd.DataFrame(
        [
            ['=== ASSETS ===', ''],
            ['Cash & Equivalents', cash_and_equivalents],
            ['Accounts Receivable', accounts_receivable],
            ['Inventories', inventories],
            ['Total Current Assets', total_current_assets],
            ['Net Property/Plant/Equipment', net_pp_e],
            ['Total Assets', total_assets],
            ['=== LIABILITIES ===', ''],
            ['Accounts Payable', accounts_payable],
            ['Total Current Liabilities', total_current_liabilities],
            ['Long Term Debt', long_term_debt],
            ['Total Liabilities', total_liabilities],
            ['=== EQUITY ===', ''],
            ['Common Stock', common_stock],
            ['Retained Earnings', retained_earnings],
            ["Total Stockholder's Equity", total_equity],
            ['Total Liabilities & Equity', total_liabilities_and_equity],
        ],
        columns=['Line Item', 'Period'],
    )

    ratios = pd.DataFrame(
        [
            ['=== PROFITABILITY ===', '', ''],
            ['Gross Margin', '', _pct(gross_margin)],
            ['EBITDA Margin', '', _pct(ebitda_margin)],
            ['Operating Margin', '', _pct(operating_margin)],
            ['Net Margin', '', _pct(net_margin)],
            ['SG&A % of Sales', '', _pct(sga_pct)],
            ['=== RETURNS ===', '', ''],
            ['Return on Assets', 'ROA', _pct(roa)],
            ['Return on Equity', 'ROE', _pct(roe)],
            ['Net Operating Profit After Tax', 'NOPAT', nopat],
            ['Invested Capital = Interest Bearing Debt + Equity', '', invested_capital],
            ['Return on Invested Capital', 'ROIC', _pct(roic)],
            ['Return on Net Operating Assets', 'RONA', _pct(rona)],
            ['=== EFFICIENCY & WORKING CAPITAL ===', '', ''],
            ['Asset Turnover', '', asset_turnover],
            ['Fixed Asset Turnover', '', fixed_asset_turnover],
            ['Inventory Turnover', '', inventory_turnover],
            ['Accounts Receivable Turnover', '', receivables_turnover],
            ['Accounts Payable Turnover', '', payables_turnover],
            ['Days Sales Outstanding', 'DSO', dso],
            ['Days Inventory Outstanding', 'DIO', dio],
            ['Days Payables Outstanding', 'DPO', dpo],
            ['Cash Conversion Cycle', 'CCC', ccc],
            ['=== LIQUIDITY ===', '', ''],
            ['Current Ratio', '', current_ratio],
            ['Quick Ratio', '', quick_ratio],
            ['Net Working Capital', 'NWC', net_working_capital],
            ['=== LEVERAGE & SOLVENCY ===', '', ''],
            ['Debt-to-Equity', 'D/E', debt_to_equity],
            ['Liabilities-to-Assets', '', liabilities_to_assets],
            ['Equity Multiplier', '', equity_multiplier],
            ['Interest Coverage', '', interest_coverage],
            ['Net Debt', '', net_debt],
            ['Net Debt / EBITDA', '', net_debt_to_ebitda],
            ['=== PER SHARE ===', '', ''],
            ['Earnings Per Share', 'EPS', eps],
            ['Book Value Per Share', 'BVPS', book_value_per_share],
        ],        columns=['Metric', 'Acronym', 'Value'],
    )

    return {
        'Income Statement': income_statement,
        'Balance Sheet': balance_sheet,
        'Ratios': ratios,
    }


_FIN2_LABEL_COL = 'Line Item'
_FIN2_INPUTS = 'Inputs'
_FIN2_MASTER = 'Allowed line items'
_FIN2_INFO_PARAMS = ('figures_in',)
_FIN2_BASIS_PARAMS = ('tax_rate', 'interest_rate', 'period_months')
_FIN2_OUTPUT_LABEL_COLS = {'line item', 'acronym', 'metric'}


def _fin2_rows():
    # (label, parameter) pairs in the same order as the finstate input tabs
    info = finstate__info()
    labels = {name: spec['label'] for name, spec in info['schema'].items() if 'label' in spec}
    return [
        (labels[name], name)
        for tab in info['input_blocks'][0]['tabs']
        for name in tab['fields']
        if name not in _FIN2_INFO_PARAMS
    ]


def _fin2_default_inputs(entities):
    defaults = {k: v.default for k, v in inspect.signature(finstate).parameters.items()}
    return {
        'columns': [_FIN2_LABEL_COL] + list(entities),
        'data': [[label, *[defaults[name]] * len(entities)] for label, name in _fin2_rows()],
    }


def _fin2_validate(inputs, rows):
    # Row labels are the fixed contract of the table; entity columns are free-form.
    require_columns(inputs, _FIN2_INPUTS, [_FIN2_LABEL_COL])
    columns = inputs['columns']
    if columns[0] != _FIN2_LABEL_COL:
        raise Exception(f"The first column of the inputs table must be named '{_FIN2_LABEL_COL}'.")

    entities = [str(c).strip() for c in columns[1:]]
    if not entities:
        raise Exception('Add at least one value column to the inputs table (e.g. a period or a company).')
    if any(e == '' for e in entities):
        raise Exception('Every value column in the inputs table needs a name.')
    keys = [e.casefold() for e in entities]
    if len(set(keys)) != len(keys):
        raise Exception('Value column names in the inputs table must be different from each other.')
    reserved = [e for e in entities if e.casefold() in _FIN2_OUTPUT_LABEL_COLS]
    if reserved:
        raise Exception(f"Value column name(s) not allowed in the inputs table: {', '.join(reserved)}.")

    master = {'columns': [_FIN2_LABEL_COL], 'data': [[label] for label, _ in rows]}
    require_unique_values(inputs, _FIN2_INPUTS, _FIN2_LABEL_COL)
    require_values_subset(inputs, _FIN2_INPUTS, _FIN2_LABEL_COL, master, _FIN2_MASTER, _FIN2_LABEL_COL)
    require_values_subset(master, _FIN2_MASTER, _FIN2_LABEL_COL, inputs, _FIN2_INPUTS, _FIN2_LABEL_COL)
    if len(inputs['data']) != len(rows):
        raise Exception('The inputs table has extra blank rows. Remove them.')
    return entities


def _fin2_number(value, entity, label):
    try:
        return _num(value)
    except (TypeError, ValueError):
        raise Exception(
            f"'{value}' for {label} ({entity}) is not a number. "
            'Enter percentages as decimals, e.g. 0.40 for 40%.'
        ) from None


def _fin2_merge(results):
    # Same label columns as finstate; the single value column becomes one column per entity.
    entities = list(results)
    merged = {}
    for table in results[entities[0]]:
        frames = [results[e][table] for e in entities]
        values = pd.concat([f.iloc[:, -1].rename(e) for e, f in zip(entities, frames)], axis=1)
        merged[table] = pd.concat([frames[0].iloc[:, :-1], values], axis=1)
    return merged


def finstate2__info():
    return {
        'title': 'Financial Statements Comparison',
        'desc': (
            'Build the same income statement, balance sheet, and ratio tables '
            'as Financial Statements Builder for several periods or companies '
            'side by side, from a single table of inputs.'
        ),
        'calculate': 'Build',
        'layout': 'tb',
        'table_out_all': True,
        'schema': {
            'figures_in': {
                'label': 'Figures In',
                'help_text': 'Unit and scale of the monetary figures, e.g. 1000 USD for thousands of US dollars. For information only; it does not affect any calculation.',
            },
            'inputs': {
                'help_text': (
                    'One column per period or company. Keep the Line Item labels as they are; '
                    'rename or add value columns with Resize. Enter rates as decimals, e.g. 0.40 for 40%.'
                ),
            },
            'same_basis': {
                'label': 'Same Basis',
                'help_text': (
                    'Use the Tax Rate, Interest Rate, and Period (Months) of the first value column '
                    'for all columns. Clear to use each column\'s own values.'
                ),
            },
        },
    }


def finstate2__help():
    quick_start = r"""
### Quick Start

Enter one column of inputs per period or company (for example last year and
this year, or companies X, Y, and Z). Keep the **Line Item** labels
unchanged; rename the value columns and add more with **Resize**.

With **Same Basis** checked, the Tax Rate, Interest Rate, and Period
(Months) of the first value column apply to every column. Rates are
decimals, e.g. 0.40 for 40%.

The result has the same income statement, balance sheet, and ratio tables as
`finstate()`, with one value column per input column.
"""
    return md2html(quick_start)


def finstate2(
    figures_in='1000 USD',  # information only
    inputs: qtbl = _fin2_default_inputs(['Company A', 'Company B']),
    same_basis=True,
):
    rows = _fin2_rows()
    entities = _fin2_validate(inputs, rows)
    param_of = {label.strip().casefold(): name for label, name in rows}

    values = {}
    for row in inputs['data']:
        label = str(row[0]).strip()
        name = param_of[label.casefold()]
        for i, entity in enumerate(entities, start=1):
            cell = row[i] if i < len(row) else ''
            values.setdefault(entity, {})[name] = _fin2_number(cell, entity, label)

    if same_basis:
        first = values[entities[0]]
        for entity in entities[1:]:
            values[entity].update({name: first[name] for name in _FIN2_BASIS_PARAMS})

    return _fin2_merge({entity: finstate(**values[entity]) for entity in entities})
