# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import numpy as np
import pandas as pd
from qutil import replace_words, css2floats, css2strs, validated_col, css2values
from qcore import qtexta, qchar, qtable, QChart, legend_locations
from calc import QCals
import matplotlib.dates as mdates  # requires for 3D as 3D cant natively handle date axes
from datetime import date, datetime


def surface3d_chart__info():
    return {
        'title': '3D Surface Chart',
        'schema': {
            'x_values': {'type': 'qtexta'},
            'y_values': {'type': 'qtexta'},
            'z_expr': {'type': 'qtexta'},
            'surface_type': {'type': 'radio', 'choices': ['Contour', 'Contourf', 'Wireframe', 'Surface']}
        },
        'outcol': ['chart__r']
    }


def surface3d_chart(
    x_values='-5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5',
    y_values='-5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5',
    z_expr='3*x^2 + 5*y^2',
    x_label='x',
    y_label='y',
    z_label='z',
    title='z vs x,y',
    surface_type='Surface'
):
    # xnums = css2floats(x_values)
    xnums, xtype = css2values(x_values, time2val='hr')
    if xtype in (date, datetime): xnums = mdates.date2num(xnums)
    ynums = css2floats(y_values)

    def zfunc(x, y):
        return QCals.safe_eval(z_expr, ldict={'x': x, 'y': y})

    znums = []
    for x in xnums:
        zs = []
        for y in ynums:
            zs.append(zfunc(x, y))
        znums.append(zs)

    chart = QChart(xtype=xtype)
    chart.render_surface3d(xvals=xnums, yvals=ynums, zvals2d=znums, xlabel=x_label, ylabel=y_label, zlabel=z_label,
                           title=title, surface_type=surface_type)
    return {'chart': chart}


def line3d_chart__info():
    return {
        'title': '3D Line Chart',
        'schema': {
            'x_values': {'type': 'qtexta'},
            'y_values': {'type': 'qtexta'},
            'z_values': {'type': 'qtexta'}
        },
        'outcol': ['chart__r']
    }


def line3d_chart(
    x_values='10, 11, 12, 13, 14, 15, 16, 17, 18, 19',
    y_values='2, 1, 4, 5, 8, 12, 18, 25, 96, 48',
    z_values='2, 1, 4, 5, 8, 12, 18, 25, 96, 48',
    x_label='x',
    y_label='y',
    z_label='z',
    title='z vs x,y'
):
    # xnums = css2floats(x_values)
    xnums, xtype = css2values(x_values, time2val='hr')
    if xtype in (date, datetime): xnums = mdates.date2num(xnums)
    ynums = css2floats(y_values)
    znums = css2floats(z_values)
    chart = QChart(xtype=xtype)
    chart.render_line3d(xvals=xnums, yvals=ynums, zvals=znums, xlabel=x_label, ylabel=y_label, zlabel=z_label,
                        title=title)
    return {'chart': chart}


def line_chart__info():
    return {
        'title': 'Simple Line Chart',
        'schema': {
            'x_values': {'type': 'qtexta'},
            'y_values': {'type': 'qtexta'}
        },
        'outcol': ['chart__r']
    }


def line_chart(
    x_values='10, 11, 12, 13, 14, 15, 16, 17, 18, 19',
    y_values='2, 1, 4, 5, 8, 12, 18, 25, 96, 48',
    x_label='x',
    y_label='y',
    title='y vs x'
):
    # xnums = css2floats(x_values)
    xnums, xtype = css2values(x_values, time2val='hr')
    ynums = css2floats(y_values)
    chart = QChart(xtype=xtype)
    chart.render_lines(xvals=xnums, yvalsm=[ynums], xlabel=x_label, ylabel=y_label, title=title)
    return {'chart': chart}


def line2_chart__info():
    return {
        'title': 'Simple Double Line Chart',
        'outcol': ['chart__r']
    }


