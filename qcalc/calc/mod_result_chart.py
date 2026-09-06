# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import pandas as pd
import datetime
from .mod_result import result_values
from qcore import Qty, QChart
from qutil import css2strs, variable_to_title, title_to_variable, idx2names


def df2chart(df: pd.DataFrame, x_column='', y_columns: list | None = None,
             ylabel='y', chart_title='y vs x', chart_type='lines'):
    """Draw lines or stack chart from DataFrame or qdf columns.

    The X values come from the DataFrame index when ``x_column`` is empty;
    otherwise they come from the named column. Each remaining numeric-like
    column becomes a Y series. String and datetime columns are skipped, while
    one-item lists and ``Qty`` values are converted to scalar numeric values.

    Args:
        df: DataFrame or qdf containing the X and Y data.
        x_column: Display name of the column to use for X values, or an empty
            string to use the DataFrame index.
        y_columns: Optional list of columns to inspect. All DataFrame columns are
            inspected when omitted or empty.
        chart_type: can be 'lines', 'bars', 'hbars' or 'stack'.

    Returns:
        A QChart
    """
    chart_data = df2chart_data(df, x_column, y_columns)
    chart = QChart()
    if chart_type == 'lines':
        chart.render_lines(**chart_data, ylabel=ylabel, title=chart_title)
    elif chart_type == 'bars':
        chart.render_bars(**chart_data, ylabel=ylabel, title=chart_title, vertical=True)
    elif chart_type == 'hbars':
        chart.render_bars(**chart_data, ylabel=ylabel, title=chart_title, vertical=False)
    else:  # chart_type == 'stack'
        chart.render_stack(**chart_data, ylabel=ylabel, title=chart_title)
    return chart


def df2histo(df: pd.DataFrame, bin_count=20, xlabel='x', y_column=None,
             ylabel='Frequency', chart_title='Histogram'):
    if y_column is None:
        return None
    chart = QChart()
    yvals = df2histo_data(df, y_column)
    chart.render_histogram(values=yvals, bin_count=bin_count, xlabel=xlabel, ylabel=ylabel, title=chart_title)
    return chart


def df2chart_data(df, x_column='', y_columns: list | None = None):
    # df = {x:[],y:[]}
    if y_columns is None:
        y_columns = []
    ch_data = {'yvalsm': [], 'ylabels': [], 'xlabel': x_column}
    if x_column == '':
        ch_data['xvals'] = list(df.index)
    else:
        ch_data['xvals'] = df[x_column]

    if not y_columns:
        y_columns = list(df.columns)

    for rkey in y_columns:
        yvals = df[rkey]
        skip = False
        if isinstance(yvals[0], list):
            yvals = [y[0] for y in yvals]
        elif isinstance(yvals[0], Qty):
            yvals = [y.value for y in yvals]
        elif isinstance(yvals[0], datetime.datetime) or isinstance(yvals[0], str):
            skip = True

        if x_column == rkey:
            skip = True

        if not skip:
            ch_data['yvalsm'].append(yvals)
            ch_data['ylabels'].append(rkey)
    return ch_data


def df2histo_data(df, y_column: str):
    # rows can be heterogeneous (e.g. a failed trial contributes None/{} instead
    # of a number), so filter per-value rather than assuming a uniform column type
    cleaned = []
    for v in df[y_column]:
        if isinstance(v, list):
            v = v[0] if v else None
        if isinstance(v, Qty):
            v = v.val
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            cleaned.append(float(v))
    return cleaned


