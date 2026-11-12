# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

"""Single source of cost calculation: the user's Schedule of Rates and QCost, which prices quantities with it.

    cost = QCost.from_result(result, spec='~Brick Work*')   # price a calculator's own scalar Qty outputs
    result.update(cost.results(per=result['Brick Work Volume'], per_label='Volume'))

    cost = QCost()                                          # or price named quantities
    cost.add_all({'Cement': Qty(120, 'bag'), 'Skilled Labour': Qty(80, 'manday')})
    cost.overhead('Contingency', '5 pct')

Cost is then a normal output, so compare, scenario and sensitivity can use it. The Calculate Cost
calculator uses the same class. Rates are saved per user (account when logged in, session otherwise).
"""

from __future__ import annotations

from types import SimpleNamespace

import pandas as pd

from qcore import Qty, qwarn
from qutil import specified_args
from .mod_cache import QRates
from .mod_shared_data import _pack_payload, _unpack_payload

SCHEDULE_COLUMNS = ['Item', 'Price', 'Currency', 'Price Per', 'Price Unit']
_SLOT = 'schedule'
_EMPTY = pd.DataFrame(columns=SCHEDULE_COLUMNS)


def default_rate_schedule() -> pd.DataFrame:
    """Illustrative rates, used until the user saves a Schedule of Rates."""
    return pd.DataFrame({
        'Item': ['Brick', 'Sand', 'Cement', 'Gravel', 'Steel', 'Floor Tiles', 'Paint', 'Ready-mix Concrete',
                 'Skilled Labour', 'Unskilled Labour'],
        'Price': [10.0, 20.0, 500.0, 75.0, 100.0, 90.0, 700.0, 7500.0, 1200.0, 1000.0],
        'Currency': ['BDT'] * 10,
        'Price Per': [1] * 10,
        'Price Unit': ['ea', 'cft', 'bag', 'cft', 'kg', 'ft^2', 'L', 'm^3', 'manday', 'manday'],
    })


def save_rates(schedule: pd.DataFrame) -> None:
    """Save the schedule to the user's account (to the session for anonymous users)."""
    QRates.setp1(_SLOT, _pack_payload(schedule[SCHEDULE_COLUMNS].astype(str)))


def load_rates() -> pd.DataFrame | None:
    saved = _unpack_payload(QRates.getp1(_SLOT))
    return saved if isinstance(saved, pd.DataFrame) else None


def _num(value) -> float:
    return float(str(value).replace(',', ''))


def _key(name) -> str:
    return str(name).strip().casefold()


def _currency(rate: Qty) -> str:
    return rate.uom.split('/')[0]


