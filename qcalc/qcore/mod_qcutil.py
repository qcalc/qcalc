# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from qutil import replace_words, QThread
from qcore.qc_qty import Qty, str_to_qty
import math
import numbers
from qvars import qc_gpref as gs


def thread_prefs():
    # Thread-local effective preferences for the current execution context.
    # Safe fallback behavior: returns global defaults when thread-local prefs
    # were not set yet (e.g. some utility/test call paths).
    return QThread.get_prefs()


def request_prefs():
    # Request-scoped preferences for the active HTTP request.
    # More specific than thread_prefs() during form/view rendering because
    # request.pref includes per-request overrides.
    request = QThread.get_req()
    return request.pref if request is not None else thread_prefs()


def qformat_q(qty: Qty | str, val_only=False) -> str:
    if isinstance(qty, str):
        qty = Qty(qty)
    vstr, ustr = qformat(qty.val, qty.unit)
    return f'{vstr} {ustr}' if not val_only else vstr


def qformat_v(val) -> str:
    vstr = qformat(val)
    return vstr


def qformat(val, unit=None, pref=None) -> None | str | list[str]:
    # | value and quantity formatter
    if val is None or (isinstance(val, float) and math.isnan(val)):
        return val if unit is None else [val, unit.name()]

    # qformat() is used from request and non-request execution paths;
    # thread_prefs() keeps the fallback safe when no HTTP request is active.
    if pref is None:
        pref = thread_prefs()

    # Some call paths set only a subset of preferences in thread-local storage.
    # Merge with global defaults so formatter keys are always available.
    if isinstance(pref, dict):
        pref = {**gs, **pref}
    else:
        pref = gs

    is_cur = False
    funame = ''
    if unit is not None:
        dim = unit.dimension
        has_cur = 'C' in dim  # | e.g. km/USD
        is_cur = 'C' in dim and 'C-' not in dim  # | e.g. km/USD is not a currency

        if has_cur:
            val, funame = replace_UNC(val, unit.name(), pref_cur=pref.get('defa_currency', 'UNC'))
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


def df_formatter(var, unit_hint=None, val_only=False):
    if isinstance(var, Qty):
        return qformat_q(var, val_only=val_only)

    if isinstance(var, numbers.Complex) and not isinstance(var, numbers.Real):
        real = float(var.real)
        imag = float(var.imag)
        tol = 1e-12

        if abs(real) <= tol:
            return f"{qformat_v(imag)}j"
        if abs(imag) <= tol:
            return qformat_v(real)

        sign = '+' if imag >= 0 else '-'
        return f"{qformat_v(real)}{sign}{qformat_v(abs(imag))}j"

    if isinstance(var, str):
        qty = str_to_qty(var.strip())
        if qty is not None:
            if unit_hint:
                qty = Qty(qty, unit_hint)
            return qformat_q(qty, val_only=val_only)
        try:
            var = float(var.strip())
        except Exception:
            return var

    if isinstance(var, numbers.Real) and not isinstance(var, bool):
        if unit_hint:
            return qformat_q(Qty(var, unit_hint), val_only=val_only)
        return qformat_v(var)
    return var  # preserve None


def replace_cur(val, uname, cur='UNC', pref_cur: str | None = None):
    """Replace a placeholder/source currency in a unit string with user preference.

    Args:
        val: Quantity numeric value.
        uname: Source unit string that may contain currency unit ``cur``.
        cur: Currency unit to replace (default ``'UNC'``).
        pref_cur: Optional preferred currency code (e.g. ``"EUR"``).
            When omitted, ``thread_prefs()`` is used.

    Returns:
        A ``(value, unit_name)`` tuple converted to the preferred currency unit.
        If preferred currency equals ``cur``, returns the input ``(val, uname)``.
    """
    if pref_cur is None:
        # This helper is used from request and non-request paths; thread_prefs()
        # provides a safe default currency preference in both contexts.
        pref = thread_prefs()
        mycur = pref.get('defa_currency', 'UNC')
    else:
        mycur = pref_cur

    if mycur == cur:
        return val, uname
    # | case-insensitive replacement of curency uom with preferred currency
    uname2 = replace_words(uname, [cur], mycur, False)
    cqty = Qty(val, uname, uname2)
    return cqty.val, cqty.uom


def replace_UNC(val, uname, pref_cur: str | None = None):
    """Replace ``UNC`` currency token with the user's preferred currency."""
    return replace_cur(val, uname, 'UNC', pref_cur)


def to_ucur(qty: Qty | str, cur='UNC', pref_cur: str | None = None):
    """Convert currency token to preferred currency for Qty or quantity strings.

    If ``qty`` is a ``Qty`` object, returns a ``Qty``.
    If ``qty`` is a quantity string, returns a quantity string.
    Non-currency dimensions are returned unchanged.
    """
    is_qty_obj = isinstance(qty, Qty)
    qty_obj = qty if is_qty_obj else Qty(qty)
    dim = qty_obj.unit.dimension
    if 'C' not in dim:
        return qty
    val, uname = replace_cur(qty_obj.val, qty_obj.uom, cur, pref_cur)
    if is_qty_obj:
        return Qty(val, uname)
    if val:
        return f'{val} {uname}'
    return f'@{uname}'
