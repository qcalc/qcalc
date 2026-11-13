# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import json
from functools import lru_cache
from types import MappingProxyType
from .qd_basic import css2strs
from .qc_mbase import _base_names, _fps_names, _cgs_names, _base_categories, powers_to_bname_lmt, _unit_operators
from .qc_units import UnitRegistry, RegistryMeta
from .qc_mquantity import MeasureQuantity as MQty


def _decode_qty(jso):
    if '__qty__' in jso:
        return Qty(jso['val'], jso['uom'])
    else:
        return jso


def load_qty(jso):
    return _decode_qty(json.loads(jso))


class Qty(MQty):
    # | a) num, 'unit'
    # | b) num, Unit
    # | c) 'num unit'
    # | d) num, 'unit', 'unit' -> 3 args
    # | e) num, Unit, 'unit' -> 3 args
    # | f) 'num unit', 'unit' -> 2 args both string
    # | g) Qty
    # | h) Qty, 'unit'

    def __init__(self, *args):
        arg_cnt = len(args)
        if arg_cnt == 3 or (arg_cnt == 2 and isinstance(args[0], str) and isinstance(args[1], str)):  # | d) or e) or f)
            tounit = args[arg_cnt - 1]
            if arg_cnt == 3:  # | d) or e)
                super().__init__(*args[:arg_cnt - 1])
            elif arg_cnt == 2:  # | f)
                qty_str, ln = self.compose(args[0])
                super().__init__(qty_str)
            temp = self.to(tounit)
            self.value = temp.value
            self.unit = temp.unit
        else:  # | 1 or 2 args i.e. val or val, uom_str or qty_str, (a) or (b) or (c) or unknown
            if isinstance(args[0], str):  # | c)
                qty_str, ln = self.compose(args[0])
                # print('composed qty:', qty_str)
                super().__init__(qty_str)
            elif arg_cnt == 2 and isinstance(args[0], self.__class__) and isinstance(args[1], str):  # | h)
                # deb@03.07.24
                tounit = args[1]
                temp = args[0].to(tounit)
                self.value = temp.value
                self.unit = temp.unit
            else:  # | (a) or (b) or (g) Qty
                super().__init__(*args)

    def to_json(self):
        return json.dumps({'__qty__': 1, 'val': self.val, 'uom': self.uom})  # | simple json dumps

    def __str__(self):
        return f'{self.val} {self.uom}'

    def __cmp__(self, other):
        if other == '' or other is None:
            return 1
        else:
            return super().__cmp__(other)

    @property
    def val(self):
        return self.value

    @property
    def uom(self):
        return self.unit.name()

    def nzq(self):
        if self.value is None:
            self.value = 0.0

    def category(self):
        powers = self.unit.powers
        bn, lmt = powers_to_bname_lmt(powers, _base_names)
        if lmt in _base_categories:
            categ = lmt + ': ' + _base_categories[lmt]
        else:
            categ = lmt
        return categ

    def roundoff(self, idecimal=0):
        self.value = round(self.value, idecimal)
        return self

    def as_units(self, units):  # units - comma separated string of units, or list of unit strings
        if isinstance(units, str):
            units = [x.strip() for x in units.split(',')]
        xpr_as = self.in_units_of(*units)
        if isinstance(xpr_as, (list, tuple)):
            xpr_str = [str(qstr) for qstr in xpr_as]
            return ', '.join(xpr_str)
        else:
            return xpr_as

    def as_(self, units):
        return self.as_units(units)

    def to_units(self, units):  # units - comma separated string of units, or list of unit strings
        if isinstance(units, str):
            units = [x.strip() for x in units.split(',')]
        res = []
        for i in range(len(units)):
            # try:
            x = self.to(units[i]) * 1  # create a copy of the object
            res.append(x)
            # except:
            #     pass
        return res

    def si(self):
        bname, lmt = powers_to_bname_lmt(self.unit.powers, _base_names)
        return self.in_units_of(bname)

    def mks(self):
        return self.si()

    def fps(self):
        fps_name, lmt = powers_to_bname_lmt(self.unit.powers, _fps_names)
        return self.in_units_of(fps_name)

    def cgs(self):
        cgs_name, lmt = powers_to_bname_lmt(self.unit.powers, _cgs_names)
        return self.in_units_of(cgs_name)

    @staticmethod
    def compose2(qstrs_wwo_comma):
        qstrs = css2strs(qstrs_wwo_comma)
        qty_obj = None
        ln = len(qstrs)

        try:
            for qstr in qstrs:
                pq_obj = MQty(qstr)
                if pq_obj.value is not None:
                    qty_obj = pq_obj if qty_obj is None else qty_obj + pq_obj
        except:
            ln = 0

        return str(qty_obj) if qty_obj is not None else '', ln

    @staticmethod
    def compose(qstrs_wwo_comma):
        """``(text, count)`` of the sum of comma separated quantities, e.g. '1ft, 6 inch' -> ('1.5 ft', 2)."""
        qstrs = css2strs(qstrs_wwo_comma)
        ln = len(qstrs)
        qty_str = ''
        try:
            if ln == 0:
                return '', 0
            qty_str = qstrs[0]
            if ln > 1:
                var_qt = MQty(qstrs[0])
                for i in range(1, ln):
                    var_qt2 = MQty(qstrs[i])
                    if var_qt.value is None:
                        var_qt = var_qt2
                    elif var_qt2.value is not None:
                        var_qt += var_qt2
                qty_str = str(var_qt)
        except Exception:
            ln = 0
        return qty_str, ln

    @classmethod
    def parse(cls, snum_unit: str):
        """The Qty of a text such as '3.5 ft', or None when it is not one."""
        try:
            return cls(snum_unit)
        except:
            return None

    @classmethod
    def is_valid(cls, snum_unit: str) -> bool:
        return cls.parse(snum_unit) is not None

    @staticmethod
    @lru_cache(maxsize=4096)
    def kind(sunit):
        """``(kind, text, count)`` where kind is 'uom' ('ft'), 'qty' ('3.5 ft', '12h,45min,30s') or 'text'."""
        if len(sunit) > 96:  # @26.03.24 anything that long most possibly is not a unit
            return 'text', sunit, 0
        if UnitRegistry.is_uom(sunit):
            return 'uom', sunit, 0  # only uom e.g. 'ft'
        if Qty.is_valid(sunit):  # ln=1
            return 'qty', sunit, 1  # single part e.g. '3.5 ft'
        qty_str, ln = Qty.compose(sunit)
        if qty_str != '' and ln > 1:
            return 'qty', qty_str, ln  # 2,3,4 multipart e.g. '12h,45min,30s'
        return 'text', sunit, 0


