# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import re
import json
from qutil import css2strs, preprocess_expression
from qcore.qc_mbase import _fps_names, _cgs_names, _base_categories, powers_to_bname_lmt, _unit_operators
from qcore.qc_munit import isMeasureUnit
from qcore.qc_units import _unit_table, _unit_info, _base_names, _unit_tree, unit_desc
from qcore.qc_mquantity import MeasureQuantity as MQty, find_unit, isMeasureQuantity


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
                qty_str, ln = compose_qty(args[0])
                super().__init__(qty_str)
            temp = self.to(tounit)
            self.value = temp.value
            self.unit = temp.unit
        else:  # | 1 or 2 args i.e. val or val, uom_str or qty_str, (a) or (b) or (c) or unknown
            if isinstance(args[0], str):  # | c)
                qty_str, ln = compose_qty(args[0])
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


def compose_qty2(qstrs_wwo_comma):
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


def compose_qty(qstrs_wwo_comma):
    qstrs = css2strs(qstrs_wwo_comma)
    ln = len(qstrs)
    qty_str = ''
    if ln >= 0:
        try:
            qty_str = qstrs[0]
            if ln > 1:
                var_qt = MQty(qstrs[0])
                for i in range(1, ln):
                    var_qt2 = MQty(qstrs[i])
                    if var_qt.value is None:
                        var_qt = var_qt2
                    elif var_qt2.value is not None:
                        var_qt += MQty(qstrs[i])
                qty_str = str(var_qt)
        except:
            ln = 0
            pass
    return qty_str, ln


def str_to_named_uom(uname):
    unit = None
    try:
        unit = _unit_table[uname]
    except:
        pass
    return unit


def is_str_named_uom(uname):
    return str_to_named_uom(uname) is not None


def str_to_uom(uname: str):
    unit = None
    try:
        unit = eval(uname, _unit_table)  # safe
        unit = unit if isMeasureUnit(unit) else None
    except:
        pass
    return unit


def is_str_uom(uname: str) -> bool:
    return str_to_uom(uname) is not None


def str_to_qty(snum_unit: str):
    q = None
    try:
        q = Qty(snum_unit)
        q = q if isMeasureQuantity(q) else None
    except:
        pass
    return q


def is_str_qty(snum_unit: str) -> bool:
    return str_to_qty(snum_unit) is not None


def calc_unit(sunit):
    return preprocess_expression(sunit, disp=False)


def disp_unit(sunit):
    return preprocess_expression(sunit, disp=True)


def read_unit(sunit):
    # sunit = "g*ft/s^2/m^3"
    sunit = sunit.lower()  # convert to lowercase, used _unit_info[var]
    pun = find_unit(sunit)  # find_unit will also convert to lowercase
    sunit = disp_unit(sunit)
    s = sunit

    def rep(op):
        nonlocal s
        s = s.replace(op, ' ' + op + ' ')
        return s

    s = ' ' + list(map(lambda op: rep(op), _unit_operators))[-1] + ' '
    w = s
    vars_ = (re.findall('[_a-z][_a-z0-9]*', sunit, re.I))
    for var in vars_:
        s = s.replace(' ' + var + ' ', _unit_info[var]['long_name'].replace(' ', '-'))  # lowercase
        w = w.replace(' ' + var + ' ', _unit_info[var]['proper_name'].replace(' ', '-'))  # propercase
    # trim spaces
    s = s.replace(' ', '')
    w = w.replace(' ', '')
    return {"Read as": s, "Write as": w, "Category": pun.category, "Dimension": pun.dimension, "Quantity": pun.base_qty}


def str_type(sunit):
    if len(sunit) > 96:  # @26.03.24 anything that long most possibly is not a unit
        return 'text', sunit, 0
    elif is_str_uom(sunit):
        return 'uom', sunit, 0  # only uom e.g. 'ft'
    elif is_str_qty(sunit):  # ln=1
        return 'qty', sunit, 1  # single part e.g. '3.5 ft'
    else:
        qty_str, ln = compose_qty(sunit)
        if qty_str != '' and ln > 1:
            return 'qty', qty_str, ln  # 2,3,4 multipart e.g. '12h,45min,30s'
        else:
            return 'text', sunit, 0


def uname2lmt(uname):
    lmt = None
    if uname is not None:
        unit1 = find_unit(uname)
        lmt = unit1.dimension
    return lmt


def lmt2categ(lmt):
    if lmt in _base_categories:
        categ = _base_categories[lmt] + f' ({lmt})'
    else:
        categ = lmt
    return categ


