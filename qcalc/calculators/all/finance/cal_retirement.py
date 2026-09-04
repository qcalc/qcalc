# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from qcore import Qty
from calc import df2chart
from qapi import qdf


def retirement_sustainability(
    portfolio='500000 USD',
    withdrawal='30000 USD/yr',
    investment_return='7 pct/yr',
    inflation='3 pct/yr',
    investment_tax='15 pct',
    retirement_period='30 yr',
):
    """
    Calculate retirement portfolio sustainability with inflation-adjusted
    withdrawals and tax on investment returns.
    """

    q_portfolio = Qty(portfolio)
    to_cur = q_portfolio.uom

    q_withdrawal = Qty(withdrawal)
    q_investment_return = Qty(investment_return)
    q_inflation = Qty(inflation)
    q_investment_tax = Qty(investment_tax)
    q_retirement_period = Qty(retirement_period)

    portfolio_value = q_portfolio.val
    annual_withdrawal = q_withdrawal.to(f'{to_cur}/yr').val

    gross_return = q_investment_return.to('pct/yr').val / 100
    inflation_rate = q_inflation.to('pct/yr').val / 100
    tax_rate = q_investment_tax.to('pct').val / 100
    years = int(round(q_retirement_period.to('yr').val))

    balance = portfolio_value
    withdrawal_amount = annual_withdrawal

    rows = []
    depletion_year = None

    for year in range(1, years + 1):
        starting_balance = balance

        if starting_balance <= 0:
            depletion_year = year
            break

        investment_gain = starting_balance * gross_return
        investment_tax_amount = investment_gain * tax_rate
        after_tax_gain = investment_gain - investment_tax_amount

        if year > 1:
            withdrawal_amount *= 1 + inflation_rate

        ending_balance = (
            starting_balance
            + after_tax_gain
            - withdrawal_amount
        )

        ending_balance = max(0, ending_balance)

        rows.append([
            year,
            Qty(starting_balance, to_cur),
            Qty(investment_gain, to_cur),
            Qty(investment_tax_amount, to_cur),
            Qty(withdrawal_amount, f'{to_cur}/yr'),
            Qty(ending_balance, to_cur),
        ])

        balance = ending_balance

        if balance <= 0:
            depletion_year = year
            break

    net_return = gross_return * (1 - tax_rate)

    if years > 0:
        if abs(net_return - inflation_rate) < 1e-12:
            sustainable_withdrawal = (
                portfolio_value * (1 + net_return) / years
            )
        else:
            growth_ratio = (
                (1 + inflation_rate) /
                (1 + net_return)
            )

            pv_factor = (
                (1 - growth_ratio ** years)
                / (1 - growth_ratio)
                / (1 + net_return)
            )

            sustainable_withdrawal = (
                portfolio_value / pv_factor
                if pv_factor > 0 else 0
            )
    else:
        sustainable_withdrawal = 0

    initial_withdrawal_rate = (
        annual_withdrawal / portfolio_value * 100
        if portfolio_value else None
    )

    projection = {
        'data': rows,
        'columns': [
            'Year',
            'Starting Balance',
            'Investment Return',
            'Investment Tax',
            'Withdrawal',
            'Ending Balance',
        ],
    }

    df = qdf(projection)

    chart = df2chart(
        df,
        x_column='Year',
        y_columns=['Starting Balance', 'Ending Balance'],
        chart_title='Projection',
        chart_type='lines',
        ylabel='Balance',
    )

    return {
        'After-Tax Return': Qty(net_return * 100, 'pct/yr'),
        'Initial Withdrawal Rate': (
            Qty(initial_withdrawal_rate, 'pct')
            if initial_withdrawal_rate is not None
            else None
        ),
        'Sustainable Withdrawal': Qty(
            sustainable_withdrawal,
            f'{to_cur}/yr',
        ),
        'Final Balance': Qty(balance, to_cur),
        'Depletion Year': depletion_year,
        'Projection': projection,
        'Chart': chart,
    }


def retirement_sustainability__info():
    return {
        'title': 'Retirement Withdrawal Sustainability',
        'desc': (
            'Determine whether a retirement portfolio can sustain '
            'inflation-adjusted withdrawals after tax on investment returns, '
            'and estimate the sustainable annual withdrawal.'
        ),
        'tags': (
            'finance, retirement, investment, withdrawal, '
            'portfolio, sustainability'
        ),
    }