def line2_chart(
    x_values: qtexta = '10, 11, 12, 13, 14, 15, 16, 17, 18, 19',
    y_values: qtexta = '2, 1, 4, 5, 8, 12, 18, 25, 96, 48',
    y_values2: qtexta = '12, 10, 4, -5, 3, 9, 23, 12, 12, 5',
    x_label='x',
    y_labels='y1, y2',
    y_label='y',
    title='y vs x'
):
    # xnums = css2floats(x_values)
    xnums, xtype = css2values(x_values, time2val='hr')
    ynums = css2floats(y_values)
    ynums2 = css2floats(y_values2)
    chart = QChart(xtype=xtype)
    chart.render_lines(xvals=xnums, yvalsm=[ynums, ynums2], xlabel=x_label, ylabels=css2strs(y_labels), ylabel=y_label,
                       title=title)
    return {'chart': chart}


def scatter_chart__info():
    return {
        'title': 'Simple Scatter Chart',
        'outcol': ['chart__r']
    }


def scatter_chart(
    x_values: qtexta = '5,7,8,7,2,17,2,9,4,11,12,9,6',
    y_values: qtexta = '99,86,87,88,111,86,103,87,94,78,77,85,86',
    names: qtexta = '',
    x_label='x',
    y_label='y',
    title='y vs x'
):
    # xnums = css2floats(x_values)
    xnums, xtype = css2values(x_values, time2val='hr')
    ynums = css2floats(y_values)
    items = css2strs(names)
    chart = QChart(xtype=xtype)
    chart.render_scatter(xvals=xnums, yvals=ynums, names=items, xlabel=x_label, ylabel=y_label, title=title)
    return {'chart': chart}


def bar_chart__info():
    return {
        'title': 'Simple Bar Chart',
        'schema': {
            'names': {'type': 'textarea'},
            'values': {'type': 'textarea'}
        },
        'outcol': ['chart__r']
    }


def bar_chart(
    names='Jan, Feb, Mar, Apr, May, Jun, Jul, Aug, Sep, Oct, Nov, Dec',
    values='12, 14, 16, 21, 24, 30, 35, 28, 24, 21, 18, 13',
    label='Temperature',
    title='Month wise Temperature',
    vertical=True
):
    names = css2strs(names)
    nums = css2floats(values)
    chart = QChart(xtype=str)
    chart.render_bar(labels=names, vals=nums, label=label, title=title, vertical=vertical)
    return {'chart': chart}


def pie_chart__info():
    return {
        'title': 'Simple Pie Chart',
        'schema': {
            'radius': {'attrs': {'max': '2.0', 'min': '0.2'}},
            'legend': {'type': 'choice', 'choices': legend_locations},
            'labels_include': {'type': 'checkboxselectmultiple', 'choices': ['label', 'value']}
        },
        'outcol': ['chart__r']
    }


def pie_chart(
    labels: qtexta = 'Jan, Feb, Mar, Apr, May, Jun, Jul, Aug, Sep, Oct, Nov, Dec',
    values: qtexta = '12, 14, 16, 21, 24, 30, 35, 28, 24, 21, 18, 13',
    title='Month wise Temperature',
    show_pct=False,
    shadow=False,
    radius=1.0,
    show_labels=True,
    legend='none',
    labels_include=['label']
):
    chart = QChart()
    chart.save_data(locals(), 'pie_chart')
    names = css2strs(labels)
    sizes = css2floats(values)
    chart.render_pie(names, sizes, title=title, show_pct=show_pct, shadow=shadow, radius=radius,
                     show_labels=show_labels, legend=legend, labels_include=labels_include)
    return {'chart': chart}


def pie2_chart__info():
    return {
        'title': 'Simple Pie Chart based on Tabular Data',
        'outcol': ['chart__r']
    }


