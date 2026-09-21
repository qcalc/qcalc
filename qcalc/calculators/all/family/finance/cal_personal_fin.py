# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from datetime import datetime
from qcore import qfunc
from calculators.all.general.file import csv_reader
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
    }


def ipbal(csv_file: qfunc = csv_reader,
          initial_balance=0.0, debit_interest_rate=9.0, credit_interest_rate=3.0, date_format="%d-%b-%y"):
    df = csv_file['table']
    return calculate_periodic_interest(df, initial_balance, debit_interest_rate, credit_interest_rate, date_format)

if __name__ == '__main__':
    # The CSV file should have columns: 'Date', 'Deposit', 'Withdrawal'
    import qenv
    import pandas as pd

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