def results2chart(
    results, xvals=None, result_columns='', result_units: str = '',
    chart_x_axis: str = '', chart_columns: str = '', chart_units: str = '', show='both',
    title='', chart_type='lines'):
    """Build a result table and/or chart (lines or stack) from calculated LIST or array of results
    from repeated run of the same calculator/function.

    Results may be scalars, lists, dictionaries, or quantity values. Result
    values are normalized with ``result_values``; quantity columns retain
    their units in the displayed labels. Column filters accept comma-separated
    display names or one-based column indexes.

    ``result_columns`` and ``result_units`` control columns shown in the
    table. ``chart_x_axis`` selects an existing result column for the X axis,
    while ``xvals`` supplies explicit X values. ``chart_columns`` and
    ``chart_units`` control the plotted Y series. When no chart filters are
    supplied, all chart-compatible result columns are plotted.

    Args:
        results: Non-empty sequence of calculated result values.
        xvals: Optional explicit X-axis values. If supplied without
            ``chart_x_axis``, they are added as a column named ``X``.
        result_columns: Comma-separated result column names or one-based
            indexes to include in the table.
        result_units: Comma-separated units whose columns should be included
            in the table.
        chart_x_axis: Result column name used for the X axis when ``xvals`` is
            not supplied.
        chart_columns: Comma-separated result column names or one-based
            indexes to plot.
        chart_units: Comma-separated units whose columns should be plotted.
        show: ``'table'``, ``'chart'``, or ``'both'``.
        aspect: Chart height-to-width ratio passed to ``QChart``.
        title: Chart title.

    Returns:
        A dictionary containing a pandas ``DataFrame`` under ``'table'``, a
        ``QChart`` under ``'chart'``, or both, according to ``show``. An
        unsupported ``show`` value returns ``None``.
    """
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
        y_columns = idx2names(result_columns, result_all_columns)
    else:
        y_columns = []

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

    y_columns = [title_to_variable(rkey.strip()) for rkey in y_columns]
    ukeys = [ukey.strip().lower() for ukey in ukeys]
    ckeys = [title_to_variable(ckey.strip()) for ckey in ckeys]
    cukeys = [cukey.strip().lower() for cukey in cukeys]

    empty_tbl_filter = True
    empty_cht_filter = True
    if len(y_columns) + len(ukeys) > 0:
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
    all_y_columns = list(rvalues.keys())

    data = {}
    data2c = {}
    x_name = title_to_variable(chart_x_axis)
    x_column = variable_to_title(x_name)
    if len(xvals) > 0:  # xvals given
        if chart_x_axis == '':
            x_name = 'x'
            x_column = 'X'
        data[x_name] = xvals
        data2c[x_name] = xvals
        data_changed_title.append(x_column)
        data2c_changed_title.append(x_column)
    else:  # xvals not specified
        if chart_x_axis == '':
            if len(all_y_columns) > 1:
                chart_x_axis = all_y_columns[0]
                x_name = title_to_variable(chart_x_axis)
            # else chart_axis='' is index

    for rkey in all_y_columns:
        if not empty_tbl_filter:
            rkey_ok = rkey in y_columns
            ukey_ok = rkey in ruoms and ruoms[rkey].lower() in ukeys
            ckey_ok = rkey in ckeys
            cukey_ok = rkey in ruoms and ruoms[rkey].lower() in cukeys
            for_table_ok[rkey] = rkey_ok or ukey_ok or ckey_ok or cukey_ok
        else:
            for_table_ok[rkey] = True

        if not empty_cht_filter:
            ckey_ok = rkey in ckeys
            cukey_ok = rkey in ruoms and ruoms[rkey].lower() in cukeys
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

    build_table = show in ('both', 'table')
    build_chart = show in ('both', 'chart')

    for result in results:
        rvalues, ruoms = result_values(result)
        if build_table:
            for rkey in data_columns:
                data[rkey].append(rvalues.get(rkey))
        if build_chart:
            for rkey in data2c_columns:
                data2c[rkey].append(rvalues.get(rkey))

    df = None
    if build_table:
        df = pd.DataFrame(data)
        df.columns = data_changed_title

    chart = None
    if build_chart:
        df2c = pd.DataFrame(data2c)
        df2c.columns = data2c_changed_title
        chart = df2chart(df2c, x_column, y_columns=None, chart_title=title, chart_type=chart_type)

    res = None
    if show == 'both':
        res = {'table': df, 'chart': chart}
    elif show == 'table':
        res = {'table': df}
    elif show == 'chart':
        res = {'chart': chart}
    return res


def results2histo(
    results, bin_count=20, result_columns='', result_units: str = '',
    chart_column: str = '', show='both', title=''):
    if isinstance(results[0], dict):
        result_all_columns = list(results[0].keys())
    elif isinstance(results[0], list):
        result_all_columns = ['result']
    else:
        result_all_columns = ['result']

    if result_columns != '':
        y_columns = idx2names(result_columns, result_all_columns)
    else:
        y_columns = []

    if result_units != '':
        ukeys = css2strs(result_units)
    else:
        ukeys = []

    if chart_column != '':
        ckeys = idx2names(chart_column, result_all_columns)
    else:
        ckeys = []

    y_columns = [title_to_variable(rkey.strip()) for rkey in y_columns]
    ukeys = [ukey.strip().lower() for ukey in ukeys]
    ckeys = [title_to_variable(ckey.strip()) for ckey in ckeys]

    empty_tbl_filter = True
    empty_cht_filter = True
    if len(y_columns) + len(ukeys) > 0:
        empty_tbl_filter = False
    if len(ckeys) > 0:
        empty_cht_filter = False

    for_table_ok = {}
    for_chart_ok = {}
    data_columns = []
    data2c_columns = []
    data_changed_title = []
    data2c_changed_title = []

    rvalues, ruoms = result_values(results[0])  # title to variable
    all_y_columns = list(rvalues.keys())

    data = {}
    data2c = {}

    for rkey in all_y_columns:
        if not empty_tbl_filter:
            rkey_ok = rkey in y_columns
            ukey_ok = rkey in ruoms and ruoms[rkey].lower() in ukeys
            ckey_ok = rkey in ckeys
            for_table_ok[rkey] = rkey_ok or ukey_ok or ckey_ok
        else:
            for_table_ok[rkey] = True

        if not empty_cht_filter:
            ckey_ok = rkey in ckeys
            for_chart_ok[rkey] = ckey_ok
        else:
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

    build_table = show in ('both', 'table')
    build_chart = show in ('both', 'chart')

    for result in results:
        rvalues, ruoms = result_values(result)
        if build_table:
            for rkey in data_columns:
                data[rkey].append(rvalues.get(rkey))
        for rkey in data2c_columns:
            data2c[rkey].append(rvalues.get(rkey))

    df = None
    if build_table:
        df = pd.DataFrame(data)
        df.columns = data_changed_title

    df2c = pd.DataFrame(data2c)
    df2c.columns = data2c_changed_title
    if len(data2c_changed_title) > 1:
        raise Exception(
            f"Multiple chartable columns {data2c_changed_title} found; "
            "specify chart_column to pick one for the histogram")
    y_column = data2c_changed_title[0] if data2c_changed_title else None
    # values (for stats) are cheap to derive and always computed; the chart
    # (matplotlib render) is the expensive part, only built when requested
    values = df2histo_data(df2c, y_column) if y_column is not None else []
    chart = df2histo(df2c, bin_count, xlabel='', y_column=y_column, chart_title=title) if build_chart else None

    res = None
    if show == 'both':
        res = {'table': df, 'chart': chart, 'values': values}
    elif show == 'table':
        res = {'table': df, 'values': values}
    elif show == 'chart':
        res = {'chart': chart, 'values': values}
    return res
