# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from qcore import _unit_tree, qx, qxi, ucur
from qcore import read_unit, lmt2ulist, lmt2categ, _unit_info, _base_categ_mlist, lmt2qlist
from qutil import css2strs, list2table, find_matched_variables, cal_link, calurl
from calc import QCals
import itertools
from qcore.mod_anno import *


def convert_list(ulist):
    unames = [u[0] for u in ulist]
    plist = list(itertools.permutations(unames, 2))
    links = []
    for upair in plist:
        parameters = f'value/1/from_unit/{upair[0]}/convert_to_units/{upair[1]}/unit_cost/-/---/'
        uname0 = upair[0] + ' (' + _unit_info[upair[0]]['long_name'] + ')'
        uname1 = upair[1] + ' (' + _unit_info[upair[1]]['long_name'] + ')'
        caption = f"Convert {uname0} to {uname1}"
        links.append(cal_link(calurl('conv', parameters), caption, target='a'))
    return links


def conv2__help(__info=None):
    lmt = 'L' if __info is None else __info.upper()
    ulist = lmt2ulist(lmt)
    clist = convert_list(ulist)
    cid = 'conv2_help__page'
    tbl = list2table(clist, ["Conversion Options"], cid, 'table')
    return tbl


def conv2__info(__info=None):
    if __info is None:
        lmt = 'L'
    else:
        lmt = __info.upper()
    ulist = lmt2ulist(lmt)
    qlist = lmt2qlist(lmt)
    if len(qlist) > 0:
        mode_list = {
            'u2u': 'Unit -> Unit',
            'u2q': 'Unit -> Quantity',
            'q2u': 'Quantity -> Unit',
            'q2q': 'Quantity -> Quantity'
        }
    else:
        mode_list = {
            'u2u': 'Unit -> Unit',
        }

    return {
        'title': f'Unit Converter: {lmt2categ(lmt)}',
        'desc': '',
        'schema': {
            'quantity': {
                # 'type':'qsel2' doesn't trigger hx-get, because select2 change the element properties at runtime
                'type': 'choice', 'choices': _base_categ_mlist(),
                'attrs': {
                    'hx-get': '/catalog/ulist/',
                    'hx-target': 'closest .calc',
                    'hx-swap': 'outerHTML', 'hx-indicator': '.htmx-indicator'
                }
            },
            'mode': {
                'type': 'choice', 'choices': mode_list,
            },
            'from_unit': {
                'type': 'multiplechoice', 'choices': ulist,
                'xhelp_text': 'Select one unit',
            },
            'to_units': {
                'type': 'multiplechoice', 'choices': ulist,
                'xhelp_text': 'Select one or more units',
            },
            'from_qty': {'type': 'qsel2', 'choices': qlist},
            'to_qty': {'type': 'qsel2', 'choices': qlist},
        },
        'showhide': {
            'mode': {'fields': ['from_unit', 'from_qty', 'to_units', 'to_qty', 'unit_cost'], 'callback': 'conv2_sh'}
        },
        'calculate': 'Convert',
        # 'row': ['3-4'],
        'kins': 'conv',
        'script': '''
        function conv2_sh(v){
          if(v=='u2u'){
            return [true, false, true, false, true]
          } else if (v=='u2q') {
            return [true, false, false, true, false]
          } else if (v=='q2u') {
            return [false, true, true, false, false]
          } else if (v=='q2q') {
            return [false, true, false, true, false]
          }
        }
        '''
    }


def conv2__input(_kwargs):
    return {
        'unit_cost': ucur('@UNC/ft'),
    }


