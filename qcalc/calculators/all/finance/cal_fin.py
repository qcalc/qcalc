# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import numpy as np
import pandas as pd
from qcore import Qty, qtable, qhtml, qformat_q
import numpy_financial as npf
from math import log10
from qutil import addcal_button
from calc import QCals

when_choices = {'type': 'radio', 'choices': {'1': 'Period Start', '0': 'Period End'}}
cashflow_choices = {'type': 'choice', 'choices': {'1': 'Incoming', '-1': 'Outgoing'}}


def _cf(v):
    return 'Incoming' if v > 0 else 'Outgoing'


def fincal__info():
    finp_choices = {
        'pv': 'Present Value',
        'fv': 'Future Value',
        'ir': 'Interest Rate',
        'ii': 'Interest Interval',
        'ri': 'Reinvestment Rate',
        'du': 'Duration',
        'pp': 'Periodic Payment',
        'pi': 'Payment Interval',
        'pw': 'Payment When',
        'la': 'Loan Amount',
    }
    fout_choices = {
        'pv': 'Present Value',
        'fv': 'Future Value',
        'ir': 'Interest Rate',
        # 'ii': 'Interest Interval',
        'np': 'Number of Periods',
        'pp': 'Periodic Payment',
        # 'pi': 'Payment Interval',
        # 'la': 'Loan Amount',
    }
    return {
        'title': 'Finance Calculator Helper',
        'schema': {
            'unknown_parameter': {'type': 'radio', 'choices': fout_choices},
            'known_parameters': {'type': 'checkboxselectmultiple', 'choices': finp_choices},
        },
        'calculate': 'Recommend',
        'kins': 'cur',
    }


def fincal(unknown_parameter='fv', known_parameters=['ir']):
    fin = {
        'cir': ('ir', {'pv', 'fv', 'du', 'ii'}),
        'cirp': ('ir', {'pv', 'fv', 'du', 'pp', 'pi', 'pw'}),
        'fv': ('fv', {'pv', 'ir', 'du', 'pp', 'pi', 'pw'}),
        'irrm': ('ir', {'ci', 'cf', 'ri'}),
        'irrn': ('ir', {'ci', 'cf'}),
        'npv': ('pv', {'ir', 'ci', 'cf'}),
        'ppmt': ('pp', {'pv', 'fv', 'ir', 'du', 'pi', 'pw'}),
        'pv': ('pv', {'fv', 'ir', 'du', 'pp', 'pi', 'pw'}),
        'invest': ('pp', {'fv', 'ir', 'np'}),
        'loan': ('pp', {'la', 'ir', 'np'}),
        'nper': ('np', {'pv', 'fv', 'ir', 'pp', 'pi', 'pw'}),
    }
    finp_matches = []
    fnames = []
    kvset = set(known_parameters)
    for func, fio in fin.items():
        if unknown_parameter == fio[0]:
            fnames.append(func)
            finp_matches.append(len(fio[1].intersection(kvset)))

    df = pd.DataFrame({'fname': fnames, 'params': finp_matches})
    result = 'No calculator found, please try again with different parameters'
    if len(df) > 0:
        df_sorted = df.sort_values(by='params', ascending=False)
        ln = len(df_sorted)
        if ln > 0:
            # df_sorted = df_sorted.head(2 if ln > 1 else ln)
            btns = []
            for fname in df_sorted['fname']:
                btns.append(qhtml(addcal_button(fname, QCals.cnode(fname).title)))
            result = [{'': b} for b in btns]
    return result


def circ__info():
    return {
        'title': 'Compound Interest Rate Conversion',
    }


def circ(interest_rate='12 pct/yr', interest_rate_for='mo'):
    irq = Qty(interest_rate)
    irfq = Qty(1, interest_rate_for)
    irv = irq.val / 100
    periods = irv / (irq * irfq)
    pir = 10 ** (log10(1 + irv) / periods) - 1
    return Qty(pir * 100, 'pct/' + irfq.uom)


