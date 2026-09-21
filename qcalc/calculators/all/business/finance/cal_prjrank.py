# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import pandas as pd
from qcore import qtable, qformat_q, as_qtable
from calculators.all.finance import circ, npv, irrn


def prjrank__info():
    return {
        'title': 'Project Ranking based on Cashflows',
    }


def prjrank(
    discount_rate='10 pct/yr',
    cashflow_interval='yr',
    cashflows: qtable = pd.DataFrame({
        'Period': [1, 2, 3, 4, 5],
        'Project1': [-40000, 5000, 8000, 12000, 30000],
        'Project2': [-25000, 3000, 5000, 25000, ''],
        'Project3': [-10000, 2000, 6000, 7000, ''],
    })):
    cashflows = as_qtable(cashflows)
    counts = []
    end_periods = []
    npvs = []
    irrns = []
    ranks = []
    drate = circ(discount_rate, 'yr')
    maxnpv = -9e99
    bestprj = -1
    cols = cashflows.columns.tolist()
    if len(cols) < 2:
        raise ValueError('prjrank expects Period plus at least one project column in cashflows table.')
    if str(cols[0]).lower() != 'period':
        raise ValueError(f"prjrank expects first cashflows column to be 'Period'. Found: {cols[0]}.")
    period_col = cols[0]
    prj_columns = cols[1:]
    prd_all = pd.to_numeric(cashflows[period_col], errors='coerce')

    for i, prj in enumerate(prj_columns):
        cf = pd.to_numeric(cashflows[prj], errors='coerce')
        data = pd.DataFrame({'Period': prd_all, 'Cashflow': cf}).dropna()
        if len(data) == 0:
            raise ValueError(f"prjrank found no numeric cashflow rows for project '{prj}'.")
        if data['Period'].duplicated().any():
            raise ValueError(f"prjrank found duplicate Period values in project '{prj}'.")
        if not data['Period'].is_monotonic_increasing:
            raise ValueError(f"prjrank expects Period values to be increasing for project '{prj}'.")
        vals = data['Cashflow'].tolist()
        counts.append(len(vals))
        end_periods.append(data['Period'].iloc[-1])
        prj_npv = npv(discount_rate, cashflow_interval, data)['Net Present Value']
        prj_irrn = irrn(cashflow_interval, data)['Annual Interest Rate']
        npvs.append(prj_npv)
        irrns.append(prj_irrn)

        if prj_npv < 0 or prj_irrn.val < drate.val:
            ranks.append('Bad')
        else:
            ranks.append('OK')
            if maxnpv < prj_npv:
                maxnpv = prj_npv
                bestprj = i
    df = pd.DataFrame({
        'Project': prj_columns,
        'Count': counts,
        'End Period': end_periods,
        'NPV': npvs,
        'IRR': irrns,
        'Rank': ranks
    })
    if bestprj > -1:
        df._set_value(bestprj, 'Rank', 'Best')
    df['IRR'] = df['IRR'].apply(qformat_q)
    return {'Ranking': df}
