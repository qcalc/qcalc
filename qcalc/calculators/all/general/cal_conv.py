# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from qcore import _unit_tree, qx, qxi, to_ucur
from qcore import read_unit, lmt2ulist, lmt2cat, _unit_info, _base_categ_mlist, lmt2qlist, dim_to_bname, _base_names, \
    _conv_names
from qutil import css2strs, list2table, find_matched_variables, cal_link, calurl
from calc import QCals
import itertools
from qcore.mod_anno import *
from qconst import amount_help_text


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


def _conv2_ulist(lmt):
    ulist = lmt2ulist(lmt)
    if not ulist and len(lmt) > 1:  # | composite dimension without units, same default as the qty catalog
        ulist = []
        for names, label in ((_base_names, 'primary base'), (_conv_names, 'secondary base')):
            uname = dim_to_bname(lmt, names)
            if uname not in [u[0] for u in ulist]:
                ulist.append((uname, f'{uname} ({label})'))
    return ulist


def _conv2_mode_list(qlist):
    if len(qlist) > 0:
        return {
            'u2u': 'Unit -> Unit',
            'u2q': 'Unit -> Quantity',
            'q2u': 'Quantity -> Unit',
            'q2q': 'Quantity -> Quantity'
        }
    return {'u2u': 'Unit -> Unit'}


def _conv2_categ_list(catalog):
    # | the short catalog keeps only the quantities which have more than 2 units
    if catalog == 'short':
        return [(k, v) for k, v in _base_categ_mlist() if len(lmt2ulist(k)) > 2]
    return _base_categ_mlist()


def conv2__info():
    lmt = 'L'
    ulist = lmt2ulist(lmt)
    qlist = lmt2qlist(lmt)
    mode_list = _conv2_mode_list(qlist)

    return {
        'title': f'Unit Converter',
        'desc': '',
        'schema': {
            'catalog': {
                'type': 'choice', 'choices': {'short': 'Short', 'full': 'Full'},
                # | changing the catalog rebuilds the form, the quantity list follows it (see conv2__schema()),
                # | the listed fields are reset, 'mode' goes back to 'u2u' i.e. the only mode of the short catalog
                'reload': ['quantity', 'mode', 'from_unit', 'to_units', 'from_qty', 'to_qty', 'unit_cost'],
            },
            'quantity': {
                # | 'type':'qsel2' wouldn't trigger the reload, because select2 changes the element properties at runtime
                'type': 'choice', 'choices': _base_categ_mlist(),
                'initial': lmt,
                # | changing the quantity rebuilds the form, the lists and selections below follow it
                # | (see conv2__schema() and conv2__input()), 'mode' and the typed values are kept
                'reload': ['from_unit', 'to_units', 'from_qty', 'to_qty'],
            },
            'value': {'help_text': amount_help_text},
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
            # | no entry for 'catalog': it has a 'reload' trigger on 'change', the synthetic change event of the
            # | showhide init would rebuild the form again and again. In the short catalog 'mode' is a hidden field
            # | (see conv2__schema()), the visibility then depends on the catalog only
            'mode': {'fields': ['from_unit', 'from_qty', 'to_units', 'to_qty', 'unit_cost'], 'callback': 'conv2_sh'}
        },
        'calculate': 'Convert',
        'kins': 'conv',
        'script': '''
        function conv2_sh(v){
          const catalog = document.querySelector("[id$='_catalog']");
          if(catalog && catalog.value=='short'){
            return [true, false, true, false, false]  // unit -> unit without the cost
          }
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


def _conv2_catalog(ctx):
    # | what the user posted, else what the form starts with (defaults, memory, variant or url)
    def checked(value):
        value = str(value or '').lower()
        return value if value in ('short', 'full') else ''

    return checked(ctx.posted('catalog')) or checked(ctx.resolved('catalog')) or 'full'


def _conv2_lmt(ctx):
    # | the quantities which are not in the catalog are ignored, so are invalid values
    valid = dict(_conv2_categ_list(_conv2_catalog(ctx)))

    def checked(value):
        value = str(value or '').upper()
        return value if value in valid else ''

    return checked(ctx.posted('quantity')) or checked(ctx.resolved('quantity')) or 'L'


def conv2__schema(ctx):
    # | quantity, unit and quantity choices depend on the selected catalog and quantity (dimension)
    catalog = _conv2_catalog(ctx)
    lmt = _conv2_lmt(ctx)
    ulist = _conv2_ulist(lmt)
    qlist = lmt2qlist(lmt)
    # | the short catalog has no mode to choose, a hidden 'mode' keeps the value 'u2u' and the showhide init
    mode = {'type': 'qhide', 'choices': {'u2u': 'Unit -> Unit'}} if catalog == 'short' else \
        {'type': 'choice', 'choices': _conv2_mode_list(qlist)}
    return {
        'quantity': {'choices': _conv2_categ_list(catalog)},
        'mode': mode,
        'from_unit': {'choices': ulist},
        'to_units': {'choices': ulist},
        'from_qty': {'choices': qlist},
        'to_qty': {'choices': qlist},
    }


def conv2__input(ctx):
    # | default selections must be valid for the selected quantity
    lmt = _conv2_lmt(ctx)
    ulist = _conv2_ulist(lmt)
    qlist = lmt2qlist(lmt)
    inp = {'unit_cost': to_ucur('@UNC/ft')}
    if lmt == 'L':  # | explicit, because fargs may carry values set by a previous quantity
        inp.update(from_unit=['ft'], to_units=['m'], from_qty='l_earth_moon', to_qty='')
        return inp
    if ulist:
        inp['from_unit'] = [ulist[0][0]]
        inp['to_units'] = [ulist[1][0] if len(ulist) > 1 else ulist[0][0]]
    inp['from_qty'] = qlist[0][0] if qlist else ''
    inp['to_qty'] = ''
    return inp


def conv2(quantity='L', mode='u2u', value: qtexta = '1.0', from_unit=['ft'], from_qty='l_earth_moon',
          to_units=['m'], to_qty='', unit_cost: qtx = '@UNC/ft', catalog='short'):
    if catalog == 'short':  # | no unit cost either, whatever has been posted
        mode = 'u2u'
        unit_cost = '@UNC/ft'
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
        total_cost = None
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

    result = {
        'Conversion of': qhtml(f'{category}'),
        'Converting from': qhtml(ruf_out),
        'Converting to': qhtml(rut_out),
        'Converted Value': converted_value,
        'Total Cost': total_cost,
        'Expressed Value': qhtml(expressed_value)
    }
    if total_cost is None:  # | no unit cost, nothing to report
        del result['Total Cost']
    return result


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
        'images': {'top': ['calculators/all/measuring-tools.png']},
        'kins': 'conv2',
        'script': '''
            function convert_sh(v)
            {
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
        total_cost = None
    else:
        cur_used = find_matched_variables(unit_cost.uom.lower(), _unit_tree['C'])[0]
        total_cost = Qty(unit_cost * qvalue).to(cur_used)
    return conv_output(value, from_unit, inunits, xinunits,
                       converted_value, expressed_value, category, total_cost,
                       from_qty, convert_to_qty)