def fv__info(__info):
    return {
        'title': 'Future Value (FV) of a Principal and Periodic Payment',
        'schema': {
            'payment_when': when_choices,
            'pv_part': cashflow_choices,
            'pp_part': cashflow_choices,
        }
    }


def fv(present_value: float = 100000.0, pv_part='-1',
       interest_rate='6 pct/yr',
       duration='5 yr',
       periodic_payment: float = 1000.0, pp_part='-1',
       payment_interval='mo',
       payment_when='1'):
    rate = circ(interest_rate, payment_interval).val / 100
    periods = int(Qty(duration) / Qty(1, payment_interval))
    if rate != 0.0:
        fval = -int(pv_part) * present_value * (1 + rate) ** periods \
               - int(pp_part) * periodic_payment * (1 + rate * int(payment_when)) * ((1 + rate) ** periods - 1) / rate
    else:
        fval = -int(pv_part) * present_value - int(pp_part) * periodic_payment * periods
    return {'Future Value': abs(fval), 'Cash Flow': _cf(fval)}


def pv__info():
    return {
        'title': 'Present Value (PV) of a Future Cash and Periodic Payment',
        'schema': {
            'payment_when': when_choices,
            'fv_part': cashflow_choices,
            'pp_part': cashflow_choices,
        }
    }


def pv(future_value: float = 100000.0, fv_part='1',
       interest_rate='6 pct/yr',
       duration='5 yr',
       periodic_payment: float = 1000.0, pp_part='-1',
       payment_interval='mo',
       payment_when='1'):
    rate = circ(interest_rate, payment_interval).val / 100
    periods: int = int(Qty(duration) / Qty(1, payment_interval))
    if rate != 0.0:
        pval = -int(fv_part) * future_value / ((1 + rate) ** periods) \
               - int(pp_part) * periodic_payment * (1 + rate * int(payment_when)) * (1 - (1 + rate) ** -periods) / rate
    else:
        pval = future_value - periodic_payment * periods
    return {'Present Value': abs(pval), 'Cash Flow': _cf(pval)}


def prjrank__info():
    return {
        'title': 'Project Ranking based on Cashflows',
    }


def prjrank(
    discount_rate='10 pct/yr',
    cashflow_interval='yr',
    cashflows: qtable = pd.DataFrame({
        'Project1': [-40000, 5000, 8000, 12000, 30000],
        'Project2': [-25000, 3000, 5000, 25000, ''],
        'Project3': [-10000, 2000, 6000, 7000, ''],
    })):
    periods = []
    npvs = []
    irrns = []
    ranks = []
    drate = circ(discount_rate, 'yr')
    maxnpv = -9e99
    bestprj = -1
    for i, prj in enumerate(cashflows.columns.tolist()):
        vals = []
        for v in cashflows[prj].tolist():
            if v:
                vals.append(v)
            else:
                break
        periods.append(len(vals))
        data = pd.DataFrame({'Cashflow': vals})
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
        'Project': cashflows.columns.values,
        'Period': periods,
        'NPV': npvs,
        'IRR': irrns,
        'Rank': ranks
    })
    if bestprj > -1:
        df._set_value(bestprj, 'Rank', 'Best')
    df['IRR'] = df['IRR'].apply(qformat_q)
    return {'Ranking': df}


def npv__info():
    return {
        'title': 'Net Present Value (NPV) of Future Cashflows',
    }


def npv(interest_rate='5 pct/yr',
        cashflow_interval='yr',
        cashflows: qtable = pd.DataFrame({'Cashflow': [-40000, 5000, 8000, 12000, 30000]})
        ):
    rate = circ(interest_rate, cashflow_interval).val / 100
    npv_val = np.sum([float(cf) / (1 + rate) ** i for i, cf in enumerate(cashflows['Cashflow'])])
    return {
        'Net Present Value': npv_val
    }