def pie2_chart(
    data: qtable = pd.DataFrame(
        {"label": ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
         "value": ['12', '14', '16', '21', '24', '30', '35', '28', '24', '21', '18', '13']}),
    title='Month wise Temperature',
    show_pct=False,
    shadow=False,
    label_column: qchar = 'label',
    value_column: qchar = 'value'
):
    cols = data.columns
    lbl = validated_col(cols, 0, label_column)
    val = validated_col(cols, 1, value_column)

    names = data[lbl].to_list()
    sizes = data[val].to_list()
    chart = QChart()
    chart.render_pie(names, sizes, title=title, show_pct=show_pct, shadow=shadow, legend=None)
    return {'chart': chart}


def pareto_chart__info():
    return {
        'title': 'Simple Pareto Chart',
        'outcol': ['chart__r']
    }


def pareto_chart(
    labels: qtexta = 'Jan, Feb, Mar, Apr, May, Jun, Jul, Aug, Sep, Oct, Nov, Dec',
    values: qtexta = '12, 14, 16, 21, 24, 30, 35, 28, 24, 21, 18, 13',
    title='Month wise Temperature',
    value_label='Count',
):
    x = css2strs(labels)
    y = css2floats(values)
    chart = QChart(xtype=str)
    chart.render_pareto(x, y, ylabel=value_label, title=title)
    return {'chart': chart}


def histogram__info():
    return {
        'title': 'Simple Histogram',
        'schema': {
            'values': {'type': 'textarea'}
        },
        'outcol': ['chart__r']
    }


def histogram(
    values='89, 106, 122, 102,  98, 122,  97, 110,  93,  75, 133, 118,  104, 117,  103, 91,  91, 117, 108, 129',
    bin_count=8,
    density=True,
    x_label='Values',
    y_label='Frequency',
    title='Simple Histogram'
):
    nums = css2floats(values)
    chart = QChart()
    chart.render_histogram(nums, bin_count, density=density, xlabel=x_label, ylabel=y_label, title=title)
    return {'chart': chart}


def pareq__info():
    ret = {
        'title': 'Parametric Equation',
        # 'outcol': ['chart__r'],
        # 'template': 'v4.21',
        'col': ['x-title', 'const_1-aspect'],
        # 'row': ['10-11', '12-13','14-15','16-17','18-19']
    }
    return ret


def pareq(
    x: qtexta = 'cos(theta)',
    y: qtexta = 'sin(theta)',
    variable: qchar = 'theta', variable_start=0, variable_stop=6.28, variations=100,
    x_label='x', y_label='y', title='Parametric Equation',
    const_1: qchar = '', const_1_part='',
    const_2: qchar = '', const_2_part='',
    const_3: qchar = '', const_3_part='',
    aspect=0
):
    v = np.linspace(variable_start, variable_stop, variations)

    if const_1_part != '':
        x = replace_words(x, [const_1], f'({const_1_part})')
        y = replace_words(y, [const_1], f'({const_1_part})')
    if const_2_part != '':
        x = replace_words(x, [const_2], f'({const_2_part})')
        y = replace_words(y, [const_2], f'({const_2_part})')
    if const_3_part != '':
        x = replace_words(x, [const_3], f'({const_3_part})')
        y = replace_words(y, [const_3], f'({const_3_part})')

    xv = [QCals.safe_eval(replace_words(x, [variable], f'({val})')) for val in v]
    yv = [QCals.safe_eval(replace_words(y, [variable], f'({val})')) for val in v]
    if aspect != '':
        asp = float(aspect)
    else:
        asp = 0

    chart = QChart(aspect=asp)
    chart.render_lines(xv, [yv], x_label, [y_label], title)
    return chart


def fx2__info():
    return {
        'title': 'Plot Multiple Equations',
        'newcol': ['y', 'const_1'],
        'endcol': ['title', 'aspect'],
        'outcol': ['chart__r']
    }


