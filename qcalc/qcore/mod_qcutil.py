# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from qutil import replace_words, QThread
from qcore.qc_qty import Qty
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


class QCurrency:
    """Converts currency tokens in units to one preferred currency.

    ``pref_cur`` defaults to the user's ``defa_currency`` from ``thread_prefs()``,
    which is read once per instance. Create instances per request, not at import.
    """

    def __init__(self, pref_cur: str | None = None):
        # thread_prefs() gives a safe default in request and non-request paths.
        self.pref_cur = pref_cur if pref_cur is not None else thread_prefs().get('defa_currency', 'UNC')

    def convert(self, val, uname, cur='UNC'):
        """Return ``(value, unit_name)`` with ``cur`` replaced by the preferred currency."""
        if self.pref_cur == cur:
            return val, uname
        # | case-insensitive replacement of curency uom with preferred currency
        uname2 = replace_words(uname, [cur], self.pref_cur, False)
        cqty = Qty(val, uname, uname2)
        return cqty.val, cqty.uom

    def to_ucur(self, qty: Qty | str, cur='UNC'):
        """Convert currency token of a ``Qty`` (returns ``Qty``) or quantity string (returns str).

        Non-currency dimensions are returned unchanged.
        """
        is_qty_obj = isinstance(qty, Qty)
        qty_obj = qty if is_qty_obj else Qty(qty)
        if 'C' not in qty_obj.unit.dimension:
            return qty
        val, uname = self.convert(qty_obj.val, qty_obj.uom, cur)
        if is_qty_obj:
            return Qty(val, uname)
        return f'{val} {uname}' if val else f'@{uname}'


class QFormatter:
    """Value/quantity formatter bound to one set of preferences.

    ``pref`` defaults to ``thread_prefs()``. It is merged with global defaults once,
    since some call paths set only a subset of preferences.
    """

    def __init__(self, pref=None):
        if pref is None:
            pref = thread_prefs()
        self.pref = {**gs, **pref} if isinstance(pref, dict) else gs
        self.currency = QCurrency(self.pref.get('defa_currency', 'UNC'))

    def format(self, val, unit=None, thousands_separator=None) -> None | str | list[str]:
        """Format a value (returns str) or a value with unit (returns ``[value, unit_name]``)."""
        if val is None or (isinstance(val, float) and math.isnan(val)):
            return val if unit is None else [val, unit.name()]

        pref = self.pref
        is_cur = False
        funame = ''
        if unit is not None:
            dim = unit.dimension
            has_cur = 'C' in dim  # | e.g. km/USD
            is_cur = 'C' in dim and 'C-' not in dim  # | e.g. km/USD is not a currency

            if has_cur:
                val, funame = self.currency.convert(val, unit.name())
            else:
                funame = unit.name()

            dec = pref['currency_decimal'] if is_cur else pref['qty_decimal']
        else:
            dec = pref['decimal']

        if isinstance(val, (int, float)) and not math.isfinite(val):
            sval = 'inf' if val > 0 else '-inf'
            return sval if unit is None else [sval, funame]

        if pref['ignore_decimal_format']:
            return str(val) if unit is None else [str(val), funame]

        if thousands_separator is None:
            thousands_separator = pref['thousands_separator']
        tsep = ',' if thousands_separator else ''
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

    def value(self, val) -> str:
        return self.format(val)

    def qty(self, qty: Qty | str, val_only=False, thousands_separator=None) -> str:
        if isinstance(qty, str):
            qty = Qty(qty)
        vstr, ustr = self.format(qty.val, qty.unit, thousands_separator)
        return f'{vstr} {ustr}' if not val_only else vstr

    def df(self, var, unit_hint=None, val_only=False):
        """Format any dataframe cell: Qty, complex, quantity string, number; others unchanged."""
        if isinstance(var, Qty):
            return self.qty(var, val_only=val_only)

        if isinstance(var, numbers.Complex) and not isinstance(var, numbers.Real):
            real = float(var.real)
            imag = float(var.imag)
            tol = 1e-12

            if abs(real) <= tol:
                return f"{self.value(imag)}j"
            if abs(imag) <= tol:
                return self.value(real)

            sign = '+' if imag >= 0 else '-'
            return f"{self.value(real)}{sign}{self.value(abs(imag))}j"

        if isinstance(var, str):
            qty = Qty.parse(var.strip())
            if qty is not None:
                if unit_hint:
                    qty = Qty(qty, unit_hint)
                return self.qty(qty, val_only=val_only)
            try:
                var = float(var.strip())
            except Exception:
                return var

        if isinstance(var, numbers.Real) and not isinstance(var, bool):
            if unit_hint:
                return self.qty(Qty(var, unit_hint), val_only=val_only)
            return self.value(var)
        return var  # preserve None