def irrn__info():  # name conflicts with Iranian Rial IRR
    return {
        'title': 'Internal Rate of Return (IRR)',
        'step2': [
            {'step': 'run', 'func': 'npv', 'caption': 'Net Present Value',
             'spec': {'cashflows': 'cashflows'}
             },
        ],
    }


def irrn(cashflow_interval='yr',
         cashflows: qtable = pd.DataFrame({'Cashflow': [-40000, 5000, 8000, 12000, 30000]})
         ):
    cfiq = Qty(1, cashflow_interval)
    values = cashflows['Cashflow'].astype(float)
    irr_val = npf.irr(values) * 100  # pct/intreval
    irr_str = f'{irr_val} pct/{cfiq.uom}'
    interest_rate_for = 'yr'
    irr_fq = circ(irr_str, interest_rate_for)
    return {
        'Periodic Interest Rate': Qty(irr_str),
        'Annual Interest Rate': irr_fq
    }


def irrm__info():
    return {
        'title': 'Modified Internal Rate of Return (IRRM)',
    }


def irrm(cashflow_interval='yr',
         cashflows: qtable = pd.DataFrame({'Cashflow': [-40000, 5000, 8000, 12000, 30000]}),
         finance_rate='10 pct/yr',
         reinvestment_rate='12 pct/yr'
         ):
    cfiq = Qty(1, cashflow_interval)
    finance_rate_p = circ(finance_rate, cashflow_interval).val / 100
    reinvestment_rate_p = circ(reinvestment_rate, cashflow_interval).val / 100
    values = cashflows['Cashflow'].astype(float)
    mirr_val = npf.mirr(values, finance_rate_p, reinvestment_rate_p) * 100
    mirr_str = f'{mirr_val} pct/{cfiq.uom}'
    interest_rate_for = 'yr'
    mirr_fq = circ(mirr_str, interest_rate_for)
    return {
        'Periodic Interest Rate': Qty(mirr_str),
        'Annual Interest Rate': mirr_fq
    }


def cir__info():
    return {
        'title': 'Compound Interest Rate without Periodic Payment',
    }


def cir(present_value: float = 100.0, future_value: float = 200.0,
        duration='6 yr', interest_interval='mo'):
    cfiq = Qty(1, interest_interval)
    periods = int(Qty(duration) / Qty(1, interest_interval))
    cir_val = ((future_value / present_value) ** (1 / periods) - 1) * 100  # pct
    cir_str = f'{cir_val} pct/{cfiq.uom}'
    interest_rate_for = 'yr'
    cir_fq = circ(cir_str, interest_rate_for)
    return {
        'Periodic Interest Rate': Qty(cir_str),
        'Annual Interest Rate': cir_fq
    }


def bond__info():
    return {
        'title': 'Bond Pricing',
    }


# Bond Pricing
def bond(face_value: float = 1000.0,
         coupon_rate='5 pct/yr',
         interest_payment_interval='halfyr',
         duration='2 yr',
         interest_rate='3 pct/yr'):
    ipiq = Qty(1, interest_payment_interval)
    coupon_rate_v = Qty(coupon_rate) * ipiq
    interest_rate_v = Qty(interest_rate) * ipiq
    period_n = int(Qty(duration) / ipiq)
    bond_price = 0
    for i in range(1, period_n + 1):
        bond_price += (coupon_rate_v * face_value) / (1 + interest_rate_v) ** i
    bond_price += face_value / (1 + interest_rate_v) ** period_n
    return {
        'Bond Price': bond_price
    }


# # Capital Asset Pricing Model (CAPM)
# def capital_asset_pricing_model(risk_free_rate, beta, market_return):
#     return risk_free_rate + beta * (market_return - risk_free_rate)

def cirp__info():
    return {
        'title': 'Compound Interest Rate with Periodic Payment',
        'schema': {
            'payment_when': when_choices,
            'pv_part': cashflow_choices,
            'fv_part': cashflow_choices,
            'pp_part': cashflow_choices,
        }
    }