def conv2(quantity='L', mode='u2u', value: qtexta = '1.0', from_unit=['ft'], from_qty='l_earth_moon',
          to_units=['m'], to_qty='', unit_cost: qtx = '@UNC/ft', __info: qhide = 'L'):
    qfrom = None
    from_unit_ = ''
    to_units_ = to_units
    value = QCals.safe_eval(value)
    converted_value = None
    if mode == 'u2u':
        from_qty = ''
        to_qty = ''
        from_unit_ = from_unit[0]
        qfrom = Qty(value, from_unit_)
        converted_value = qfrom.to_units(to_units)
    elif mode == 'u2q':
        from_qty = ''
        to_units = []
        unit_cost = '@UNC/ft'
        from_unit_ = from_unit[0]
        qfrom = Qty(value, from_unit_)
        converted_value = qfrom / qx(to_qty)
    elif mode == 'q2u':
        from_unit = []
        from_unit_ = ''
        to_qty = ''
        unit_cost = '@UNC/ft'
        qfrom = value * qx(from_qty)
        converted_value = qfrom.to_units(to_units)
    elif mode == 'q2q':
        from_unit = []
        from_unit_ = ''
        to_units = []
        unit_cost = '@UNC/ft'
        qfrom = value * qx(from_qty)
        converted_value = qfrom / qx(to_qty)

    category = qfrom.category()
    expressed_value = 'n/a'
    # | Cost calculation
    unit_cost = Qty(unit_cost)
    if unit_cost.val is None:
        total_cost = Qty('@UNC')
    else:
        qvalue = Qty(value, from_unit[0])
        cur_used = find_matched_variables(unit_cost.uom.lower(), _unit_tree['C'])[0]
        total_cost = Qty(unit_cost * qvalue).to(cur_used)
    return conv_output(value, from_unit_, to_units_, [], converted_value,
                       expressed_value, category, total_cost, from_qty, to_qty)


def conv_output(value, from_unit, inunits: list, xinunits: list, converted_value,
                expressed_value, category, total_cost, from_qty='', to_qty=''):
    etc = ', etc.' if len(inunits) > 1 or len(xinunits) > 1 else ''
    if from_qty == '':
        ruf = read_unit(from_unit if from_unit != '' else 'unit')
        ruf_out = f'{value} {ruf.get("Write as")} ({ruf.get("Read as")})'
    else:
        if value == 1:
            ruf_out = f'{qxi(from_qty)['description']} ({from_qty})'
        else:
            ruf_out = f'{value} times {qxi(from_qty)['description']} ({from_qty})'

    if to_qty == '':
        to_unit = (inunits[0] if len(inunits) > 0 else '') or (
            xinunits[0] if len(xinunits) > 0 else '') or from_unit
        rut_out = ''
        if to_unit != '':
            rut = read_unit(to_unit)
            rut_out = f'{rut.get("Write as")} ({rut.get("Read as")}){etc}'
        elif from_qty != '':
            rut_out = f'{qxi(from_qty)['description']} ({from_qty})'
    else:
        rut_out = f'{qxi(to_qty)['description']} ({to_qty})'

    return {
        'Conversion of': qhtml(f'{category}'),
        'Converting from': qhtml(ruf_out),
        'Converting to': qhtml(rut_out),
        'Converted Value': converted_value,
        'Total Cost': total_cost,
        'Expressed Value': qhtml(expressed_value)
    }


def conv1__info():
    return {
        'title': 'Simple Unit Converter (old version)',
        'images': {'top': ['calc/images/measuring-tools.png']},
        'kins': 'conv2'
    }


def conv1(value: qtexta = '5.5', from_unit: quomx = 'ft',
          convert_to_units: str = 'm', express_in_units: str = 'yd,ft,inch',
          unit_cost: qtx = '@UNC/ft'):
    """Simple Unit Converter

    Args:
        value: Value to be converted, you can enter simple expression as well (e.g. 92/3+15)
        from_unit: Unit to be converted from
        convert_to_units: Unit to be converted to. If you want to convert to multiple units, separate those units using comma (e,g, ft, m, yd)
        express_in_units: Unit to be expressed in. If you want to express in multiple units, separate those units using comma (e,g, ft, m, yd)

    Return:
        returns converted unit(s) and expressed in unit(s)
    """
    # qvalue = Qty(float(value), from_unit)  # , convert_to_unit)
    # keep arguement convert_to_units: str = ''
    value = QCals.safe_eval(value)
    qvalue = Qty(value, from_unit)
    converted_value = qvalue
    category = qvalue.category()
    expressed_value = 'n/a'
    # breakpoint()
    inunits = []
    if convert_to_units != '':
        # labels = []
        if convert_to_units == 'all':
            lmt = category.split(':')[0]
            if lmt in _unit_tree:
                # print(_unit_tree[lmt])
                inunits = [name for name in _unit_tree[lmt]]
                # labels = [long_name for long_name in _unit_tree[lmt]]
        else:
            inunits = css2strs(convert_to_units)
        converted_value = qvalue.to_units(inunits)

    xinunits = []
    if express_in_units != '':
        xinunits = css2strs(express_in_units)
        expressed_value = qvalue.as_units(express_in_units)

    # | Cost calculation
    unit_cost = Qty(unit_cost)
    if unit_cost.val is None:
        total_cost = Qty('@UNC')
    else:
        cur_used = find_matched_variables(unit_cost.uom.lower(), _unit_tree['C'])[0]
        total_cost = Qty(unit_cost * qvalue).to(cur_used)
    return conv_output(value, from_unit, inunits, xinunits,
                       converted_value, expressed_value, category, total_cost)