def _add_all_quantities(_add_qty):
    _add_qty('l_earth_moon', '384000 km', 'Average distance between the Earth and the Moon')
    _add_qty('a_earth', '4.543e9 yr', 'Age of Earth')
    _add_qty('r_earth', '6378100 m', 'Nominal Earth equatorial radius')
    _add_qty('r_jupiter', '71492000 m', 'Nominal Jupiter equatorial radius')
    _add_qty('r_sun', '695700000 m', 'Nominal Solar radius')
    _add_qty('m_earth', '5.97216787e+24 kg', 'Earth mass')
    _add_qty('m_moon', '7.34767309e+22 kg', 'Moon mass')
    _add_qty('m_jupiter', '1.8981246E+27 kg', 'Jupiter mass')
    _add_qty('m_sun', '1.98840987E+30 kg', 'Solar mass')
    _add_qty('mp_earth', '398600400000000 m**3/s**2', 'Nominal Earth gravitational parameter')
    _add_qty('mp_jupiter', '126686530000000000 m**3/s**2', 'Nominal Jupiter gravitational parameter')
    _add_qty('mp_sun', '1.3271244E+20 m**3/s**2', 'Nominal solar gravitational parameter')
    _add_qty('r_neutrino', '142 quectom', 'Effective cross section radius of 1 MeV neutrinos')
    _add_qty('r_neutrino_he', '7 zeptom', 'Effective cross section radius of high-energy neutrinos')
    _add_qty('r_proton', '850 attom', 'Approximate Proton radius')
    _add_qty('l_string', '1 yoctom', 'Upper bound of typical size range for fundamental strings')
    _add_qty('l_weak_force', '10 attom', 'Range of weak force')
    _add_qty('r_electron', '2.81794 femtom', 'Classical electron radius')

    _add_qty('m_a4', '5 g', '80 GSM A4 size paper weight')
    _add_qty('th_hair', '0.075 mm', 'Average thickness of human hair')
    _add_qty('g_moon', '1.625 m/s**2', 'Gravitational acceleration on the moon')
    _add_qty('mole_w', '55.50837344 mol', 'Number of moles in 1L water')
    _add_qty('atom_w', '55.50837344 mol*Nav', 'Number of atoms in 1L water')
    _add_qty('m_glucose', '180.15588 g/mol', 'molar mass of glucose (C6H12O6)')


