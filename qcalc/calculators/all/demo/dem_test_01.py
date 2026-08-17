# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from math import pi
from calculators.all.fun.cal_img2ascii import qf2img
from calculators.all.general.chart.cal_chart import pie_chart, line_chart, scatter_chart, line2_chart
from calculators.all.engineering.surveying.cal_survey import rectland
from calculators.all.mathematics.geometry.cal_circle import circle
from calculators.all.health.cal_bmi import bmi
from calc import QList
from qutil import cal_link, resize_df, to_df, command_button, calurl
import time
from calculators.all.general.cal_conv import conv2
from qcore.mod_anno import *


def demo_adda__modify(arg_name, arg_value, _action):
    if arg_name == 'y':
        return arg_value ** 2
    else:
        return arg_value


def demo_adda__info():
    return {
        'title': 'Testing Callback',
        'inserts': {
            'form_bottom': command_button('demo_adda', 'Y**2', '__modify', args=['y'])  # not good for scripting
        }
    }


def demo_adda(x=3, y=2):
    return x + y


def demo_addat__modify(arg_name, arg_value, _action):
    if arg_name == 'y':
        return arg_value + 'hi'
    else:
        return arg_value + 'lo'


def demo_addat__info():
    return {
        'title': 'Testing Callback',
        'inserts': {
            'form_bottom': command_button('addat', 'Load', '__modify', args=['y'])  # not good for scripting
        }
    }


def demo_addat(x: str = '3', y: str = '2'):
    return x + y


def demo_anno2__info():
    return {
        'title': 'Test Annotation (explicit)'
    }


def demo_anno2(u: quom = 'kg', u2: quom2 = 'g', q: qt = '1 ft', q2: qt2 = '1 ft'):
    return u, u2, q, q2


def demo_anno__info():
    return {
        'title': 'Test Annotation (implicit)'
    }


def demo_anno(u='kg', u2='g', q='1 ft', q2='1 ft'):
    return u, u2, q, q2


def demo_table2__info():
    df_x = pd.DataFrame(columns=['Name', 'Age', 'Salary', 'Joined'],
                        data=[['', 0, 0, '2001-01-01'] for i in range(10)])
    # df_x.columns['Age'].astype(int)
    # df_x.columns['Salary'].astype(float)
    # df_x.columns['Joined'].astype(date)
    return {
        'title': 'Testing Table',
        'schema': {
            'x': {'initial': df_x},
            'tsel': QList.get("test")
        },
        'col': ['x', 'y'],
        # 'endcol': ['table_del_x', 'table_del_y'],
    }


def demo_table2(x: qtable,
            y: qtable = pd.DataFrame(columns=['Last Name', 'Team Name', 'Play Score'], index=range(5)),
            tfloat=5.5, tint=2, tbool=True, tdate: qdate = '2024-02-17', tstr: str = 'hello',
            tsel='D',
            z: qtable = resize_df(pd.DataFrame(data=[], columns=[]), 3, 2)
            ):
    # print('x:', x)
    # print('y:', y)
    return y, x, y, z, (tfloat, tint, tbool, tdate, tstr)


def demo_table__info():
    df_x = pd.DataFrame(columns=['Name', 'Age', 'Salary', 'Joined'],
                        data=[['', 0, 0, '2001-01-01'] for i in range(10)])
    # df_x.columns['Age'].astype(int)
    # df_x.columns['Salary'].astype(float)
    # df_x.columns['Joined'].astype(date)
    return {
        'title': 'Testing Table',
        'schema': {
            'x': {'initial': df_x},
            'tsel': QList.get("test")
        },
        'col': ['x', 'y'],
        # 'endcol': ['table_del_x', 'table_del_y'],
    }