def fx2(
    y_expressions: qtexta = 'sin(theta)\ncos(theta)',
    variable: qchar = 'theta', variable_start=0, variable_stop=6.28, variations=100,
    x_label='x', y_labels='', title='Plot Multiple Equations',
    const_1: qchar = '', const_1_part: qchar = '',
    const_2: qchar = '', const_2_part: qchar = '',
    const_3: qchar = '', const_3_part: qchar = '',
    aspect=0.0
):
    xvals = np.linspace(variable_start, variable_stop, variations)

    if const_1_part != '':
        y_expressions = replace_words(y_expressions, [const_1], f'({const_1_part})')
    if const_2_part != '':
        y_expressions = replace_words(y_expressions, [const_2], f'({const_2_part})')
    if const_3_part != '':
        y_expressions = replace_words(y_expressions, [const_3], f'({const_3_part})')

    y_xpr_list = [line.strip() for line in y_expressions.split('\n')]
    ylabels = css2strs(y_labels) if y_labels else y_xpr_list
    yvalsm = [[QCals.safe_eval(replace_words(expr, [variable], f'({val})')) for val in xvals]
              for expr in y_xpr_list]

    if aspect != '':
        asp = float(aspect)
    else:
        asp = 0

    chart = QChart(aspect=asp)
    chart.render_lines(xvals=xvals, yvalsm=yvalsm, xlabel=x_label, ylabels=ylabels, title=title)
    return {'chart': chart}


def mesh__info():
    return {
        'title': 'Simple Network Diagram or 2D Mesh',
        'outcol': ['chart__r']
    }


def mesh(
    nodes: qtable = pd.DataFrame(
        data={"Point": ["A", "B", "C", "D"], "X": [0, 1, 1, -0.50], "Y": [0, 0, 1, 0.80]}),
    edges: qtable = pd.DataFrame(
        data={"Edge": ["1", "2", "3", "4", "5"], "N1": ["A", "B", "C", "D", "A"],
              "N2": ["B", "C", "D", "A", "C"]}),
    title='Network Diagram',
    edge_label=True
):
    chart = QChart()
    chart.render_network(
        nodes,
        edges,
        title=title,
        edge_label=edge_label
    )
    return {'chart': chart}


def quadrant_chart__info():
    return {
        'title': 'Quadrant Chart'
    }


def quadrant_chart(
    category_x: qtable = pd.DataFrame(
        {'Name': ['Low', 'Medium', 'High', 'Very High'], 'Weight': [10, 20, 30, 40]}),
    category_y: qtable = pd.DataFrame(
        {'Name': ['Low', 'Medium', 'High', 'Very High'], 'Weight': [10, 20, 30, 40]}),
    data: qtable = pd.DataFrame(
        {'Item': ['A', 'B', 'C', 'D'], 'X': ['Low', 'High', 'Medium', 'Low'],
         'Y': ['Medium', 'High', 'Very High', 'Low']}),
    item_column: qchar = '',
    x_column: qchar = '',
    y_column: qchar = '',
    title='Quardant Chart'
):
    cols = data.columns
    item = validated_col(cols, 0, item_column)
    x = validated_col(cols, 1, x_column)
    y = validated_col(cols, 2, y_column)

    cols_x = category_x.columns
    name_x = cols_x[0]
    weight_x = cols_x[1]
    category_x_dict = dict(map(lambda i, j: (i, j), category_x[name_x], category_x[weight_x]))

    cols_y = category_y.columns
    name_y = cols_y[0]
    weight_y = cols_y[1]
    category_y_dict = dict(map(lambda i, j: (i, j), category_y[name_y], category_y[weight_y]))

    items = data[item]
    points_x = []
    for vx in data[x]:
        points_x.append(int(category_x_dict[vx]))
    x_offset = sum(points_x) / len(points_x)
    points_x = [vx - x_offset for vx in points_x]

    points_y = []
    for vy in data[y]:
        points_y.append(int(category_y_dict[vy]))
    y_offset = sum(points_y) / len(points_y)
    points_y = [vy - y_offset for vy in points_y]

    chart = QChart()
    chart.render_scatter(points_x, points_y, items, x_column, y_column, title)
    return {'chart': chart}
