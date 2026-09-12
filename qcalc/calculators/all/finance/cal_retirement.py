# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import math

from qcore import Qty
from calc import QResults
from qapi import qdf
from calculators.all.finance.cal_fin import circ


def retirement_sustainability(
    portfolio='500000 USD',
    withdrawal='30000 USD/yr',
    investment_return='7 pct/yr',
    inflation='3 pct/yr',
    investment_tax='15 pct',
    retirement_period='25 yr',
    withdrawal_period='yr',
    withdrawal_when='end',
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
    period_unit = Qty(1, withdrawal_period).uom
    withdrawal_unit = f'{to_cur}/{period_unit}'
    withdrawal_amount = q_withdrawal.to(withdrawal_unit).val
    initial_withdrawal = withdrawal_amount

    gross_return = circ(q_investment_return, period_unit).val / 100
    inflation_rate = circ(q_inflation, period_unit).val / 100
    tax_rate = q_investment_tax.to('pct').val / 100
    periods = int(round(q_retirement_period / Qty(1, period_unit)))

    balance = portfolio_value
    rows = []
    depletion_period = None

    for period in range(1, periods + 1):
        starting_balance = balance

        if starting_balance <= 0:
            depletion_period = Qty(period, period_unit)
            break

        if period > 1:
            withdrawal_amount *= 1 + inflation_rate

        invested_balance = starting_balance
        if withdrawal_when == 'start':
            invested_balance -= withdrawal_amount

        investment_gain = invested_balance * gross_return
        investment_tax_amount = investment_gain * tax_rate
        after_tax_gain = investment_gain - investment_tax_amount

        ending_balance = invested_balance + after_tax_gain
        if withdrawal_when == 'end':
            ending_balance -= withdrawal_amount

        ending_balance = max(0, ending_balance)

        rows.append([
            period,
            Qty(starting_balance, to_cur),
            Qty(investment_gain, to_cur),
            Qty(investment_tax_amount, to_cur),
            Qty(withdrawal_amount, withdrawal_unit),
            Qty(ending_balance, to_cur),
        ])

        balance = ending_balance

        if balance <= 0:
            depletion_period = Qty(period, period_unit)
            break

    net_return = gross_return * (1 - tax_rate)

    if periods > 0:
        pv_factor = sum(
            (1 + inflation_rate) ** period /
            (1 + net_return) ** (
                period + (1 if withdrawal_when == 'end' else 0)
            )
            for period in range(periods)
        )
        sustainable_withdrawal = (
            portfolio_value / pv_factor
            if pv_factor > 0 else 0
        )
    else:
        sustainable_withdrawal = 0

    initial_withdrawal_rate = (
        initial_withdrawal / portfolio_value * 100
        if portfolio_value else None
    )
    zero_return_zero_inflation_depletion_period = (
        Qty(math.ceil(portfolio_value / initial_withdrawal), period_unit)
        if portfolio_value and initial_withdrawal > 0 else None
    )

    projection = {
        'data': rows,
        'columns': [
            'Period',
            'Starting Balance',
            'Investment Return',
            'Investment Tax',
            'Withdrawal',
            'Ending Balance',
        ],
    }

    df = qdf(projection)

    chart = QResults.df2chart(
        df,
        x_column='Period',
        y_columns=['Starting Balance', 'Ending Balance'],
        chart_title='Projection',
        chart_type='lines',
        ylabel='Balance',
    )

    return {
        'After-Tax Return': Qty(net_return * 100, f'pct/{period_unit}'),
        'Initial Withdrawal Rate': (
            Qty(initial_withdrawal_rate, 'pct')
            if initial_withdrawal_rate is not None
            else None
        ),
        'Sustainable Withdrawal': Qty(sustainable_withdrawal, withdrawal_unit),
        'Final Balance': Qty(balance, to_cur),
        'Depletion Period': depletion_period,
        'Depletion Period (0% Return, 0% Inflation)': (
            zero_return_zero_inflation_depletion_period
        ),
        'Chart': chart,
        'Projection': projection,
    }


def retirement_sustainability__info():
    return {
        'title': 'Retirement Withdrawal Sustainability',
        'desc': (
            'Estimate whether a retirement portfolio can sustain '
            'inflation-adjusted withdrawals at a selected interval, using '
            'compound periodic returns, tax on investment gains, and '
            'start-of-period or end-of-period withdrawal timing.'
        ),
        'interactive': True,
        'schema':{
            'withdrawal_when': {
                'type': 'choice',
                'choices': ['start', 'end'],
                'default': 'end',
                'help_text': 'Specify whether withdrawals occur at the start or end of each period.'
            }
        },
        'tags': (
            'finance, retirement, investment, withdrawal, '
            'portfolio, sustainability'
        ),
    }