def demo_table(x: qtable,
           y: qtable = pd.DataFrame(columns=['Name', 'Team', 'Score'], index=range(5)),
           tfloat=5.5, tint=2, tbool=True, tdate: qdate = '2024-02-17', tstr: str = 'hello',
           tsel='D',
           z: qtable = resize_df(pd.DataFrame(data=[], columns=[]), 3, 2)
           ):
    # print('x:', x)
    # print('y:', y)
    return x, y, z, (tfloat, tint, tbool, tdate, tstr)


def demo_date__info():
    return {
        'title': 'Testing Date',
    }


def demo_date(future: qdate = '2025-12-31', past='1924-01-01'):
    # print(QDateTime(future).date, QDateTime(past).date)
    # print(future, past)
    return future - past


def demo_uom__info():
    return {
        'title': 'Testing lone uom',
        # 'beside': ['x', 'y', 'z']
    }


def demo_uom(x_uom='ft'):
    return {'Length Uom': x_uom}


def demo_dict__info():
    return {'title': 'Testing Dict'}


def demo_dict(x={"x": 10, "y": 'hello', "z": '30 ft', "w": {'a': 2, 'b': 3}}):
    # x: qdict = {"x": 10, "y": 'hello', "z": '30 ft', "w": {'a': 2, 'b': 3}}
    # x: qdict = {"x": 10, "y": 'hello', "z": '30 ft'}
    # 'x--#': 'x', 'x--x': 10, 'x--y': 'hello', 'x--z': 30.0, 'x--z_uom': 'ft', 'x--w--a': 2, 'x--w--b': 6
    # x--#= 'x', x--x= 10, x--y= 'hello', x--z= 30.0, x--z_uom= 'ft', x--w--a= 2, x--w--b= 6
    t = Qty(x['z']) / x['x']
    v = x['w']['a'] + x['w']['b']
    return x['y'], t, v


def demo_arr__info():
    return {'title': 'Testing Array'}


def demo_arr(x: qlist = [10, 20, 30]):
    return x, sum(x)


def demo_arr2__info():
    return {
        'title': 'Testing Array2',
        'outcol': 'result',
    }


def demo_arr2(x: qlist = [100, 200, 300],
          y: qlist = [10, 20, 30],
          z: qlist = [50, 60, 70]):
    return sum(x), sum(y), sum(z)


def demo_personal_list__info():
    return {
        'schema': {
            'x': QList.get("test")
        }
    }


def demo_personal_list(x):
    return x


def demo_conv3__info():
    return {}


def demo_conv3(f: qfunc = conv2):
    return f


def demo_cntry__info():
    return {
        'schema': {
            'country': QList.getx("country", initial='BD')
        }
    }


def demo_cntry(country):
    return country


def demo_rfunc__info():
    return {}


def demo_rfunc(sfunc: str):
    qf = oqfunc(sfunc)
    return qf


def demo_hide__info():
    return {
        'showhide': {'__': {'fields': ['t', 'u']}},
        'fargs': {'t': 300},
    }


def demo_hide(x=5, y: qhide = 3, z=100.5, t: float = 200, u='5ft'):
    return {'x': x, 'y1': y + 1, 'z': z, 't1': t + 1, 'u': u}


def demo_cal2__info():
    return {
        'title': 'Cal Calling Cal',
        'col': ['c-b', 'r2-anytext'],
    }


def demo_cal2(c: qfunc = circle, r: qfunc = rectland, b: qfunc = bmi, r2: qfunc = 'sunrise',
          anyfile: qfile = None, anytext: qtexta = "Hi'ya there"):
    # print(c, r)
    area = c['Area'] + r['Area']
    return {'Combined Area': area, 'BMI': b['BMI'], 'sunsrise': r2, 'anytext': anytext}


def demo_out__info():
    return {
        'outcol': ['html__r', 'chart__r', 'table__r', 'code__r'],
    }


