# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import pandas as pd
from qcore import QChart, Qty
from calc import QResults


def amort__info():
    return {
        'title': 'Amortization Schedule Calculation',
    }


def amort(loan_amount: float = 100000.0, annual_interest_rate: float = 5.0, loan_term_years: int = 10):
    monthly_interest_rate = annual_interest_rate / 12 / 100
    number_of_payments = loan_term_years * 12
    # Calculate monthly payment using the formula for an amortizing loan
    monthly_payment = (loan_amount * monthly_interest_rate) / (
        1 - (1 + monthly_interest_rate) ** -number_of_payments)

    amortization_schedule = []

    remaining_principal = loan_amount
    total_interest = 0
    total_principal = 0
    for payment_number in range(1, number_of_payments + 1):
        interest_payment = remaining_principal * monthly_interest_rate
        principal_payment = monthly_payment - interest_payment
        total_interest += interest_payment
        total_principal += principal_payment
        total_payment = total_interest + total_principal
        remaining_principal -= principal_payment

        amortization_schedule.append([
            payment_number,
            round(monthly_payment, 2),
            round(principal_payment, 2),
            round(interest_payment, 2),
            round(total_principal, 2),
            round(total_interest, 2),
            round(total_payment, 2),
            round(remaining_principal, 2)
        ])

    columns = [
        "Payment Number",
        "Monthly Payment",
        "Principal Payment",
        "Interest Payment",
        "Total Principal",
        "Total Interest",
        "Total Payment",
        "Remaining Principal"
    ]
    df = pd.DataFrame(amortization_schedule, columns=columns)

    chdata = QResults.df2chart_data(
        df, y_columns=["Total Principal", "Total Interest", "Total Payment", "Remaining Principal"])
    chart = QChart(aspect=1)
    chart.legend_loc_best = 'upper center'
    chart.render_lines(**chdata, ylabel='Amount', title='Amortization')

    for c in range(1, 8):
        df[columns[c]] = df[columns[c]].apply('{:,.2f}'.format)

    return {
        "Amortization Schedule": df,
        "Amortization Chart": chart
    }


def loan_prepay__info():
    return {
        'title': 'Loan Prepayment Savings',
        'desc': 'Estimate the interest and payoff time saved by adding an extra amount to every monthly payment.',
        'calculate': 'Calculate Savings',
        'schema': {
            'loan_amount': {'help_text': 'Original loan principal.'},
            'annual_interest_rate': {'help_text': 'Fixed annual interest rate.'},
            'loan_term_years': {'help_text': 'Original repayment term in years.'},
            'extra_monthly_payment': {
                'label': 'Extra Monthly Payment',
                'help_text': 'Additional principal paid with every scheduled monthly payment.',
            },
        },
        'kins': 'loan,amort',
        'tags': 'loan,mortgage,prepayment,interest,savings',
    }


def _loan_payoff(loan_value, monthly_rate, monthly_payment, extra_payment=0):
    balance = loan_value
    total_interest = 0
    months = 0

    while balance > 1e-8:
        interest = balance * monthly_rate
        payment = min(balance + interest, monthly_payment + extra_payment)
        principal = payment - interest
        if principal <= 0:
            raise ValueError('Monthly payment must be greater than the monthly interest.')
        balance = max(0, balance - principal)
        total_interest += interest
        months += 1

    return months, total_interest


def loan_prepay(
    loan_amount='300000 USD',
    annual_interest_rate='6 pct/yr',
    loan_term_years: int = 30,
    extra_monthly_payment='200 USD',
):
    loan = Qty(loan_amount)
    currency = loan.uom
    rate = Qty(annual_interest_rate, 'pct/yr')
    extra_payment = Qty(extra_monthly_payment, currency)

    if loan.val <= 0:
        raise ValueError('Loan amount must be greater than zero.')
    if loan_term_years <= 0:
        raise ValueError('Loan term must be greater than zero.')
    if rate.val < 0:
        raise ValueError('Annual interest rate cannot be negative.')
    if extra_payment.val < 0:
        raise ValueError('Extra monthly payment cannot be negative.')

    total_months = loan_term_years * 12
    monthly_rate = rate.val / 1200
    if monthly_rate == 0:
        monthly_payment = loan.val / total_months
    else:
        monthly_payment = (
            loan.val * monthly_rate
            / (1 - (1 + monthly_rate) ** -total_months)
        )

    original_months, original_interest = _loan_payoff(
        loan.val, monthly_rate, monthly_payment
    )
    prepay_months, prepay_interest = _loan_payoff(
        loan.val, monthly_rate, monthly_payment, extra_payment.val
    )
    saved_months = original_months - prepay_months
    saved_years, remaining_months = divmod(saved_months, 12)

    return {
        'Scheduled Monthly Payment': Qty(monthly_payment, currency),
        'Original Total Interest': Qty(original_interest, currency),
        'Prepayment Total Interest': Qty(prepay_interest, currency),
        'Interest Saved': Qty(original_interest - prepay_interest, currency),
        'Original Payoff Time': f'{original_months} months',
        'Prepayment Payoff Time': f'{prepay_months} months',
        'Time Saved': f'{saved_months} months ({saved_years} years, {remaining_months} months)',
    }


def real_return__info():
    return {
        'title': 'Real Return After Inflation and Tax',
        'desc': (
            'Calculate the investment return after tax and inflation, '
            'and compare nominal, after-tax and real returns.'
        ),
    }


def real_return(
    nominal_return='8 pct/yr',
    tax_rate='15 pct',
    inflation_rate='3 pct/yr',
):
    q_nominal_return = Qty(nominal_return)
    q_tax_rate = Qty(tax_rate)
    q_inflation_rate = Qty(inflation_rate)

    nominal = q_nominal_return.to('pct/yr').val / 100.0
    tax = q_tax_rate.to('pct').val / 100.0
    inflation = q_inflation_rate.to('pct/yr').val / 100.0

    # Return remaining after tax.
    after_tax_return = nominal * (1.0 - tax)

    # Real return after inflation.
    real_return_after_tax = ((1.0 + after_tax_return) / (1.0 + inflation)) - 1.0

    # Real return before tax.
    real_return_before_tax = ((1.0 + nominal) / (1.0 + inflation)) - 1.0

    # Reduction caused by tax.
    tax_impact = nominal - after_tax_return

    # Reduction from after-tax nominal return to real after-tax return.
    inflation_impact = (
        after_tax_return -
        real_return_after_tax
    )

    return {
        'After-Tax Return': Qty(after_tax_return * 100, 'pct/yr'),
        'Real Return Before Tax': Qty(real_return_before_tax * 100, 'pct/yr'),
        'Real Return After Tax': Qty(real_return_after_tax * 100, 'pct/yr'),
        'Tax Impact': Qty(tax_impact * 100, 'pct/yr'),
        'Inflation Impact': Qty(inflation_impact * 100, 'pct/yr'),
    }