class QtyRegistry(metaclass=RegistryMeta):
    """The named quantities (e.g. 'th_hair'), filled once by ``_load()``. Everything is class level.

    ``info`` and ``tree`` are read-only views and only the ``_`` methods change the registry,
    see RegistryMeta in qc_units for the reason.
    """

    # _info example: {'q0001': {'base_qty': '384000000 m',
    # 'description': 'The average distance between the Earth and the Moon', 'dimension': 'L'}}
    _info = {}

    # _tree example: {'L': ('q0001',)}
    _tree = {}

    @classmethod
    def _add(cls, name, qty_str: str, description):
        if name in cls._info:
            raise KeyError(f'Error (PQO): Qty {name} already defined')

        qty = Qty(qty_str)
        cls._info[name] = MappingProxyType({
            "description": description,
            "qty": qty,
            "base_qty": qty.unit.base_qty,
            "dimension": qty.unit.dimension
        })
        dim = qty.unit.dimension  # unit.dimension will be assigned to '0' for unitless entity
        assert dim in _base_categories
        cls._tree[dim] = (*cls._tree.get(dim, ()), name)

    @classmethod
    def _load(cls):
        _add_all_quantities(cls._add)

    @classmethod
    def get(cls, qcode):  # q() extended
        return cls.info[qcode.lower()]['qty']

    @classmethod
    def entry(cls, qcode):  # extended q() info
        return cls.info[qcode.lower()]

    @classmethod
    def by_dimension(cls, lmt):
        """``[(name, title), ...]`` of the named quantities of a dimension."""
        tmp = []
        if lmt is not None:
            for qname in cls.tree.get(lmt.upper(), []):
                tmp.append((qname, f"{cls.info[qname]['description']} ({qname})"))
        return tmp

    @classmethod
    def desc(cls, sname):  # deb@04.06.24
        if sname in cls.info:
            lname = cls.info[sname]['description']
            bqty = cls.info[sname]['base_qty']
            category = ''
            lmt = '[' + cls.info[sname]['dimension'] + ']'

            lname_categ = ', '.join(filter(None, [lname, category, lmt]))
            lname_categ = '(' + lname_categ + ')' if lname_categ != '' else ''
            qtydesc = '%s %s: 1 %s = %s' % (sname, lname_categ, sname, bqty)
        else:
            qtydesc = f'qty {sname}: not found'
        return qtydesc

    @classmethod
    def search(cls, sterm):
        """Up to 100 ``(name, description)`` of the units and named quantities whose description has ``sterm``."""
        if any(op in sterm for op in _unit_operators):
            try:
                unit = UnitRegistry.find(sterm)
                sterm = '[' + unit.dimension + ']'
            except (Exception,):
                pass

        sterm = sterm.lower()  # lowercase
        matches = []
        if len(sterm) > 0:
            for name in UnitRegistry.info:
                udesc = UnitRegistry.desc(name)
                if sterm in udesc.lower():
                    matches.append((name, udesc))
            for name in cls.info:
                qdesc = cls.desc(name)
                if sterm in qdesc.lower():
                    matches.append((name, qdesc))
        return matches[0:100]