def demo_out():
    return {
        'single value': 100,
        'list of values': [1, 2, 3],
        'touple of values': [1, 2, 3],
        'dict': {'name': 'Dave', 'Age': 25, 'Male': True},
        'dict of dict': {
            'boy': {'name': 'Dave', 'Age': 25, 'Male': True},
            'girl': {'name': 'Arche', 'Age': 20, 'Male': False}
        },
        'html': qhtml('<b>Hello World</b>'),
        **pie_chart(),
        'table': pd.DataFrame([1, 2, 3], columns=['fact']),
        'code': qpage("print('Hello World')"),
    }


def demo_sleep___info():
    return {}


def demo_sleep_(a='10 ft', b='20 ft', sleep=15):
    a = Qty(a)
    b = Qty(b)
    time.sleep(sleep)
    c = a + b
    return c


def demo_conv__info():
    return {}


def demo_conv(x=5, y='', z='unc', t='1 ft2', w='kg'):
    return x, y, z, t, w


def demo_prsc__info():
    return {
        'title': 'Print on Screen Demo'
    }


def demo_prsc(n=10):
    sum = 0
    out = QScreen()
    out.write('Demo of print output', n)
    for i in range(n):
        sum += i
        out.write(i, sum)
    out.write(f'Demo ends after {n} run')
    out.write('\n<h1>Thanks</h1>')
    out.write('-----------')
    return out.flush()


def demo_html__info():
    return {}


def demo_html(calculator='thtml', a='5ft', b='6m'):
    url = qhtml("<a href='https://www.google.com' target='_blank'>Google</a>")
    message = qhtml("<span>Hello World </span> <b>hey there</b>")
    c = Qty(a) + Qty(b)
    # print(calculator + f'/a/{str(c)}')
    url2 = qhtml(cal_link(calurl(calculator, f'a/{str(c)}'), button=True))
    # print(url2)
    # QMem.setf2(request, calculator, 'input', {'a': str(c), 'b': '3m'})
    d = Qty(a) * Qty(b)
    # requests.get(url)
    # print(request)
    return {'url': url, 'url2': url2, 'message': message, 'c': qhtml(c), 'd': d}


def demo_ftype__info():
    return {}


def demo_ftype(b: bool, i: int, f: float, s: str, v, un='ft', qt='1 g'):
    return


def demo_imec__info():
    return {}


def demo_imec(x=12.0, x_uom='h'):
    xq = Qty(x, x_uom)
    return xq.in_units_of('s', 'min', 'h', 'd', 'wk', 'mo', 'yr')


def demo_imex__info():
    return {}


def demo_imex(x=12.0, x_uom='h'):
    xq = Qty(x, x_uom)
    return xq.to_units('s, min, h, d, wk, mo, yr')


def demo_estf__info():
    return {}


def demo_estf(x=5.0, x_uom='m', y=12.0, y_uom='m', z=5.0, t=3.0, zz=9.0, zz_uom='ft/s', pp=3.0, qq=8.0, qq_uom='g/s',
          tt=3.0,
          tt_uom='kg/ft'):
    qx = Qty(x, x_uom, 'ft')
    qy = Qty(y, y_uom, 'ft')
    return qx + qy


def demo_ftable__info():
    return {}


def demo_ftable():
    data = {
        "calories": [420, 380, 390],
        "duration": [50, 40, 45]
    }
    df = pd.DataFrame(data)
    return df  # .to_html(table_id='test_table')  # , classes=["table-bordered", "table-striped", "table-hover"])


def demo_fchart__info():
    return {}


def demo_fchart():
    # chart = PieChart({'Blueberry': 44, 'Strawberry': 23}, width='200px', height='200px')
    # data = [
    #     {'name': 'Workout', 'data': {'2021-01-01': 3, '2021-01-02': 4}},
    #     {'name': 'Call parents', 'data': {'2021-01-01': 5, '2021-01-02': 3}}
    # ]
    # chart = LineChart(data, width='100%')
    chart = line2_chart('20210101, 20210102', '3, 4', '2, 3')
    # print(type(chart)) # class 'chartkick.django.LineChart'
    return chart


