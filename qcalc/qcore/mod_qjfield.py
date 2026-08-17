# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from qcore.mod_anno import *
from datetime import date, time as dt_time, datetime
import qutil as ut
from qvars import qc_gpref as gs
from qutil import QDateTime
import pandas as pd
from qcore import str_type, Qty


class QJField:  # 11422
    # | This class determines field type, field initial value and size of the field
    # | It considers function arguement annotation and assigned value if any
    # | It also considers type and initial value specified in the func_info schema
    # | annotation and assigned value gets priority over schema specifications
    def __init__(self, arg_name, arg_type=None, arg_value=None,
                 id_prefix='', required=False, inf_class='', sufx=''):
        self.name = arg_name
        self.id_prefix = id_prefix
        self.jf_ex: list[QJField] = []
        self.inf_class = inf_class
        self.jf = {
            'name': arg_name,
            'type': '',
            'initial': arg_value,
            'attrs': {'id': id_prefix + arg_name, 'class': ''},
            'required': required,
            'sufx': sufx,
        }
        self.mode = ''
        self.s2f = {'type': ''}
        self.c4f = {arg_name: 1}
        self.doc_info = {}

        if arg_type:
            self._ann2type(arg_type, arg_value)
        else:
            self._val2type(arg_value)

        if arg_type in [qtable, 'qtable', qtbl, 'qtbl']:
            self.jf['attrs']['class'] = inf_class
            # can be '', table-in or table-out
            # '' when not specified to change i.e. status quo
            self.doc_info['table_in'] = True
        else:
            acl = self.jf['attrs']['class']
            if acl in ['inp', 'val', 'chr'] and arg_name.endswith('_part'):
                acl = 'val-pp'

            self.jf['attrs']['class'] = ut.joinx([acl, self.inf_class])

    def _ann2type(self, arg_type, arg_value):
        if arg_type in [bool, 'boolean', 'bool']:
            self.jf['type'] = 'boolean'
        elif arg_type in [qchar, 'char']:
            self.jf['type'] = 'char'
            self.jf['attrs']['class'] = 'chr'
        elif arg_type in [qdate, 'date', 'qdate']:
            self.jf['type'] = 'date'
        elif arg_type in [qtime, 'time', 'qtime']:
            self.jf['type'] = 'time'
        elif arg_type in [qdatetime, 'datetime', 'qdatetime']:
            self.jf['type'] = 'datetime'
        elif arg_type in [qemail, 'email', 'qemail']:
            self.jf['type'] = 'email'
            self.jf['attrs']['class'] = 'inp'
        elif arg_type in [qfile, 'file', 'qfile']:
            self.jf['type'] = 'file'
            self.s2f['type'] = 'file'
            self.jf['attrs']['onchange'] = 'validateFileSize(this)'
        elif arg_type in [qfl, 'qfl']:
            self.jf['type'] = 'float'
            self.jf['attrs']['class'] = 'val-p'
        elif arg_type in [qfunc, 'qfunc', qhide, 'qhide']: # | pass the value to function call, e.g. __info
            self.jf['type'] = 'hidden'
        elif arg_type in [qhidex, 'qhidex']:
            self.jf['type'] = 'hidden'
            self.s2f = {'type': 'x'}  # | do not pass the value to function call, e.g. --#
        elif arg_type in [qimage, 'image', 'qimage']:
            self.jf['type'] = 'image'
            self.s2f['type'] = 'image'
            self.jf['attrs']['onchange'] = 'validateFileSize(this)'
        elif arg_type in [qin, 'qin']:
            self.jf['type'] = 'integer'
            self.jf['attrs']['class'] = 'val-p'
        elif arg_type in [float, 'float']:
            self.jf['type'] = 'float'
            self.jf['attrs']['class'] = 'val'
        elif arg_type in [int, 'integer', 'int']:
            self.jf['type'] = 'integer'
            self.jf['attrs']['class'] = 'val'
        elif arg_type in [qread, 'qread']:
            self.jf['type'] = 'read'
            self.jf['attrs']['class'] = 'chr'
        elif arg_type in [qregex, 'regex', 'qregex']:
            self.jf['type'] = 'regex'
            self.jf['attrs']['class'] = 'inp'
        elif arg_type in [qreq, 'qreq']:  # | should not be used
            self.jf['initial'] = "__req__"
            self.jf['type'] = 'hidden'
        elif arg_type in [str, 'text', 'str', qtext, 'qtext']:
            self.jf['type'] = 'text'
            self.jf['attrs']['class'] = 'inp'
        elif arg_type in [qsel2, 'select2', 'qsel2']:
            self.jf['type'] = 'select2'
            self.jf['attrs']['class'] = 'select2 inp'
            self.doc_info['qsel2'] = True
        elif arg_type in [qtexta, 'textarea', 'qtexta']:
            self.jf['type'] = 'textarea'
            self.jf['attrs']['class'] = 'texta'
        elif arg_type in [qtexte, 'textedit', 'qtexte']:
            self.jf['type'] = 'textedit'
            self.jf['attrs']['class'] = 'texte'
        elif arg_type in [qcode, 'codeedit', 'qcode']:
            self.jf['type'] = 'codeedit'
            self.jf['attrs']['class'] = 'code'
        elif arg_type in [qtime, 'time', 'qtime']:
            self.jf['type'] = 'time'
        elif arg_type in [quom, 'quom', 'uom', 'uomx', 'quomx']:
            self._str2uom(arg_value)  # uom_interface from global setting
        elif arg_type in [quom2, 'quom2', 'uom2']:
            self._str2uom(arg_value, 'uom2')
        elif arg_type in [qt, 'qt']:
            self._str2qt(arg_value)  # uom_interface from global setting
        elif arg_type in [qtx, 'qtx']:
            self._str2qt(arg_value, 'uomx')
        elif arg_type in [qt2, 'qt2']:
            self._str2qt(arg_value, 'uom2')
        elif arg_type in [qtc, 'qtc']:  # composite of 2+ fields
            self._str2qtc(arg_value)
        elif arg_type in [qtc2, 'qtc2']:  # composite of 2+ fields
            self._str2qtc(arg_value, 'uom2')
        elif arg_type in [quomx, 'quomx']:
            self.jf['type'] = 'uomx'
            self.jf['attrs']['class'] = 'uom'
        elif arg_type in [qurl, 'url', 'qurl']:
            self.jf['type'] = 'url'
            self.jf['attrs']['class'] = 'inp'
        elif arg_type in qlist_types:  # composite of N fields
            self.doc_info['qlist'] = True
            self._list2jflds(arg_value, arg_type)
        elif arg_type in [qdict, 'qdict']:  # composite of N fields
            self.c4f[self.name] = len(arg_value)
        elif arg_type in [qtable, 'qtable']:  # composite of 4 fields
            self._table2flds(arg_value, 'table')
        elif arg_type in [qtbl, 'qtbl']:  # composite of 4 fields, plain dict not DataFrame
            self._table2flds(arg_value, 'tbl')
        elif arg_type == 'float-q':  # special
            self.jf['type'] = 'float'
            self.jf['attrs']['class'] = 'val-q'
        elif arg_type == 'float-pq':  # special
            self.jf['type'] = 'float'
            self.jf['attrs']['class'] = 'val-pq'
        elif arg_type == 'integer-q':  # special
            self.jf['type'] = 'integer'
            self.jf['attrs']['class'] = 'val-q'
        elif arg_type == 'integer-pq':  # special
            self.jf['type'] = 'integer'
            self.jf['attrs']['class'] = 'val-pq'
        elif arg_type == 'uom-q':  # special
            self.jf['type'] = 'uom'
            self.jf['attrs']['class'] = 'uom-q'
        elif arg_type == 'uom-pq':  # special
            self.jf['type'] = 'uom'
            self.jf['attrs']['class'] = 'uom-pq'
        elif arg_type == 'uomx-q':  # special
            self.jf['type'] = 'uomx'
            self.jf['attrs']['class'] = 'uom-q'
        elif arg_type == 'uomx-pq':  # special
            self.jf['type'] = 'uomx'
            self.jf['attrs']['class'] = 'uom-pq'
        elif arg_type == 'uom2-q':  # special
            self.jf['type'] = 'uom2'
            self.jf['attrs']['class'] = 'select2 uom-q'
        elif arg_type == 'uom2-pq':  # special
            self.jf['type'] = 'uom2'
            self.jf['attrs']['class'] = 'select2 uom-pq'
        elif isinstance(arg_type, str) and arg_type.startswith('btn'):  # special
            self.s2f = {'type': 'x'}
            self.jf['type'] = arg_type
            # self.jf['attrs']['class'] = 'btn'
        # | display output types
        elif arg_type in [qhtml, 'html', 'qhtml']:
            self.jf['type'] = 'html'
        elif arg_type in ['checkbox', 'boolean']:
            self.jf['type'] = arg_type
            self.jf['required'] = False
        elif arg_type in ['choice', 'multiplechoice']:
            self.jf['type'] = arg_type
            self.jf['attrs']['class'] = 'inp'
        elif arg_type in ['checkboxselectmultiple']:
            self.jf['type'] = arg_type
            self.jf['attrs']['class'] = 'mcheck'
        elif arg_type in ['radio']:
            self.jf['type'] = arg_type
            self.jf['attrs']['class'] = 'radio'
        elif arg_type in ['combo', 'decimal', 'duration', 'filepath', 'multiplechoice',
                          'multivalue', 'nullboolean', 'range', 'rchoice', 'slug',
                          'splitdatetime', 'uuid']:  # some are not tested
            self.jf['type'] = arg_type
        else:
            raise Exception(f'Error (QJF): Unknown type [{arg_type}]')

    def _val2type(self, arg_value):
        if arg_value is None:
            self.jf['type'] = 'float'  # or 'char?'
            self.jf['attrs']['class'] = 'unknown'
        elif isinstance(arg_value, float):
            self.jf['type'] = 'float'
            self.jf['attrs']['class'] = 'val'
        elif type(arg_value) is bool:
            # | isinstance(True, bool) = True, isinstance(True, int) = True!
            self.jf['type'] = 'checkbox'
        elif type(arg_value) is int:
            # | isinstance(True, int) = True!
            self.jf['type'] = 'integer'
            self.jf['attrs']['class'] = 'val'
        elif isinstance(arg_value, date) and not isinstance(arg_value, datetime):
            self.jf['type'] = 'date'
        elif isinstance(arg_value, dt_time):
            self.jf['type'] = 'time'
        elif isinstance(arg_value, datetime):
            self.jf['type'] = 'datetime'
        elif isinstance(arg_value, QDateTime):
            if arg_value.is_date:
                self.jf['type'] = 'date'
            elif arg_value.is_datetime:
                self.jf['type'] = 'datetime'
            elif arg_value.is_time:
                self.jf['type'] = 'time'
            self.jf['initial'] = arg_value.val
        elif isinstance(arg_value, str):
            self._str2type(arg_value)
        elif isinstance(arg_value, list):
            self.jf['type'] = 'multiplechoice'
            self.jf['attrs']['class'] = 'unknown'
        elif isinstance(arg_value, pd.DataFrame):
            self._table2flds(arg_value, 'table')
        else:
            raise TypeError(f'Error (FTFS): argument {self.name} type [{type(arg_value)}] not supported')

    def _str2uom(self, value, uom_interface=None):
        # arg_type in ['uom', 'quom', 'uom2', 'quom2']
        # uom_interface can be 'uom2', 'uom', 'uomx'
        value = '' if value is None else value.strip()
        if uom_interface is None:
            uom_interface = 'uom2' if gs['uom_v2'] else 'uom'

        if uom_interface == 'uom2':
            self.jf['attrs']['class'] = 'select2 uom'
        else:
            self.jf['attrs']['class'] = 'uom'
        self.jf['type'] = uom_interface  # 'uom'
        self.jf['initial'] = value

    def _str2qt(self, value, uom_interface=None):  # arg_type in ['qt']
        value = '' if value is None else value.strip()
        if uom_interface is None:
            uom_interface = 'uom2' if gs['uom_v2'] else 'uom'
        ln = len(value.split(','))
        full_part = '-pq' if ln > 1 else '-q'
        uom_type = uom_interface + full_part

        self.s2f['type'] = 'qty'
        self.s2f['parts'] = ln  # fields to combine
        self.c4f[self.name] = ln * 2
        qval = ut.css2strs(value)
        for j in range(ln):
            namej = self.name + '_' + str(j + 1) + '_part' if j > 0 else self.name
            typej = 'float' if j == ln - 1 else 'integer'
            type_sizej = typej + full_part
            var_qt = Qty(qval[j])
            if j > 0:
                self.jf_ex.append(QJField(namej, type_sizej, var_qt.val, self.id_prefix))
            else:
                self.jf['type'] = typej
                self.jf['initial'] = var_qt.val
                self.jf['attrs']['class'] = 'val' + full_part

            if j == 0 and ln == 1:
                namej = self.name + '_uom'
            elif j == 0 and ln > 1:
                namej = self.name + '_part_uom'
            else:
                namej = self.name + '_' + str(j + 1) + '_part_uom'
            self.jf_ex.append(QJField(namej, uom_type, var_qt.uom, self.id_prefix, True))

    def _str2qtc(self, value, uom_interface=None):  # arg_type in ['qt']
        value = '' if value is None else value.strip()
        if uom_interface is None:
            uom_interface = 'uom2' if gs['uom_v2'] else 'uom'
        ln = len(value.split(','))
        full_part = '-pq' if ln > 1 else '-q'
        uom_type = uom_interface + full_part

        # self.s2f['type'] = 'qty'
        self.s2f['type'] = 'c'
        # self.s2f['parts'] = ln  # fields to combine
        # self.c4f[self.name] = ln * 2
        qval = ut.css2strs(value)
        self.jf['type'] = 'qty'
        self.jf['initial'] = value
        self.jf['attrs']['class'] = ''

        vals = []
        for j in range(ln):
            namej = self.name + '_' + str(j + 1) + '_part' if j > 0 else self.name
            sufxj = str(j + 1) + '_part' if j > 0 else ''
            typej = 'float' if j == ln - 1 else 'integer'
            type_sizej = typej + full_part
            var_qt = Qty(qval[j])
            self.jf_ex.append(QJField(namej, type_sizej, var_qt.val, self.id_prefix, sufx=sufxj))
            vals.append(var_qt.val)

            if j == 0 and ln == 1:
                namej = self.name + '_uom'
                sufxj = 'uom'
            elif j == 0 and ln > 1:
                namej = self.name + '_part_uom'
                sufxj = 'part_uom'
            else:
                namej = self.name + '_' + str(j + 1) + '_part_uom'
                sufxj = str(j + 1) + '_part_uom'
            self.jf_ex.append(QJField(namej, uom_type, var_qt.uom, self.id_prefix, True, sufx=sufxj))
            vals.append(var_qt.uom)

        self.jf['initial'] = None  # vals

    def _str2type(self, value):
        value = value.strip()
        # | if string length is >96 it will quickly return as a non-qty string
        otype, sunit, ln = str_type(value)
        uom_interface = 'uom2' if gs['uom_v2'] else 'uom'
        if otype == 'uom':
            self._str2uom(value, uom_interface)
        elif otype == 'qty':
            self._str2qt(value, uom_interface)
        elif otype == 'qtc':
            self._str2qtc(value, uom_interface)
        elif not (5 <= len(value) <= 32):
            # | if string length is not between 5-32 chars it will return as string
            self.jf['type'] = 'text'  # type='char'
            self.jf['attrs']['class'] = 'unknown'
            self.jf['initial'] = value
        else:
            # | a potential iso datetime string can be between 5-32 characters
            qdate = QDateTime(value)
            if qdate.dt_value is None:
                self.jf['type'] = 'text'  # type='char'
                self.jf['attrs']['class'] = 'unknown'
                self.jf['initial'] = value
            elif qdate.is_date:
                # print('date', value)
                self.jf['type'] = 'date'
                self.jf['initial'] = value
            elif qdate.is_time:
                # print('time', value)
                self.jf['type'] = 'time'
                self.jf['initial'] = value
            elif qdate.is_datetime:
                # print('datetime', value)
                self.jf['type'] = 'datetime'
                self.jf['initial'] = value
            else:
                self.jf['type'] = 'text'  # type='char'
                self.jf['attrs']['class'] = 'unknown'
                self.jf['initial'] = value

    def _list2jflds(self, value, arg_type):
        if value:
            arr_size = len(value)
        else:
            arr_size = 1
            value = ['']

        self.s2f['type'] = 'qlist'
        self.c4f[self.name] = arr_size
        self.name_prefix = self.name
        for j in range(arr_size):
            if j > 0:
                namej = f'{self.name_prefix}_{j}'  # 0 based
                self.jf_ex.append(QJField(namej, qlist_types[arg_type][1], value[j], self.id_prefix))
                self.jf_ex[-1].jf['attrs']['class'] = qlist_types[arg_type][2]
            else:
                self.jf['type'] = qlist_types[arg_type][0]
                self.jf['initial'] = value[j]
                self.jf['attrs']['class'] = qlist_types[arg_type][2]

        self.jf_ex.append(QJField(f"list_add_{self.name_prefix}",
                                  "btn:0", "+", self.id_prefix))
        self.jf_ex.append(QJField(f"list_del_{self.name_prefix}",
                                  "btn:0", "-", self.id_prefix))

    def _table2flds(self, _value, s2f_type='table'):
        self.doc_info['xpr'] = False
        self.doc_info['url'] = False
        self.doc_info['loop'] = False
        self.jf['type'] = 'table'
        self.s2f = {'type': s2f_type}  # 'table' -> DataFrame, 'tbl' -> plain dict
