# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import io
import json
import pandas as pd
from .mod_qfile import QFile
from .qc_qty import Qty
from qutil import HtmxHttpRequest


# Short character input field up to 50 characters.
class qchar(str):  # char 50
    def __init__(self):
        pass


# Floating-point short input field
class qfl(float):  # float short field width
    def __init__(self):
        pass


# Integer short input field
class qin(int):  # int short field width
    def __init__(self):
        pass


# Date input field.
class qdate(str):
    def __init__(self):
        pass


# Date-and-time input field.
class qdatetime(str):
    def __init__(self):
        pass


# Email address input field.
class qemail(str):
    def __init__(self):
        pass


# File upload field with a 2 MB limit.
class qfile(QFile):  # file 2 MB
    pass
    # def __init__(self):
    #     pass


# Image upload field with a 2 MB limit.
class qimage(QFile):  # file 2 MB
    pass
    # def __init__(self):
    #     pass


# qCalc function field.
class qfunc(str):  # qcalc function
    def __init__(self):
        pass


# Hidden field, pass the value to function call but do not display the field, e.g. func, __info
class qhide(str):  
    def __init__(self):
        pass


# Hidden field whose value is omitted from the function call.
# Do not pass the value to function call and do not display the field, e.g. --#
class qhidex(str):  
    def __init__(self):
        pass


# Read-only text input field up to 50 characters.
class qread(str):  # read 50
    def __init__(self):
        pass


# Regular-expression input field.
class qregex(str):
    def __init__(self):
        pass


# Text input field with a 255-character limit.
class qtext(str):  # text 255
    def __init__(self):
        pass


# Multi-line text input field with a 65535-character limit.
class qtexta(str):  # textarea 65535
    def __init__(self):
        pass


# Rich text editor input field with a 65535-character limit.
class qtexte(str):  # textedit 65535
    def __init__(self):
        pass


# Source-code editor input field.
class qcode(str):
    def __init__(self):
        pass


# Time input field.
class qtime(str):
    def __init__(self):
        pass


# Compatible unit input for a specific dimension such as length, weight, or pressure.
# No search and select drop-down is provided; the unit must be entered manually.
class quom(str):  # ft
    def __init__(self):
        pass


# Unit input accepting any valid unit such as ft, kg, or m2.
# No search and select drop-down is provided; the unit must be entered manually.
class quomx(str):
    def __init__(self):
        pass


# URL input field up to 255 characters.
class qurl(str):  # read 255
    def __init__(self):
        pass


# Text input field, search and select from drop-down
class qsel2(str):
    def __init__(self):
        pass


# Unit input field, search and select from drop-down
# Only compatible units for a specific dimension such as length, weight, or pressure are displayed in the drop-down.
class quom2(str):
    def __init__(self):
        pass


# Quantity input accepting value and any valid unit.
class qtx(str):  # val+any uom
    def __init__(self):
        pass


# Quantity input containing a value and a valid unit using simple interface.
# Could be single or multipart quantity input.
# If explicitly not specified, the default unit selection interface is select2 (improved selection) unless otherwise changed by the global preference setting uom_v2
class qt(str):  # val+uom
    def __init__(self):
        pass


# Quantity input using the select2 (improved selection) unit interface.
# Could be single or multipart quantity input.
# If explicitly not specified, the default unit selection interface is select2 (improved selection) unless otherwise changed by the global preference setting uom_v2
class qt2(str):  # val+uom2
    def __init__(self):
        pass


# Composite quantity input containing a value and a valid unit.
# Could be single or multipart quantity input.
# Experimental, use the 'qt' type instead.
class qtc(str):  # composite qty field with choice widget
    def __init__(self):
        pass


# Composite quantity input using select2 (improved selection) interface.
# Experimental, use the 'qt2' type instead.
class qtc2(str):  # composite qty field with select2 widget
    def __init__(self):
        pass


# Dynamic list input allowing item addition and deletion.
# List values can be of type float, int, str, qtexta, or qchar.
class qlist(list):  # dynamic addition/deletion possible
    pass
    # def __init__(self):
    #     pass


qlist_types = {
    qlist: ('float', float, 'val'),
    qlist[float]: ('float', float, 'val'),
    qlist[int]: ('integer', float, 'val'),
    qlist[str]: ('char', qchar, 'inp'),
    qlist[qtexta]: ('textarea', qtexta, 'texta'),
    qlist[qchar]: ('char', qchar, 'chr'),
}


# Fixed dictionary field whose items cannot be added or deleted.
class qdict(dict):  # dynamic addition/deletion not possible
    pass
    # def __init__(self):
    #     pass


# Editable table input backed by a DataFrame. Not available for front-end calculator
class qtable(pd.DataFrame):  # pd.DataFrame
    pass
    # def __init__(self):
    #     pass


# Safe table field represented by columns and row data without exposing the DataFrame API.
class qtbl(dict):  # {'columns': [...], 'data': [[...]]} - safe table, no DataFrame API exposed
    pass


# display output fields
# Display output field containing a QCalc function result.
class oqfunc(str):
    def __init__(self, _sfunc):
        pass


# Display output field containing HTML markup.
class qhtml(str):
    def __init__(self, _html):
        pass


# Display output field containing a loop-safe value string.
class qvstr(str):  # value string, loop ok
    def __init__(self, _vstr):
        pass


# Display output field containing a page of text.
class qpage(str):  # page of text
    def __init__(self, _txt):
        pass


# HTTP request field for HTMX requests; reserved and generally unused.
class qreq(HtmxHttpRequest):  # | should not be used
    def __init__(self):
        super().__init__()
        pass


class QScreen:
    def __init__(self):
        self.out = io.StringIO()

    def write(self, *args):
        print(*args, file=self.out)

    def flush(self):
        contents = qpage(self.out.getvalue())
        self.out.close()
        return contents


def convert_to_type(value, target_type):
    try:
        if target_type is None:
            return float(value)
        elif target_type in [int, qin]:
            return int(value)
        elif target_type in [float, qfl]:
            return float(value)
        elif target_type == bool:
            return bool(value)
        elif target_type == qtable:
            try:
                value = json.loads(value)
                return pd.DataFrame(data=value['data'], columns=value['columns'])
            except Exception as e:
                e.args = (f'Error (C2T): Invalid value for table',)
                raise e
        elif target_type == qtbl:
            try:
                return json.loads(value)
            except Exception as e:
                e.args = (f'Error (C2T): Invalid value for tbl',)
                raise e
        elif target_type in [
            str, qchar, qemail, qtext, qtexta, qtexte,
            qread, qcode, qurl, qsel2
        ]:
            return str(value)
        elif target_type in [
            quom, quomx, quom2, qtx, qt, qt2, qtc, qtc2
        ]:
            return Qty(value)
        else:
            return value
    except (ValueError, TypeError):
        return value


def wrap_actions(html_element):
    return f"""<div class="elem-wrapper">{html_element}
    <span class="fullscreen-square" onclick="toggleFullscreen(this.closest('.elem-wrapper'))"></span></div>"""


def _test():
    x = qhtml(2)
    print(type(x) is qhtml)
    print(type(x), isinstance(x, qhtml))
    print(x + '2')

    x = qpage('hello')
    print(type(x) is qpage)
    print(type(x), isinstance(x, qpage))
    print(x)


if __name__ == '__main__':
    _test()
