# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import pandas as pd
import datetime
from .mod_result import result_values
from qcore import Qty, QChart
from qutil import css2strs, variable_to_title, title_to_variable, idx2names


def df_kchart_data_yy(df: pd.DataFrame, x_title='', rkeys=None):
    # df = {x:[],y:[]}
    if rkeys is None:
        rkeys = []
    ch_data = []
    if not rkeys:
        rkeys = df.columns.tolist()

    for rkey in rkeys:
        yvals = df[rkey]
        skip = False
        if isinstance(yvals[0], list):
            yvals = [y[0] for y in yvals]
        elif isinstance(yvals[0], Qty):
            yvals = [y.value for y in yvals]
        elif isinstance(yvals[0], datetime.datetime) or isinstance(yvals[0], str):
            skip = True

        if x_title == rkey:
            skip = True

        if not skip:
            if x_title == '':
                ch_data.append({'name': rkey, 'data': yvals.to_dict()})
            else:
                ch_data.append({'name': rkey, 'data': dict(zip(df[x_title], yvals))})
    return ch_data


def df_qchart_data_yy(df: pd.DataFrame, x_title='', rkeys=None):
    # df = {x:[],y:[]}
    if rkeys is None:
        rkeys = []
    ch_data = {'yvalsm': [], 'ylabelm': [], 'xlabel': x_title}
    if x_title == '':
        ch_data['xvals'] = df.index
    else:
        ch_data['xvals'] = df[x_title]

    if not rkeys:
        rkeys = df.columns.tolist()

    for rkey in rkeys:
        yvals = df[rkey]
        skip = False
        if isinstance(yvals[0], list):
            yvals = [y[0] for y in yvals]
        elif isinstance(yvals[0], Qty):
            yvals = [y.value for y in yvals]
        elif isinstance(yvals[0], datetime.datetime) or isinstance(yvals[0], str):
            skip = True

        if x_title == rkey:
            skip = True

        if not skip:
            ch_data['yvalsm'].append(yvals)
            ch_data['ylabelm'].append(rkey)
    return ch_data


def df_kchart_data_y(df: pd.DataFrame, y=''):
    # df = {x:[]}
    if y == '':
        y = df.columns[0]
    ch_data = [{'name': y, 'data': df[y].to_dict()}]
    return ch_data


def df_qchart_data_y(df: pd.DataFrame, y=''):
    # df = {x:[]}
    if y == '':
        y = df.columns[0]
    ch_data = {'yvals': df[y], 'ylabel': y}
    return ch_data


def fchart(results, xvals=None, result_columns='', result_units: str = '', chart_x_axis: str = '',
           chart_columns: str = '', chart_units: str = '', show='both', aspect=1.0, title=''):
    # create line chart(s) from calculated result and optional xaxis values
    # allowing filtering of table columns based on result column list or units
    # allowing filtering of chartable columns based on chart column list or units
    if isinstance(results[0], dict):
        result_all_columns = list(results[0].keys())
    elif isinstance(results[0], list):
        result_all_columns = ['result']
    else:
        result_all_columns = ['result']

    if xvals is None:
        xvals = []
    if result_columns != '':
        rkeys = idx2names(result_columns, result_all_columns)
    else:
        rkeys = []

    if result_units != '':
        ukeys = css2strs(result_units)
    else:
        ukeys = []

    if chart_columns != '':
        ckeys = idx2names(chart_columns, result_all_columns)
    else:
        ckeys = []

    if chart_units != '':
        cukeys = css2strs(chart_units)
    else:
        cukeys = []

    rkeys = [title_to_variable(rkey.strip()) for rkey in rkeys]
    ukeys = [ukey.strip() for ukey in ukeys]
    ckeys = [title_to_variable(ckey.strip()) for ckey in ckeys]
    cukeys = [cukey.strip() for cukey in cukeys]

    empty_tbl_filter = True
    empty_cht_filter = True
    if len(rkeys) + len(ukeys) + len(ckeys) + len(cukeys) > 0:
        empty_tbl_filter = False
    if len(ckeys) + len(cukeys) > 0:
        empty_cht_filter = False

    for_table_ok = {}
    for_chart_ok = {}
    data_columns = []
    data2c_columns = []
    data_changed_title = []
    data2c_changed_title = []

    rvalues, ruoms = result_values(results[0])  # title to variable
    all_rkeys = list(rvalues.keys())

    data = {}
    data2c = {}
    x_name = title_to_variable(chart_x_axis)
    x_title = variable_to_title(x_name)
    if len(xvals) > 0:  # xvals given
        if chart_x_axis == '':
            x_name = 'x'
            x_title = 'X'
        data[x_name] = xvals
        data2c[x_name] = xvals
        data_changed_title.append(x_title)
        data2c_changed_title.append(x_title)
    else:  # xvals not specified
        if chart_x_axis == '':
            if len(all_rkeys) > 1:
                chart_x_axis = all_rkeys[0]
                x_name = title_to_variable(chart_x_axis)
            # else chart_axis='' is index

    for rkey in all_rkeys:
        if not empty_tbl_filter:
            rkey_ok = rkey in rkeys
            ukey_ok = rkey in ruoms and ruoms[rkey] in ukeys
            ckey_ok = rkey in ckeys
            cukey_ok = rkey in ruoms and ruoms[rkey] in cukeys
            for_table_ok[rkey] = rkey_ok or ukey_ok or ckey_ok or cukey_ok
        else:
            for_table_ok[rkey] = True

        if not empty_cht_filter:
            ckey_ok = rkey in ckeys
            cukey_ok = rkey in ruoms and ruoms[rkey] in cukeys
            for_chart_ok[rkey] = ckey_ok or cukey_ok
        else:
            for_chart_ok[rkey] = True

        if rkey == x_name:
            for_table_ok[rkey] = True
            for_chart_ok[rkey] = True

        if for_table_ok[rkey]:
            data_columns.append(rkey)
            y = variable_to_title(rkey)
            if rkey in ruoms:
                y = y + ' (' + ruoms[rkey] + ')'
            data_changed_title.append(y)

            if for_chart_ok[rkey]:
                data2c_columns.append(rkey)
                data2c_changed_title.append(y)

    for rkey in data_columns:
        data[rkey] = []
    for rkey in data2c_columns:
        data2c[rkey] = []

    for result in results:
        rvalues, ruoms = result_values(result)
        for rkey in data_columns:
            rvalue = rvalues[rkey]
            data[rkey].append(rvalue)
        for rkey in data2c_columns:
            rvalue = rvalues[rkey]
            data2c[rkey].append(rvalue)

    df = pd.DataFrame(data)
    df.columns = data_changed_title
    chart = None
    if show == 'both' or show == 'chart':
        df2c = pd.DataFrame(data2c)
        df2c.columns = data2c_changed_title

        chdata = df_qchart_data_yy(df2c, x_title)
        chart = QChart(aspect=aspect)
        chart.render_lines(**chdata, title=title)

    res = None
    if show == 'both':
        res = {'table': df, 'chart': chart}
    elif show == 'table':
        res = {'table': df}
    elif show == 'chart':
        res = {'chart': chart}
    return res
