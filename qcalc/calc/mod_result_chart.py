# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import pandas as pd
import datetime

from .mod_result import result_values
from qcore import Qty, QChart
from qutil import css2strs, variable_to_title, title_to_variable, specified_args


class QResults:
    """Build result tables and charts from calculated results.

    An instance wraps a non-empty sequence of calculated result values
    (scalars, lists, dictionaries, or quantity values) from repeated
    run(s) of the same calculator/function, along with the table/chart
    filters shared by ``to_chart`` and ``to_histo``.

    Args:
        results: Non-empty sequence of calculated result values.
        xvals: Optional explicit X-axis values. If supplied without
            ``chart_x_axis`` (in ``to_chart``), they are added as a column
            named ``X``.
        table_columns: Comma-separated result column names or one-based
            indexes to include in the table.
        table_units: Comma-separated units whose columns should be included
            in the table.
        show: ``'table'``, ``'chart'``, or ``'both'``.
        title: Chart title.
    """

    def __init__(self, results, xvals=None, variable='',
                 table_columns: str = '', table_units: str = '',
                 show='both'):

        self.results = results
        self.xvals = xvals if xvals is not None else []
        self.variable = variable

        self.table_columns = table_columns
        self.table_units = table_units

        self.chart_columns = ''
        self.chart_units = ''
        self.ylabel = 'y'
        self.chart_title = ''
        self.chart_type = 'lines'

        self.histo_column = ''
        self.bin_count = 20

        self.show = show
        # header/shape info derived from the first result, reused by to_chart/to_histo
        self._all_columns = self._compute_all_columns()
        self._header_values, self._header_uoms = result_values(results[0])
        self._all_y_columns = list(self._header_values.keys())

        self.table_df = None
        self.chart = None
        self.values = []
        self._processed = False

    def setup_chart(self,
                    chart_columns: str = '', chart_units: str = '',
                    ylabel='y', chart_title: str = '', chart_type='lines'
                    ):
        self.chart_columns = chart_columns  # comma separated
        self.chart_units = chart_units
        self.ylabel = ylabel
        self.chart_title = chart_title
        self.chart_type = chart_type

    def setup_histo(self,
                    histo_column: str = '', bin_count: int = 20,
                    ylabel='Frequency', chart_title: str = 'Histogram'
                    ):
        self.histo_column = histo_column
        self.bin_count = bin_count
        self.ylabel = ylabel
        self.histo_column = histo_column
        self.chart_columns = histo_column  # single str, not comma separated
        self.bin_count = bin_count
        self.ylabel = ylabel
        self.chart_title = chart_title
        self.chart_type = 'histo'

    def _compute_all_columns(self):
        """Raw column names for one-based/name filter resolution (idx2names)."""
        results = self.results
        if isinstance(results[0], dict):
            cols = list(results[0].keys())
            # the swept variable occupies the first slot for one-based index filters
            var_columns = css2strs(self.variable)
            return (var_columns + cols) if var_columns else cols
        elif isinstance(results[0], list):
            return [f"Result {i}" for i, _ in enumerate(results, 1)]
        else:
            return ['Result']

    def _fill_columns(self, columns):
        """Extract each result's normalized value for the given columns, one row per result."""
        data = {rkey: [] for rkey in columns}
        for result in self.results:
            rvalues, _ = result_values(result)
            for rkey in columns:
                data[rkey].append(rvalues.get(rkey))
        return data

    @staticmethod
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
        chart_data = QResults.df2chart_data(df, x_column, y_columns)
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

    @staticmethod
    def df2histo(df: pd.DataFrame, bin_count=20, xlabel='Value', y_column=None,
                 ylabel='Frequency', chart_title='Histogram', density=True):
        if y_column is None:
            return None
        chart = QChart()
        yvals = QResults.df2histo_data(df, y_column)
        chart.render_histogram(values=yvals, bin_count=bin_count, density=density,
                       xlabel=xlabel, ylabel=ylabel, title=chart_title)
        return chart

    @staticmethod
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

    @staticmethod
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
                v = float(v)
                # statistics.stdev/fmean raise "'float' object has no attribute
                # 'numerator'" when the data contains NaN, so drop it here
                if v == v:
                    cleaned.append(v)
        return cleaned

    def _table_column_filters(self):
        """Parse ``self.table_columns``/``self.table_units`` into variable-name keys."""
        table_columns = self.table_columns
        table_units = self.table_units
        # y_columns = idx2names(table_columns, self._all_columns) if table_columns != '' else []
        y_columns = specified_args(self._all_columns, table_columns) if table_columns != '' else []
        ukeys = css2strs(table_units) if table_units != '' else []

        y_columns = [title_to_variable(rkey.strip()) for rkey in y_columns]
        ukeys = [ukey.strip().lower() for ukey in ukeys]
        return y_columns, ukeys

    def _chart_column_filter(self):
        """Parse comma-separated chart column/unit filters into variable-name keys.

        ``chart_units`` is unused by histograms, which only ever chart one column.
        """
        # ckeys = idx2names(self.chart_columns, self._all_columns) if self.chart_columns != '' else []
        ckeys = specified_args(self._all_columns, self.chart_columns) if self.chart_columns != '' else []
        cukeys = css2strs(self.chart_units) if self.chart_units != '' else []

        ckeys = [title_to_variable(ckey.strip()) for ckey in ckeys]
        cukeys = [cukey.strip().lower() for cukey in cukeys]
        return ckeys, cukeys

    def _classify_columns(self, y_columns, ukeys, ckeys, cukeys, x_name=None):
        """Split ``self._all_y_columns`` into table/chart column lists and their display titles.

        A column is kept for the table when it matches a table/chart column or
        unit filter (or no table/chart filter was given), and additionally kept
        for the chart when it matches a chart column or unit filter (or no
        chart filter was given). ``x_name``, when given, is always kept in both.
        """
        all_y_columns = self._all_y_columns
        ruoms = self._header_uoms
        empty_tbl_filter = not (y_columns or ukeys)
        empty_cht_filter = not (ckeys or cukeys)

        data_columns = []
        data2c_columns = []
        data_changed_titles = []
        data2c_changed_titles = []

        for rkey in all_y_columns:
            if not empty_tbl_filter:
                rkey_ok = rkey in y_columns
                ukey_ok = rkey in ruoms and ruoms[rkey].lower() in ukeys
                ckey_ok = rkey in ckeys
                cukey_ok = rkey in ruoms and ruoms[rkey].lower() in cukeys
                table_ok = rkey_ok or ukey_ok or ckey_ok or cukey_ok
            else:
                table_ok = True

            if not empty_cht_filter:
                ckey_ok = rkey in ckeys
                cukey_ok = rkey in ruoms and ruoms[rkey].lower() in cukeys
                chart_ok = ckey_ok or cukey_ok
            else:
                chart_ok = True

            if rkey == x_name:
                table_ok = True
                chart_ok = True

            if table_ok:
                data_columns.append(rkey)
                y = variable_to_title(rkey)
                if rkey in ruoms:
                    y = y + ' (' + ruoms[rkey] + ')'
                data_changed_titles.append(y)

                if chart_ok:
                    data2c_columns.append(rkey)
                    data2c_changed_titles.append(y)

        return data_columns, data2c_columns, data_changed_titles, data2c_changed_titles

    def process(self):
        """Build a result table and/or chart from ``self.results`` (memoized).

        Results may be scalars, lists, dictionaries, or quantity values. Result
        values are normalized with ``result_values``; quantity columns retain
        their units in the displayed labels. Column filters accept comma-separated
        display names or one-based column indexes.

        ``self.table_columns``/``self.table_units`` control columns shown in the
        table. ``self.variable`` (if set) selects the result column used for the
        X axis, while ``self.xvals`` supplies explicit X values. The chart/histogram
        settings configured via ``setup_chart``/``setup_histo`` control the plotted
        Y series. When no chart filters are supplied, all chart-compatible result
        columns are plotted (or, for a histogram, must resolve to exactly one).

        Returns:
            A ``(table_df, chart)`` tuple, either of which may be ``None``
            depending on ``self.show``.
        """
        # create chart(s) from calculated result and optional xaxis values
        # allowing filtering of table columns based on result column list or units
        # allowing filtering of chartable columns based on chart column list or units
        if self._processed:
            return self.table_df, self.chart
        chart_x_axis = self.variable
        xvals = self.xvals

        if xvals is None:
            xvals = []
        y_columns, ukeys = self._table_column_filters()
        ckeys, cukeys = self._chart_column_filter()
        all_y_columns = self._all_y_columns

        x_name = title_to_variable(chart_x_axis)
        x_column = variable_to_title(x_name)
        prefill = {}
        if len(xvals) > 0:  # xvals given
            if chart_x_axis == '':
                x_name = 'x'
                x_column = 'X'
            prefill[x_name] = xvals
        else:  # xvals not specified
            if chart_x_axis == '':
                if len(all_y_columns) > 1:
                    chart_x_axis = all_y_columns[0]
                    x_name = title_to_variable(chart_x_axis)
                # else chart_axis='' is index

        table_columns, chart_columns, table_changed_titles, chart_changed_titles = self._classify_columns(
            y_columns, ukeys, ckeys, cukeys, x_name=x_name)
        has_y_series = bool(chart_changed_titles)  # before the x column is prepended below
        if prefill:
            table_changed_titles = [x_column] + table_changed_titles
            # a histogram only ever plots the swept variable's own result column(s),
            # never the x-axis/xvals column used by line/bar/stack charts
            if self.chart_type != 'histo':
                chart_changed_titles = [x_column] + chart_changed_titles

        table_data = dict(prefill)
        table_data.update(self._fill_columns(table_columns))
        self.table_df = pd.DataFrame(table_data)
        self.table_df.columns = table_changed_titles

        build_chart = self.show in ('both', 'chart')
        if has_y_series:
            chart_df = self.table_df[chart_changed_titles]
            if self.chart_type == 'histo':
                if len(chart_columns) > 1:
                    raise Exception(
                        f"Multiple chartable columns {chart_changed_titles} found; "
                        "specify histo_column to pick one for the histogram")
                y_column = chart_changed_titles[0]
                # values (for stats) are cheap to derive and always computed; the chart
                # (matplotlib render) is the expensive part, only built when requested
                self.values = QResults.df2histo_data(chart_df, y_column)
                if build_chart:
                    self.chart = QResults.df2histo(
                        chart_df, self.bin_count, xlabel=y_column, y_column=y_column,
                        ylabel=self.ylabel, chart_title=self.chart_title, density=False)
            elif build_chart:
                self.chart = QResults.df2chart(
                    chart_df, x_column, y_columns=None,
                    ylabel=self.ylabel, chart_title=self.chart_title, chart_type=self.chart_type)

        self._processed = True
        return self.table_df, self.chart

    def objects(self):
        if not self._processed:
            self.process()
        show = self.show
        res = {}
        if show == 'both' or show == 'table':
            res['table'] = self.table_df
        if show == 'both' or show == 'chart':
            res['chart'] = self.chart
        if self.chart_type == 'histo':
            res['values'] = self.values
        return res
