# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import pandas as pd

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
            'tax_rate': {
                'type': 'float',
                'initial': DEFAULT_TAX_RATE,
                'help_text': 'Tax rate as a decimal, e.g. 0.40 for 40%.',
            },
            'interest_rate': {
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
    roa = net_income / total_assets if total_assets else 0.0
    roe = net_income / total_equity if total_equity else 0.0
    nopat = ebit * (1.0 - tax_rate)
    invested_capital = long_term_debt + total_equity
    roic = nopat / invested_capital if invested_capital else 0.0
    ebitda = ebit + depreciation_period
    rona = nopat / net_operating_assets if net_operating_assets else 0.0
    eps = net_income / shares_outstanding if shares_outstanding else 0.0

    income_statement = pd.DataFrame(
        [
            ['Sales', '', sales_period],
            ['Cost of Goods Sold', '', cogs_period],
            ['Gross Profit', '', gross_profit],
            ['Selling, General and Administrative Expenses', 'SG&A', sga_period],
            ['Other Operating Income', '', other_operating_income],
            ['Other Operating Expense', '', other_operating_expense],
            ['Earnings Before Interest, Taxes, Depreciation and Amortization', 'EBITDA', ebitda],
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
            ['Cash & Equivalents', cash_and_equivalents],
            ['Accounts Receivable', accounts_receivable],
            ['Inventories', inventories],
            ['Total Current Assets', total_current_assets],
            ['Net Property/Plant/Equipment', net_pp_e],
            ['Total Assets', total_assets],
            ['', ''],
            ['Accounts Payable', accounts_payable],
            ['Total Current Liabilities', total_current_liabilities],
            ['Long Term Debt', long_term_debt],
            ['Total Liabilities', total_liabilities],
            ['Common Stock', common_stock],
            ['Retained Earnings', retained_earnings],
            ["Total Stockholder's Equity", total_equity],
            ['Total Liabilities & Equity', total_liabilities_and_equity],
        ],
        columns=['Line Item', 'Period'],
    )

    ratios = pd.DataFrame(
        [
            ['Gross Margin', '', _pct(gross_margin)],
            ['Operating Margin', '', _pct(operating_margin)],
            ['Net Margin', '', _pct(net_margin)],
            ['Asset Turnover', '', asset_turnover],
            ['Inventory Turnover', '', inventory_turnover],
            ['Accounts Receivable Turnover', '', receivables_turnover],
            ['Accounts Payable Turnover', '', payables_turnover],
            ['Days Sales Outstanding', 'DSO', dso],
            ['Days Inventory Outstanding', 'DIO', dio],
            ['Days Payables Outstanding', 'DPO', dpo],
            ['Return on Assets', 'ROA', _pct(roa)],
            ['Return on Equity', 'ROE', _pct(roe)],
            ['Net Operating Profit After Tax', 'NOPAT', nopat],
            ['Invested Capital = Interest Bearing Debt + Equity', '', invested_capital],
            ['Return on Invested Capital', 'ROIC', _pct(roic)],
            ['Return on Net Operating Assets', 'RONA', _pct(rona)],
            ['Earnings Per Share', 'EPS', eps],
        ],
        columns=['Metric', 'Acronym', 'Value'],
    )


    return {
        'Income Statement': income_statement,
        'Balance Sheet': balance_sheet,
        'Ratios': ratios,
    }