def conv__info():
    return {
        'title': 'Simple Unit Converter',
        'schema': {
            'mode': {'type': 'choice', 'choices': {'1': 'Simple', '2': 'Common', '3': 'Extended'}}
        },
        'anyof': {"1": {"fields": ["from_unit", "from_qty"]},
                  "2": {"fields": ["convert_to_units", "convert_to_qty"]}
                  },
        'showhide': {
            "mode": {"fields": ["from_qty", "convert_to_qty", "express_in_units", "unit_cost"],
                     "callback": "convert_sh"}
        },
        'images': {'top': ['calc/images/measuring-tools.png']},
        'kins': 'conv2',
        'script': '''
            function convert_sh(v)
            {
            console.log(v);
            if(v=='1') return [false,false,false,false];
            else if(v=='2') return [false,false,true,true];
            else return [true,true,true,true]
            }
            ''',
    }


def conv(value: qtexta = '1.0',
         from_unit: str = 'ft',
         from_qty: str = 'q0001',
         convert_to_units: str = 'm',
         convert_to_qty: str = 'm',
         express_in_units: str = 'yd,ft,inch',
         unit_cost: qtx = '@UNC/ft',
         mode='1'):
    """Simple Unit Converter

    Args:
        value: Value to be converted, you can enter simple expression as well (e.g. 92/3+15)
        from_unit: Unit to be converted from
        convert_to_units: Unit to be converted to. If you want to convert to multiple units, separate those units using comma (e,g, ft, m, yd)
        express_in_units: Unit to be expressed in. If you want to express in multiple units, separate those units using comma (e,g, ft, m, yd)

    Return:
        returns converted unit(s) and expressed in unit(s)
    """
    # qvalue = Qty(float(value), from_unit)  # , convert_to_unit)
    # keep arguement convert_to_units: str = ''
    if mode == '1':
        from_qty = ''
        convert_to_qty = ''
        express_in_units = ''
        unit_cost = '@UNC/ft'
    elif mode == '2':
        from_qty = ''
        convert_to_qty = ''

    value = QCals.safe_eval(value)
    if from_unit != '':
        qvalue = Qty(value, from_unit)
    elif from_qty != '':
        qvalue = value * qx(from_qty)
    else:
        qvalue = Qty(value, 'unit')
    converted_value = qvalue
    category = qvalue.category()
    expressed_value = 'n/a'
    # breakpoint()
    inunits = []
    if convert_to_units != '':
        if convert_to_units == 'all':
            lmt = category.split(':')[0]
            if lmt in _unit_tree:
                inunits = [name for name in _unit_tree[lmt]]
        else:
            inunits = css2strs(convert_to_units)
        converted_value = qvalue.to_units(inunits)

    if convert_to_qty != '':
        qty = qx(convert_to_qty)
        converted_value = qvalue / qty
        inunits = []

    xinunits = []
    if express_in_units != '':
        xinunits = css2strs(express_in_units)
        expressed_value = qvalue.as_units(express_in_units)

    # | Cost calculation
    unit_cost = Qty(unit_cost)
    if unit_cost.val is None:
        total_cost = Qty('@UNC')
    else:
        cur_used = find_matched_variables(unit_cost.uom.lower(), _unit_tree['C'])[0]
        total_cost = Qty(unit_cost * qvalue).to(cur_used)
    return conv_output(value, from_unit, inunits, xinunits,
                       converted_value, expressed_value, category, total_cost,
                       from_qty, convert_to_qty)