class QCost:
    """Quantities priced with a Schedule of Rates, plus overheads applied on the running subtotal."""

    def __init__(self, schedule: pd.DataFrame | None = None, use_defaults: bool = True):
        """schedule: Item/Price/Currency/Price Per/Price Unit table, else the saved one, else the defaults.

        use_defaults=False leaves items without a saved rate unpriced instead of using the illustrative defaults.
        """
        self.default = False
        if schedule is None:
            schedule = load_rates()
        if schedule is None and use_defaults:
            schedule, self.default = default_rate_schedule(), True
        self._rates, self._labels = {}, {}  # casefolded item -> unit cost Qty, item as written
        for _, row in (schedule if schedule is not None else _EMPTY).iterrows():
            unit_price = _num(row['Price']) / _num(row['Price Per'])
            self._rates[_key(row['Item'])] = Qty(f"{unit_price:.12g} {str(row['Currency']).strip()}/"
                                                 f"{str(row['Price Unit']).strip()}")
            self._labels[_key(row['Item'])] = str(row['Item']).strip()
        self.lines = []  # name, qty, rate, cost, group; cost is None when there is no rate
        self.currency = None
        self._overheads = []

    @classmethod
    def from_result(cls, result: dict, spec='*', **kwargs) -> QCost:
        """Price the scalar Qty outputs picked by spec (the specified_args syntax, e.g. '~Brick Work*')."""
        cost = cls(**kwargs)
        for name in specified_args(list(result), spec, empty_spec='*'):
            qty = result[name]
            if isinstance(qty, Qty) and 'C' not in qty.unit.dimension:  # a currency quantity is not priced again
                cost.add(name, qty)
        return cost

    @classmethod
    def from_frame(cls, items: pd.DataFrame) -> QCost:
        """Price the Item/Quantity/Unit Cost rows of a table, using the rates in the table itself."""
        cost = cls(schedule=_EMPTY)
        for _, row in items.iterrows():
            cost.add(row['Item'], Qty(row['Quantity']), rate=Qty(row['Unit Cost']))
        return cost

    @classmethod
    def from_unit_costs(cls, unit_costs: pd.DataFrame) -> QCost:
        """Rates from an Item/Unit Cost table, the form shared by the Schedule of Rates calculator."""
        cost = cls(schedule=_EMPTY)
        for item, rate in zip(unit_costs['Item'], unit_costs['Unit Cost']):
            cost._rates[_key(item)], cost._labels[_key(item)] = Qty(rate), str(item).strip()
        return cost

    @property
    def has_rates(self) -> bool:
        return bool(self._rates)

    def unit_costs(self) -> pd.DataFrame:
        """The rates as an Item/Unit Cost table."""
        return pd.DataFrame({'Item': [self._labels[k] for k in self._rates], 'Unit Cost': list(self._rates.values())})

    def add(self, name, qty: Qty, rate=None, group: str | None = None):
        """Price one quantity. rate overrides the schedule; the group defaults to Labour for mandays, else Material."""
        rate = Qty(rate) if rate is not None else self._rates.get(_key(name))
        group = group or ('Labour' if qty.uom.lower() == 'manday' else 'Material')
        cost = None
        if rate is not None:
            self.currency = self.currency or _currency(rate)
            cost = (qty * rate).to(self.currency)
        self.lines.append(SimpleNamespace(name=str(name), qty=qty, rate=rate, cost=cost, group=group))

    def add_all(self, items: dict, group: str | None = None):
        for name, qty in items.items():
            self.add(name, qty, group=group)

    def overhead(self, name: str, share):
        """Add an overhead (markup, contingency, tax) on the subtotal so far, e.g. '10 pct' or 0.1."""
        self._overheads.append((name, Qty(share, 'unit').val if isinstance(share, str) else float(share)))

    @staticmethod
    def compound(subtotal: float, shares) -> list:
        """Amount of each overhead when every share applies on the subtotal plus the overheads before it."""
        amounts, running = [], subtotal
        for share in shares:
            amounts.append(running * share)
            running += amounts[-1]
        return amounts

    def fill_rates(self, items: pd.DataFrame) -> pd.DataFrame:
        """Replace the Unit Cost of the rows that have a rate here; other rows keep theirs."""
        items['Unit Cost'] = [self._rates.get(_key(item), old) for item, old in zip(items['Item'], items['Unit Cost'])]
        return items

    @property
    def missing(self) -> list:
        return [x.name for x in self.lines if x.cost is None]

    @property
    def notes(self) -> list:
        notes = []
        if self.default:
            notes.append('No Schedule of Rates is saved, so illustrative default rates were used. Open Schedule of Rates '
                         'and click Load to save your own; they are then used here.')
        if self.missing:
            notes.append('Not priced, no rate in the Schedule of Rates for: ' + ', '.join(self.missing) + '.')
        return notes

    def _subtotal(self) -> float:
        return sum(x.cost.val for x in self.lines if x.cost is not None)

    def _overhead_amounts(self) -> list:
        return self.compound(self._subtotal(), [share for _, share in self._overheads])

    @property
    def total(self) -> Qty | None:
        if self.currency is None:
            return None
        return Qty(self._subtotal() + sum(self._overhead_amounts()), self.currency)

    def group(self, name: str) -> Qty | None:
        """Cost of the priced lines of one group, before overheads."""
        if self.currency is None:
            return None
        return Qty(sum(x.cost.val for x in self.lines if x.cost is not None and x.group == name), self.currency)

    def per(self, qty: Qty) -> Qty | None:
        """Total cost per unit of qty, e.g. per ft^2 of built-up area."""
        total = self.total
        return None if total is None or not qty.val else Qty(total.val / qty.val, f'{self.currency}/{qty.uom}')

    def rows(self) -> dict:
        """Breakdown as a result table: every priced line, then each overhead, with its share of the total."""
        total = self.total.val if self.total is not None else 0

        def share(amount):
            return f'{amount / total * 100:.1f} %' if total else ''

        data = [[x.name, x.qty, x.rate, x.cost, share(x.cost.val)] for x in self.lines if x.cost is not None]
        data += [[name, '', '', Qty(amount, self.currency), share(amount)]
                 for (name, _), amount in zip(self._overheads, self._overhead_amounts())]
        return {'data': data, 'columns': ['Item', 'Quantity', 'Rate', 'Cost', 'Share']}

    def frame(self, costs: bool = False) -> pd.DataFrame:
        """Item/Quantity/Unit Cost table, with Item Cost when costs is True."""
        frame = pd.DataFrame({
            'Item': [x.name for x in self.lines],
            'Quantity': [x.qty for x in self.lines],
            'Unit Cost': [x.rate for x in self.lines]})
        if costs:
            frame['Item Cost'] = [x.cost for x in self.lines]
        return frame

    def chart(self, title: str = 'Cost Chart'):
        """Pie of the priced lines and overheads, built by the pie_chart calculator so step2 Modify Chart can reopen it."""
        from calculators.all.general.chart import pie_chart  # lazily, calc sits below the calculators
        rows = self.rows()['data']
        if not rows:
            return None
        return pie_chart(labels=','.join(str(r[0]).replace(',', ' ') for r in rows),
                         values=','.join(str(r[3].val) for r in rows), title=title, show_pct=True)['chart']

    def results(self, per: Qty | None = None, per_label: str = 'Unit', chart: bool = True) -> dict:
        """Result items: a cost per group, Total Cost, Cost per <per_label> when per is given, Cost Breakdown,
        Cost Chart unless chart is False, and Cost Notes."""
        if self.currency is None:
            return {'Cost Notes': qwarn('\n'.join(f'- {x}' for x in self.notes))} if self.notes else {}
        out = {f'{g} Cost': self.group(g) for g in dict.fromkeys(x.group for x in self.lines if x.cost is not None)}
        out['Total Cost'] = self.total
        if per is not None:
            out[f'Cost per {per_label}'] = self.per(per)
        out['Cost Breakdown'] = self.rows()
        if chart:
            out['Cost Chart'] = self.chart()
        if self.notes:
            out['Cost Notes'] = qwarn('\n'.join(f'- {x}' for x in self.notes))
        return out
