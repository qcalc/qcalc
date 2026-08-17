# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import io
import json
# from django.http import HttpRequest
import pandas as pd
from .mod_qfile import QFile
from .qc_qty import Qty
from qutil import HtmxHttpRequest


class qchar(str):  # char 50
    def __init__(self):
        pass


class qfl(float):  # float short field width
    def __init__(self):
        pass


class qin(int):  # int short field width
    def __init__(self):
        pass


class qdate(str):
    def __init__(self):
        pass


class qdatetime(str):
    def __init__(self):
        pass


class qemail(str):
    def __init__(self):
        pass


class qfile(QFile):  # file 2 MB
    pass
    # def __init__(self):
    #     pass


class qimage(QFile):  # file 2 MB
    pass
    # def __init__(self):
    #     pass


class qfunc(str):  # qcalc function
    def __init__(self):
        pass


class qhide(str):  # | pass the value to function call but do not display the field, e.g. func, __info
    def __init__(self):
        pass


class qhidex(str):  # | do not pass the value to function call and do not display the field, e.g. --#
    def __init__(self):
        pass


class qread(str):  # read 50
    def __init__(self):
        pass


class qregex(str):
    def __init__(self):
        pass


class qtext(str):  # text 255
    def __init__(self):
        pass


class qtexta(str):  # textarea 65535
    def __init__(self):
        pass


class qtexte(str):  # textedit 65535
    def __init__(self):
        pass


class qcode(str):
    def __init__(self):
        pass


class qtime(str):
    def __init__(self):
        pass


class quom(str):  # ft
    def __init__(self):
        pass


class quomx(str):  # ft, kg, m2 any valid unit
    def __init__(self):
        pass


class qurl(str):  # read 255
    def __init__(self):
        pass


class qsel2(str):
    def __init__(self):
        pass


class quom2(str):
    def __init__(self):
        pass


class qtx(str):  # val+any uom
    def __init__(self):
        pass


class qt(str):  # val+uom
    def __init__(self):
        pass


class qt2(str):  # val+uom2
    def __init__(self):
        pass


class qtc(str):  # composite qty field with choice widget
    def __init__(self):
        pass


class qtc2(str):  # composite qty field with select2 widget
    def __init__(self):
        pass


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


class qdict(dict):  # dynamic addition/deletion not possible
    pass
    # def __init__(self):
    #     pass


class qtable(pd.DataFrame):  # pd.DataFrame
    pass
    # def __init__(self):
    #     pass


class qtbl(dict):  # {'columns': [...], 'data': [[...]]} - safe table, no DataFrame API exposed
    pass


# display output fields
class oqfunc(str):
    def __init__(self, _sfunc):
        pass


class qhtml(str):
    def __init__(self, _html):
        pass


class qvstr(str):  # value string, loop ok
    def __init__(self, _vstr):
        pass


class qpage(str):  # page of text
    def __init__(self, _txt):
        pass


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