def cirp(present_value: float = 100000.0, pv_part='-1',
         future_value: float = 200000.0, fv_part='1',
         duration='5 yr',
         periodic_payment: float = 1000.0, pp_part='-1',
         payment_interval='mo',
         payment_when='1',
         starting_guess='6.0 pct/yr',
         tolerance=0.00001,
         maximum_iteration=100):
    perq = Qty(1, payment_interval)
    periods: int = int(Qty(duration) / perq)
    guess = Qty(starting_guess) * perq
    irate_val = npf.rate(periods, int(pp_part) * periodic_payment, int(pv_part) * present_value,
                         int(fv_part) * future_value, int(payment_when), guess, tolerance, maximum_iteration)
    irate_str = f"{irate_val * 100} pct/{perq.uom}"
    irate_period = Qty(irate_str)
    irate_yr = circ(irate_str, 'yr')
    return {
        'Periodic Interest Rate': irate_period,
        'Annual Interest Rate': irate_yr
    }


def ppmt__info():
    return {
        'title': 'Periodic Payment',
        'schema': {
            'payment_when': when_choices,
            'pv_part': cashflow_choices,
            'fv_part': cashflow_choices,
        }
    }


def ppmt(present_value: float = 100000.0, pv_part='-1',
         future_value: float = 200000.0, fv_part='1',
         interest_rate='6 pct/yr',
         duration='5 yr',
         payment_interval='mo',
         payment_when='1'):
    perq = Qty(1, payment_interval)
    periods: int = int(Qty(duration) / perq)
    irate_period = Qty(interest_rate) * perq
    ppmt_val = npf.pmt(irate_period, periods, int(pv_part) * present_value, int(fv_part) * future_value,
                       int(payment_when))
    return {
        'Periodic Payment': abs(ppmt_val),
        'Cash Flow': _cf(ppmt_val)
    }


def nper__info():
    return {
        'title': 'Number of Periodic Payments',
        'schema': {
            'payment_when': when_choices,
            'pv_part': cashflow_choices,
            'fv_part': cashflow_choices,
            'pp_part': cashflow_choices,
        }
    }


def nper(present_value: float = 100000.0, pv_part='1',
         future_value: float = 0, fv_part='1',
         interest_rate='6 pct/yr',
         periodic_payment: float = 1000.0, pp_part='-1',
         payment_interval='mo',
         payment_when='1'):
    rate = circ(interest_rate, payment_interval).val / 100
    periods = npf.nper(rate, int(pp_part) * periodic_payment, int(pv_part) * present_value,
                       int(fv_part) * future_value, int(payment_when))
    return {
        'Number of Periods': periods,
        'Number of Years': Qty(periods, payment_interval).to('yr'),
        'Total Payment': periods * periodic_payment
    }


def loan__info():
    return {
        'title': 'Periodic Payment for a Loan'
    }


def loan(loan_amount: float = 100000,
         interest_rate='6.0 pct/yr',
         number_of_periods='12.0 mo'):
    number_of_periods = Qty(number_of_periods)
    rate_per_period = Qty(interest_rate, '1/' + number_of_periods.uom)
    payment_per_period = (rate_per_period * loan_amount) / (1 - (1 + rate_per_period.val) ** (-number_of_periods.val))
    total_payment = payment_per_period * number_of_periods
    return {'payment_per_period': payment_per_period, 'total_payment': total_payment}


def invest__info(): return {'title': 'Periodic Payment for a Future Cash'}


def invest(future_value: float = 100000,
           interest_rate='6.0 pct/yr',
           number_of_periods='12.0 mo'):
    number_of_periods = Qty(number_of_periods)
    rate_per_period = Qty(interest_rate, '1/' + number_of_periods.uom)
    payment_per_period = (rate_per_period * future_value) / ((1 + rate_per_period.val) ** number_of_periods.val - 1)
    total_payment = payment_per_period * number_of_periods
    return {'payment_per_period': payment_per_period, 'total_payment': total_payment}
