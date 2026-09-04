# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from qcore import Qty
from qutil import css2ints


def debt_invest__info():
    return {
        'title': 'Debt Paydown vs Investment',
        'calculate': 'Compare',
        'schema': {
            'available_cash': {
                'help_text': 'Cash available either to pay down debt or invest.',
            },
            'debt_remaining': {
                'help_text': 'Current outstanding debt balance.',
            },
            'debt_rate': {
                'label': 'Debt Interest Rate',
                'help_text': 'Annual interest rate on the debt.',
            },
            'debt_term_years': {
                'label': 'Remaining Debt Term',
                'help_text': 'Remaining term of the debt in years.',
            },
            'investment_return': {
                'label': 'Expected Investment Return',
                'help_text': 'Expected annual investment return before tax.',
            },
            'investment_tax': {
                'help_text': 'Tax rate applied to investment returns.',
            },
            'inflation': {
                'label': 'Inflation Rate',
                'help_text': 'Expected annual inflation rate.',
            },
            'periods': {
                'label': 'Comparison Periods',
                'help_text': 'Comma-separated number of years, e.g. 5,10,20.',
            },
        },
    }


def debt_invest(
    available_cash='20000 USD',
    debt_remaining='100000 USD',
    debt_rate='9 pct/yr',
    debt_term_years: int = 20,
    investment_return='8 pct/yr',
    investment_tax='15 pct',
    inflation='3 pct/yr',
    periods: str = '5,10,20',
):
    # Normalize inputs.
    cash = Qty(available_cash)
    to_cur = cash.uom
    debt = Qty(debt_remaining, to_cur)
    debt_rate = Qty(debt_rate, 'pct/yr')
    investment_return = Qty(investment_return, 'pct/yr')
    investment_tax = Qty(investment_tax, 'pct')
    inflation = Qty(inflation, 'pct/yr')

    cash_value = cash.val
    debt_value = debt.val

    debt_rate_value = debt_rate.val / 100
    investment_rate_value = investment_return.val / 100
    tax_value = investment_tax.val / 100
    inflation_value = inflation.val / 100

    periods = css2ints(periods)

    if not periods:
        raise ValueError('At least one comparison period is required.')

    if any(p <= 0 for p in periods):
        raise ValueError('Comparison periods must be positive integers.')

    if debt_term_years <= 0:
        raise ValueError('Remaining debt term must be positive.')

    if cash_value < 0:
        raise ValueError('Available cash cannot be negative.')

    if debt_value < 0:
        raise ValueError('Debt remaining cannot be negative.')

    if cash_value > debt_value:
        cash_used_for_debt = debt_value
    else:
        cash_used_for_debt = cash_value

    # Monthly debt rate.
    monthly_debt_rate = debt_rate_value / 12
    total_debt_payments = debt_term_years * 12

    # Original monthly payment.
    if monthly_debt_rate == 0:
        original_payment = debt_value / total_debt_payments
    else:
        original_payment = (
            debt_value * monthly_debt_rate
            / (1 - (1 + monthly_debt_rate) ** -total_debt_payments)
        )

    # Debt balance after making the lump-sum payment.
    debt_after_paydown = debt_value - cash_used_for_debt

    if monthly_debt_rate == 0:
        reduced_payment = (
            debt_after_paydown / total_debt_payments
            if total_debt_payments else 0
        )
    else:
        reduced_payment = (
            debt_after_paydown * monthly_debt_rate
            / (1 - (1 + monthly_debt_rate) ** -total_debt_payments)
            if debt_after_paydown > 0
            else 0
        )

    # Monthly payment difference available for investment
    # under the debt-paydown strategy.
    monthly_saving = original_payment - reduced_payment
    # Investment return after tax.
    after_tax_investment_rate = investment_rate_value * (1 - tax_value)
    monthly_investment_rate = after_tax_investment_rate / 12

    # Build comparison table.
    rows = []

    for years in periods:
        months = years * 12
        # ---------------------------------------------------------
        # Strategy 1: INVEST
        #
        # Keep the original debt and invest the available cash.
        # ---------------------------------------------------------

        investment_value = (
            cash_value * (1 + monthly_investment_rate) ** months
        )

        # Debt balance under the original loan.
        if monthly_debt_rate == 0:
            debt_balance_invest = max(
                0,
                debt_value - original_payment * months
            )
        else:
            debt_balance_invest = (
                debt_value * (1 + monthly_debt_rate) ** months
                - original_payment
                * ((1 + monthly_debt_rate) ** months - 1)
                / monthly_debt_rate
            )

        debt_balance_invest = max(0, debt_balance_invest)

        # ---------------------------------------------------------
        # Strategy 2: PAY DOWN DEBT
        #
        # Apply the cash immediately to the debt.
        # Invest the monthly payment saving.
        # ---------------------------------------------------------

        # The debt balance after the lump-sum payment.
        if monthly_debt_rate == 0:
            debt_balance_paydown = max(0, debt_after_paydown - reduced_payment * months)
        else:
            debt_balance_paydown = (
                debt_after_paydown
                * (1 + monthly_debt_rate) ** months
                - reduced_payment
                * ((1 + monthly_debt_rate) ** months - 1)
                / monthly_debt_rate
            )

        debt_balance_paydown = max(0, debt_balance_paydown)

        # Invest the monthly payment saving.
        if monthly_investment_rate == 0:
            savings_investment = monthly_saving * months
        else:
            savings_investment = (
                monthly_saving
                * ((1 + monthly_investment_rate) ** months - 1)
                / monthly_investment_rate
            )

        # Net wealth relative to the debt.
        net_wealth_invest = investment_value - debt_balance_invest
        net_wealth_paydown = savings_investment - debt_balance_paydown
        wealth_difference = net_wealth_invest - net_wealth_paydown

        # Inflation adjustment.
        inflation_factor = (1 + inflation_value) ** years
        net_wealth_invest_real = net_wealth_invest / inflation_factor
        net_wealth_paydown_real = net_wealth_paydown / inflation_factor
        wealth_difference_real = wealth_difference / inflation_factor

        if wealth_difference > 0:
            better = 'Invest'
        elif wealth_difference < 0:
            better = 'Pay down debt'
        else:
            better = 'Equal'

        rows.append([
            years,
            Qty(investment_value, to_cur),
            Qty(debt_balance_invest, to_cur),
            Qty(net_wealth_invest, to_cur),
            Qty(savings_investment, to_cur),
            Qty(debt_balance_paydown, to_cur),
            Qty(net_wealth_paydown, to_cur),
            Qty(wealth_difference, to_cur),
            Qty(net_wealth_invest_real, to_cur),
            Qty(net_wealth_paydown_real, to_cur),
            Qty(wealth_difference_real, to_cur),
            better,
        ])

    table = {
        'columns': [
            'Years',
            'Investment Value',
            'Debt Balance (Invest)',
            'Net Wealth (Invest)',
            'Savings Invested (Paydown)',
            'Debt Balance (Paydown)',
            'Net Wealth (Paydown)',
            'Wealth Difference',
            'Net Wealth (Invest, Today)',
            'Net Wealth (Paydown, Today)',
            'Difference (Today)',
            'Better Choice',
        ],
        'data': rows,
    }

    # Break-even investment return.
    if tax_value < 1:
        break_even_return = debt_rate_value / (1 - tax_value)
    else:
        break_even_return = 0

    return {
        'Comparison': table,
        'Original Monthly Debt Payment': Qty(original_payment, 'USD/mo'),
        'Reduced Monthly Debt Payment': Qty(reduced_payment, 'USD/mo'),
        'Monthly Payment Saving': Qty(monthly_saving, 'USD/mo'),
        'After-Tax Investment Return': Qty(after_tax_investment_rate * 100, 'pct/yr'),
        'Break-Even Investment Return': Qty(break_even_return * 100, 'pct/yr'),
    }