def lmt2ulist(lmt):
    tmp = []
    if lmt is not None:  # @ft output  @11.09.23
        # there are some lmt e.g. LT for which there are no member units
        # so _unit_tree[lmt] will raise exception, better to use _unit_tree.get(lmt,[])
        ulist = _unit_tree.get(lmt.upper(), [])
        for uname in ulist:
            tmp.append((uname, f"{_unit_info[uname]['proper_name']} ({_unit_info[uname]['long_name']})"))
    return tmp


def lmt2qlist(lmt):
    tmp = []
    if lmt is not None:
        qlist = _qty_tree.get(lmt.upper(), [])
        for qname in qlist:
            tmp.append((qname, f"{_qty_info[qname]['description']} ({qname})"))
    return tmp


# _qty_table Example: {'q0001': MeasureUnit(384000000,'km'), ...}
# _qty_table = {}  # _qty_table['W']=_qty_info['W']['qty']

# _qty_info Example: {'q0001': {'base_qty': '384000000 m',
# 'description': 'The average distance between the Earth and the Moon', 'dimension': 'L'}}
_qty_info = {}

# _qty_tree Example: {'L': ['q0001']}
_qty_tree = {}


def _add_qty(name, qty_str: str, description):
    if name in _qty_info:  # _qty_table:
        raise KeyError(f'Error (PQO): Qty {name} already defined')

    qty = Qty(qty_str)
    # _qty_table[name] = qty
    _qty_info[name] = {
        "description": description,
        "qty": qty,
        "base_qty": qty.unit.base_qty,
        "dimension": qty.unit.dimension
    }
    dim = qty.unit.dimension  # unit.dimension will be assigned to '0' for unitless entity
    assert dim in _base_categories
    if dim not in _qty_tree:
        _qty_tree[dim] = []
    _qty_tree[dim].append(name)


def add_quantities():
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


def qx(qcode):  # q() extended
    # return _qty_table[qcode.lower()]
    return _qty_info[qcode.lower()]['qty']


def _base_categ_mlist():
    return [(k, v) for k, v in _base_categories.items()]  # if k in _unit_tree


def qxi(qcode):  # extended q() info
    return _qty_info[qcode.lower()]


def qty_desc(sname):  # deb@04.06.24
    if sname in _qty_info:
        lname = _qty_info[sname]['description']
        bqty = _qty_info[sname]['base_qty']
        # category = _unit_info[sname]['category']
        category = ''
        lmt = '[' + _qty_info[sname]['dimension'] + ']'

        lname_categ = ', '.join(filter(None, [lname, category, lmt]))
        lname_categ = '(' + lname_categ + ')' if lname_categ != '' else ''
        qtydesc = '%s %s: 1 %s = %s' % (sname, lname_categ, sname, bqty)
    else:
        qtydesc = f'qty {sname}: not found'
    return qtydesc


def search_unit_result(sterm):
    if any(op in sterm for op in _unit_operators):
        try:
            unit = find_unit(sterm)
            sterm = '[' + unit.dimension + ']'
        except (Exception,):
            pass

    sterm = sterm.lower()  # lowercase
    matches = []
    if len(sterm) > 0:
        for name in _unit_info:
            udesc = unit_desc(name)
            if sterm in udesc.lower():
                matches.append((name, udesc))
        for name in _qty_info:
            qdesc = qty_desc(name)
            if sterm in qdesc.lower():
                matches.append((name, qdesc))
    else:
        matches = []
    return matches[0:100]


def _test():
    import time
    x = Qty('5 ft')
    y = Qty(x, 'inch')
    print('y=', y)
    # exit(0)

    n = 100
    start_time = time.time()
    q1 = q2 = q3 = q4 = ''
    for i in range(n):
        q1 = compose_qty('1ft,2inch')
        q2 = compose_qty('None ft,2inch')
        q3 = compose_qty('@ft,2inch')
        q4 = compose_qty('xyz, abc')
    end_time = time.time()
    diff1 = end_time - start_time
    print(q1, q2, q3, q4)
    print(diff1)

    start_time = time.time()
    for i in range(n):
        q1 = compose_qty2('1ft,2inch')
        q2 = compose_qty2('None ft,2inch')
        q3 = compose_qty2('@ft,2inch')
        q4 = compose_qty2('xyz, abc')  # fails
    end_time = time.time()
    diff2 = end_time - start_time
    print(q1, q2, q3, q4)
    print(diff2)
    print(diff1 / diff2)

    print(read_unit('mmH2O/g/ft'))

    print(str_to_uom('ft'))
    print(str_to_uom('ft/s'))
    print(str_to_named_uom('ft/s'))
    print(str_to_named_uom('ft'))
    print(compose_qty('3ft,2inch'))
    print(is_str_qty('3ft,2inch'))


if __name__ == '__main__':
    _test()
