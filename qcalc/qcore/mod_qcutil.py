# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from qutil import replace_words, QThread
from qcore.qc_qty import Qty


def uprefs():
    return QThread.get_prefs()


def qformat_qstr(qstr: str, pref=None) -> str:
    qty = Qty(qstr)
    vstr, ustr = qformat(qty.val, qty.unit, pref)
    return f'{vstr} {ustr}'


def qformat_q(qty: Qty, pref=None) -> str:
    vstr, ustr = qformat(qty.val, qty.unit, pref)
    return f'{vstr} {ustr}'


def qformat_v(val, pref=None) -> str:
    vstr = qformat(val, pref)
    return vstr


def qformat(val, unit=None, pref=None) -> None | str | list[str]:
    # | value and quantity formatter
    if val is None:
        return val if unit is None else [val, unit.name()]

    if pref is None:
        pref = uprefs()

    is_cur = False
    funame = ''
    if unit is not None:
        dim = unit.dimension
        has_cur = 'C' in dim  # | e.g. km/USD
        is_cur = 'C' in dim and 'C-' not in dim  # | e.g. km/USD is not a currency

        if has_cur:
            val, funame = replace_UNC(val, unit.name(), pref)
        else:
            funame = unit.name()

        dec = pref['currency_decimal'] if is_cur else pref['qty_decimal']
    else:
        dec = pref['decimal']

    if pref['ignore_decimal_format']:
        return str(val) if unit is None else [str(val), funame]

    tsep = ',' if pref['thousands_separator'] else ''
    if (int(val) == val and abs(val) <= 1e16) and not is_cur:
        fg = 'f'
        dec = 0
    elif (max(pref['exponent_threshold_min'], 10 ** -dec) < abs(val) < pref['exponent_threshold_max']) or is_cur:
        fg = 'f'
    elif 1e-16 <= abs(val) <= 1e16:
        fg = 'e'
    else:
        fg = 'g'
        dec = dec + 1

    fv = '{:{tsep}.{dec}{fg}}'.format(val, tsep=tsep, dec=dec, fg=fg)
    if '.' in fv:
        if fg == 'f':
            fv = fv.rstrip('0').rstrip('.')
        elif fg == 'e':
            base, exponent = fv.split('e')
            base = base.rstrip('0').rstrip('.')
            fv = f"{base}e{exponent}"
    return fv if unit is None else [fv, funame]


def df_formatter(var):
    if isinstance(var, Qty):
        return qformat_q(var)
    elif isinstance(var, float) or isinstance(var, int):
        return qformat_v(var)
    else:
        return var


def replace_cur(val, uname, cur='UNC', pref=None):
    if pref is None:
        pref = uprefs()
    mycur = pref.get('defa_currency', 'UNC')
    if mycur == cur:
        return val, uname
    # | case-insensitive replacement of curency uom with preferred currency
    uname2 = replace_words(uname, [cur], mycur, False)
    cqty = Qty(val, uname, uname2)
    return cqty.val, cqty.uom


def replace_UNC(val, uname, pref=None):
    return replace_cur(val, uname, 'UNC', pref)


def ucur(qtystr: str, cur='UNC', pref=None, dec=None):
    # | convert a quanity string having currency (e.g. '120 km/usd') using user currency (e.g. '1.2 km/bdt')
    qty = Qty(qtystr)
    dim = qty.unit.dimension
    if 'C' not in dim:
        return qtystr
    val, uname = replace_cur(qty.val, qty.uom, cur, pref)
    if val:
        dec_places = ".2f" if dec is None else f".{dec}f"
        return f'{val:{dec_places}} {uname}'
    else:
        return f'@{uname}'


def to_ucur(qty: Qty, cur='UNC', pref=None):
    dim = qty.unit.dimension
    if 'C' not in dim:
        return qty
    val, uname = replace_cur(qty.val, qty.uom, cur, pref)
    return Qty(val, uname)


def _test():
    qtystr = '120km/inr'
    print(ucur(qtystr, 'INR'))
    print(to_ucur(Qty(qtystr), 'INR'))
    print(ucur('@ft/BDT', 'bdt'))
    qty = Qty('@bdt/s')
    print(replace_cur(qty.val, qty.uom, 'BDT'))


if __name__ == '__main__':
    # import sett
    _test()