def demo_xchart__info():
    return {}


def demo_xchart():
    c1 = pie_chart()
    a = Qty('10 ft')
    c2 = line_chart()
    c3 = scatter_chart()
    x = 5
    return {
        'c1': c1['chart'],
        'a': a,
        'c2': c2['chart'],
        'c3': c3['chart'],
        'x': x
    }


def demo_ximage__info():
    return {}


def demo_ximage(img1: qfile, img2: qfile):
    x = 5
    q1 = qf2img(img1)
    q2 = qf2img(img2)
    return {
        'img1': q1,
        'img2': q2,
        'x': x
    }


def demo_xtable__info():
    return {}


def demo_xtable(csv1: qfile, csv2: qfile):
    x = 5
    q1 = to_df(csv1.txt_buf())
    q2 = to_df(csv2.txt_buf())
    return {
        'tbl1': q1,
        'tbl2': q2,
        'x': x
    }


def demo_bmi1__info():
    return {}


def demo_bmi1(weight='59.0 kg, 500.0 g', body_height='5.0 ft, 6 inch'):
    weight_kg = Qty(weight, 'kg')
    height_m = Qty(body_height, 'm')
    # print(weight_kg, height_m)
    bmi_kgpm2 = weight_kg / height_m ** 2
    return {'BMI': bmi_kgpm2}


def demo_bmi0__info():
    return {}


def demo_bmi0(weight=60, weight_uom='kg', height=5.5, height_uom='ft'):
    """Calculate Body Mass Index."""
    weight_kg = Qty(weight, weight_uom, 'kg')
    # weight_kg.to('kg')
    height_m = Qty(height, height_uom, 'm')
    # height_m.to('m')
    bmi_kgpm2 = weight_kg / height_m ** 2
    return {'BMI': bmi_kgpm2}


def demo_circle0__info():
    return {}


def circle0(radius='10ft', dia='@ft', circumference='@ft', area='@ft**2'):
    """
    Calculate Area, Circumference, Diameter and Radius of a Circle.
    Enter any one parameter.
    """
    c = Circle(radius=radius, dia=dia, circumference=circumference, area=area)
    return {'Radius': c.radius, 'Dia': c.dia, 'Circumference': c.circumference, 'Area': c.area}


class Circle:
    def __init__(self, **kwargs):
        # print(kwargs)
        if kwargs['radius'] is not None:
            # print(kwargs['radius'])
            qradius = Qty(kwargs['radius'])
            if qradius.val is not None:
                self.r2c(qradius)
                return
        if kwargs['dia'] is not None:
            # print(kwargs['dia'])
            qdia = Qty(kwargs['dia'])
            # print(qdia)
            if qdia.val is not None:
                self.d2c(qdia)
                return
        if kwargs['circumference'] is not None:
            qcircumference = Qty(kwargs['circumference'])
            if qcircumference.val is not None:
                self.p2c(qcircumference)
                return
        if kwargs['area'] is not None:
            qarea = Qty(kwargs['area'])
            if qarea.val is not None:
                self.a2c(qarea)
                return

    def r2c(self, qradius):
        self.attrs(qradius)

    def d2c(self, qdia):
        qradius = qdia / 2
        self.attrs(qradius)

    def p2c(self, qcircumference):
        qradius = qcircumference / (2 * pi)
        self.attrs(qradius)

    def a2c(self, qarea):
        qradius = (qarea / pi) ** 0.5
        self.attrs(qradius)

    def attrs(self, qradius):
        self.radius = qradius
        self.dia = qradius * 2
        self.area = pi * qradius ** 2
        self.circumference = 2 * pi * qradius


from calculators.all.general.utility.cal_range import vrange


def demo_xouts__info():
    return {}


def demo_xouts(x=5, y=10):
    z = x + y
    return {'result': {'x': x, 'y': y, 'result': z}, **vrange()}  # , 'chart': test__chart()
