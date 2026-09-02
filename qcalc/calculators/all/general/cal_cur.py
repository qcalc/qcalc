# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from qcore import Qty, qhtml
from qutil import nzv
from calc import QCals, cur_loader


def cur__info():
    return {
        'title': 'Simple Currency Converter',
        'schema': {'amount': {'type': 'textarea'}}
    }


def cur(amount: str = '1.0', from_currency='USD', to_currency='UNC'):
    """Simple Currency Converter

    Args:
        amount: Amount to be converted, you can enter simple expression as well (e.g. 92/3+15)
        from_currency: Currency to be converted from
        to_currency: Currency to be converted to.

    Return:
        returns converted amount
    """
    xcur = Qty(QCals.safe_eval(amount), from_currency)
    ycur = xcur.to(to_currency)
    return {
        'Converted Amount': ycur,
        'Currency Rate as of': qhtml(cur_loader.cur_as_of())
    }


def curx__info():
    return {
        'title': 'Exchange Currency',
        'anyof': {
            '1': {'fields': ['one_buy_currency_equals', 'one_sale_currency_equals']},
            '2': {'fields': ['buy_amount', 'sale_amount']}
        },
        'row': ['1-2', '3-4', '5-6']
    }


def curx(
    buy_amount: float = 300,
    sale_amount: float = None,
    buy_currency='usd',
    sale_currency='unc',
    one_buy_currency_equals: float = 1.0,
    one_sale_currency_equals: float = None,
    exchange_fee='@unc'
    # express_in_currencies: str = ''
):
    exchange_fee = nzv(Qty(exchange_fee, sale_currency).val)
    if buy_amount is not None:
        if one_buy_currency_equals is not None:
            samt = buy_amount * one_buy_currency_equals + exchange_fee
        else:
            samt = buy_amount / one_sale_currency_equals + exchange_fee
        qsale_amt = Qty(samt, sale_currency)
        qbuy_amt = Qty(buy_amount, buy_currency)
    else:
        if one_buy_currency_equals is not None:
            bamt = (sale_amount - exchange_fee) / one_buy_currency_equals
        else:
            bamt = (sale_amount - exchange_fee) * one_sale_currency_equals
        qbuy_amt = Qty(bamt, buy_currency)
        qsale_amt = Qty(sale_amount, sale_currency)

    # calculate based on qcalc rate
    xrate = '{:.3f}'.format(Qty(f'1 {buy_currency}', sale_currency).val)
    qbuy_amt2 = Qty(qsale_amt).to(buy_currency)
    # important: qbuy_amt2 = qsale_amt followed by qbuy_amt2.to will also convert qsale_amt

    diff = round((qbuy_amt.val - qbuy_amt2.val) * 100 / qbuy_amt2.val, 2)
    lg = 'loss' if diff < 0 else 'gain'
    return {
        'Purchased at Exchange Rate': qbuy_amt,
        # 'Expressed Currency': qamtx,
        'If Purchased at qCalc Rate': qbuy_amt2,
        'qCalc Rate is': qhtml(f'1 {buy_currency.upper()} = {xrate} {sale_currency.upper()}'),
        'qCalc Rate as of': qhtml(cur_loader.cur_as_of()),
        'Difference': qhtml(f'{abs(diff)}% ({lg})'),
        'Sold Amount': qsale_amt,
    }
