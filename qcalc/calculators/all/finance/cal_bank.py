# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

# import sett
import pandas as pd
from datetime import datetime
from qcore import qfunc, QChart
from calculators.all.general.file.cal_file import csv_reader
from calc import df_qchart_data_yy
from qutil import demo_url


def calculate_days_between_dates(start_date, end_date, date_format):  # "%Y-%m-%d"
    start_date = datetime.strptime(start_date, date_format)
    end_date = datetime.strptime(end_date, date_format)
    return (end_date - start_date).days


def calculate_periodic_interest(df, initial_balance, debit_rate, credit_rate, date_format="%d-%b-%y"):
    balance = initial_balance
    for index in range(len(df)):
        current_row = df.iloc[index]
        next_row = df.iloc[index + 1] if index + 1 < len(df) else None
        deposit = current_row['Deposit'] if current_row['Deposit'] else 0
        withdrawl = current_row['Withdrawl'] if current_row['Withdrawl'] else 0
        balance = balance + deposit - withdrawl
        days = calculate_days_between_dates(current_row['Date'], next_row['Date'],
                                            date_format) if next_row is not None else 0
        dr_balance = abs(balance * days) if balance < 0 else 0
        cr_balance = balance * days if balance > 0 else 0
        df.at[index, 'Balance'] = balance
        df.at[index, 'Days'] = days
        df.at[index, 'DR Interest'] = dr_balance * debit_rate / 36500.0
        df.at[index, 'CR Interest'] = cr_balance * credit_rate / 36500.0

    dr_interest = df['DR Interest'].sum()
    cr_interest = df['CR Interest'].sum()
    interest_earned = cr_interest - dr_interest
    df['DR Interest'] = df['DR Interest'].apply(lambda x: f"{x:.2f}")
    df['CR Interest'] = df['CR Interest'].apply(lambda x: f"{x:.2f}")

    # df.at['Total', 'DR Interest'] = dr_interest
    # df.at['Total', 'CR Interest'] = cr_interest
    # # | Change the data type of the last row to object and fill it with empty strings for NaN values
    # df.iloc[-1] = df.iloc[-1].astype(object).fillna('')
    return {
        'Total DR Interest': round(dr_interest, 2),
        'Total CR Interest': round(cr_interest, 2),
        'Total Interest Earned': round(interest_earned, 2),
        'Calculation': df
    }


def ipbal__input(_kwargs):
    return {
        'csv_file--csv_url': demo_url('ipbal.csv'),
    }


def ipbal__info():
    return {
        'title': 'Interest for Periodic Balance',
        'col': ['1-2', '3-5']
    }


def ipbal(csv_file: qfunc = csv_reader,
          initial_balance=0.0, debit_interest_rate=9.0, credit_interest_rate=3.0, date_format="%d-%b-%y"):
    df = csv_file['table']
    return calculate_periodic_interest(df, initial_balance, debit_interest_rate, credit_interest_rate, date_format)


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

    chdata = df_qchart_data_yy(
        df, rkeys=["Total Principal", "Total Interest", "Total Payment", "Remaining Principal"])
    chart = QChart(aspect=1)
    chart.legend_loc_best = 'upper center'
    chart.render_lines(**chdata)

    for c in range(1, 8):
        df[columns[c]] = df[columns[c]].apply('{:,.2f}'.format)
    # df.set_index("Payment Number", inplace=True)

    return {
        "Amortization Schedule": df,
        "Amortization Chart": chart
    }


if __name__ == '__main__':
    # The CSV file should have columns: 'Date', 'Deposit', 'Withdrawal'
    import qenv

    csv_file = qenv.ROOT_DIR.path('qsite/static/demo/ipbal.csv')
    print(csv_file)
    df = pd.read_csv(csv_file, delimiter=',')
    print(df)
    debit_interest_rate = 6
    credit_interest_rate = 10
    initial_balance = 0.00
    res = calculate_periodic_interest(df, initial_balance, debit_interest_rate, credit_interest_rate)
    print(f'Total Interest Earned: {res['Interest Earned']}')
    print(res['Calculation'])
