# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import re

import pandas as pd

from qcore import Qty
from qutil import css2strs, specified_args
from .mod_result_chart import QResults


def _split_title_unit(title: str):
    match = re.match(r'^(.*)\s*\(([^()]+)\)\s*$', str(title).strip())
    if match:
        return match.group(1).strip(), match.group(2).strip()
    return str(title).strip(), ''


def _to_df(table):
    if isinstance(table, pd.DataFrame):
        return table.copy()

    if not isinstance(table, dict):
        raise Exception('Scenario table must be a table dictionary or DataFrame')

    columns = table.get('columns', [])
    data = table.get('data', [])
    if not columns or not isinstance(columns, list):
        raise Exception("Scenario table must include a 'columns' list")
    if not isinstance(data, list):
        raise Exception("Scenario table must include a 'data' list")
    return pd.DataFrame(data, columns=columns)


def _as_float(value):
    if isinstance(value, Qty):
        return float(value.val)
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if value in ('', None):
        return None
    if isinstance(value, str):
        text = value.strip()
        if text == '':
            return None
        try:
            return float(text)
        except Exception:
            return None
    return None


def _select_metric_columns(df, metric_columns: str, metric_units: str,
                           id_columns: list[str], variable_columns: list[str]):
    base_columns = [
        column for column in df.columns
        if column not in id_columns and column not in variable_columns
    ]

    by_name = specified_args(base_columns, metric_columns) if metric_columns else []
    unit_keys = [unit.strip().lower() for unit in css2strs(metric_units)] if metric_units else []
    by_unit = []
    if unit_keys:
        for column in base_columns:
            _, unit = _split_title_unit(column)
            if unit and unit.lower() in unit_keys:
                by_unit.append(column)

    selected = []
    seen = set()
    for column in base_columns:
        if (not metric_columns and not metric_units) or column in by_name or column in by_unit:
            if column not in seen:
                selected.append(column)
                seen.add(column)
    if not selected:
        raise Exception('No metric columns selected; check metric column/unit filters')
    return selected


def _delta_column_name(column, delta_type):
    title, unit = _split_title_unit(column)
    if delta_type == 'absolute':
        return f'{title} Delta ({unit})' if unit else f'{title} Delta'
    if delta_type == 'percent':
        return f'{title} Delta (%)'
    return f'{title} Index'


def _delta_values(values: list, base_value, delta_type):
    output = []
    for value in values:
        number = _as_float(value)
        if number is None or base_value is None:
            output.append(None)
            continue
        if delta_type == 'absolute':
            output.append(number - base_value)
        elif delta_type == 'percent':
            if abs(base_value) <= 1e-12:
                output.append(None)
            else:
                output.append((number - base_value) * 100.0 / base_value)
        elif delta_type == 'index':
            if abs(base_value) <= 1e-12:
                output.append(None)
            else:
                output.append(number / base_value)
        else:
            raise Exception("delta_type must be one of: absolute, percent, index")
    return output


def _resolve_metric(metric_columns: list[str], metric_name: str, field_name='metric'):
    if not metric_name:
        return metric_columns[0] if metric_columns else ''
    selector = str(metric_name).strip()
    selector_low = selector.lower()

    for metric in metric_columns:
        title, _ = _split_title_unit(metric)
        if selector_low == str(metric).strip().lower() or selector_low == title.lower():
            return metric

    names = specified_args(metric_columns, metric_name)
    has_pattern = any(char in selector for char in ('*', '-', ',', '~')) or selector.isdigit()
    if (not names) or (names == metric_columns and not has_pattern):
        raise Exception(f"{field_name} '{metric_name}' did not match any selected metric column")
    return names[0]


def _to_float_or_raise(value, field_name='value'):
    number = _as_float(value)
    if number is None:
        raise Exception(f"{field_name} must be numeric")
    return number


def _default_numeric_metric(df, metric_columns):
    for column in metric_columns:
        if column not in df.columns:
            continue
        if df[column].apply(_as_float).notna().any():
            return column
    return metric_columns[0] if metric_columns else ''


def _safe_df2chart(df, x_column, y_columns, ylabel, chart_title, chart_type):
    if df is None or len(df) == 0:
        return None

    chart_data = QResults.df2chart_data(df, x_column=x_column, y_columns=y_columns)
    if not chart_data.get('yvalsm'):
        return None

    numeric_columns = []
    for column, series in zip(chart_data['ylabels'], chart_data['yvalsm']):
        if any(_as_float(value) is not None for value in series):
            numeric_columns.append(column)

    if not numeric_columns:
        return None

    try:
        return QResults.df2chart(
            df,
            x_column=x_column,
            y_columns=numeric_columns,
            ylabel=ylabel,
            chart_title=chart_title,
            chart_type=chart_type,
        )
    except Exception:
        return None


def _summary_as_table(summary: dict):
    rows = []
    for key, value in summary.items():
        if isinstance(value, list):
            display = ', '.join(str(v) for v in value)
        elif isinstance(value, dict):
            display = ', '.join(f"{k}: {v}" for k, v in value.items())
        else:
            display = value
        rows.append([key, display])
    return pd.DataFrame(rows, columns=['Field', 'Value'])


def _mode_rank(df, metric_columns, id_columns, variable_columns,
               rank_by='', rank_order='desc', top_n=0,
               show='both', chart_title='Scenario Rank Analysis', chart_type='bars'):
    variation_column = id_columns[0]
    output_df = df[id_columns + variable_columns + metric_columns].copy()
    rank_metric = _resolve_metric(metric_columns, rank_by, field_name='rank_by')
    if not str(rank_by).strip():
        rank_metric = _default_numeric_metric(output_df, metric_columns)
    ascending = str(rank_order).lower() in ('asc', 'ascending', 'low')

    output_df['_rank_value'] = output_df[rank_metric].apply(_as_float)
    output_df = output_df.sort_values(by='_rank_value', ascending=ascending, na_position='last').reset_index(drop=True)
    output_df['Rank'] = list(range(1, len(output_df) + 1))
    output_df = output_df.drop(columns=['_rank_value'])

    if int(top_n) > 0:
        output_df = output_df.head(int(top_n)).reset_index(drop=True)

    chart = None
    if show in ('both', 'chart') and len(output_df) > 0:
        chart_df = output_df[[variation_column, rank_metric]].copy()
        chart_df[rank_metric] = chart_df[rank_metric].apply(_as_float)
        chart = _safe_df2chart(
            chart_df,
            x_column=variation_column,
            y_columns=[rank_metric],
            ylabel=rank_metric,
            chart_title=chart_title,
            chart_type=chart_type,
        )

    summary = {
        'mode': 'rank',
        'rank_by': rank_metric,
        'rank_order': 'asc' if ascending else 'desc',
        'top_n': int(top_n),
        'metric_columns': metric_columns,
    }
    return {'table': output_df, 'chart': chart, 'summary': _summary_as_table(summary)}


def _build_filter_mask(series, operator_name, filter_value, filter_value2=''):
    operator_name = str(operator_name).strip().lower()
    if operator_name in ('contains',):
        needle = str(filter_value).strip().lower()
        return series.apply(lambda value: needle in str(value).lower())

    numbers = series.apply(_as_float)
    left = _to_float_or_raise(filter_value, field_name='filter_value')
    if operator_name in ('>', 'gt'):
        return numbers.apply(lambda value: value is not None and value > left)
    if operator_name in ('>=', 'ge'):
        return numbers.apply(lambda value: value is not None and value >= left)
    if operator_name in ('<', 'lt'):
        return numbers.apply(lambda value: value is not None and value < left)
    if operator_name in ('<=', 'le'):
        return numbers.apply(lambda value: value is not None and value <= left)
    if operator_name in ('between',):
        right = _to_float_or_raise(filter_value2, field_name='filter_value2')
        low = min(left, right)
        high = max(left, right)
        return numbers.apply(lambda value: value is not None and low <= value <= high)
    if operator_name in ('==', 'eq'):
        return series.apply(lambda value: str(value) == str(filter_value))
    if operator_name in ('!=', 'ne'):
        return series.apply(lambda value: str(value) != str(filter_value))

    raise Exception(
        "filter_operator must be one of >, >=, <, <=, ==, !=, between, contains"
    )


def _mode_filter(df, metric_columns, id_columns, variable_columns,
                 filter_by='', filter_operator='>=', filter_value='0', filter_value2='',
                 top_n=0, show='both', chart_title='Scenario Filter Analysis', chart_type='bars'):
    variation_column = id_columns[0]
    output_df = df[id_columns + variable_columns + metric_columns].copy()
    filter_metric = _resolve_metric(metric_columns, filter_by, field_name='filter_by')
    if not str(filter_by).strip():
        filter_metric = _default_numeric_metric(output_df, metric_columns)

    mask = _build_filter_mask(
        output_df[filter_metric],
        operator_name=filter_operator,
        filter_value=filter_value,
        filter_value2=filter_value2,
    )
    filtered = output_df[mask].copy().reset_index(drop=True)
    filtered['Rank'] = list(range(1, len(filtered) + 1))

    if int(top_n) > 0:
        filtered = filtered.head(int(top_n)).reset_index(drop=True)

    chart = None
    if show in ('both', 'chart') and len(filtered) > 0:
        chart_df = filtered[[variation_column] + metric_columns].copy()
        for column in metric_columns:
            chart_df[column] = chart_df[column].apply(_as_float)
        chart = _safe_df2chart(
            chart_df,
            x_column=variation_column,
            y_columns=metric_columns,
            ylabel='Filtered Metrics',
            chart_title=chart_title,
            chart_type=chart_type,
        )

    summary = {
        'mode': 'filter',
        'filter_by': filter_metric,
        'filter_operator': filter_operator,
        'filter_value': filter_value,
        'filter_value2': filter_value2,
        'rows_before': len(output_df),
        'rows_after': len(filtered),
        'top_n': int(top_n),
        'metric_columns': metric_columns,
    }
    return {'table': filtered, 'chart': chart, 'summary': _summary_as_table(summary)}


def _parse_metric_map(text: str):
    pairs = {}
    if not text:
        return pairs
    for item in css2strs(text):
        if ':' not in item:
            raise Exception(f"Invalid mapping '{item}'. Use 'Metric:Value' pairs")
        left, right = item.split(':', 1)
        key = left.strip()
        value = right.strip()
        if key == '':
            raise Exception(f"Invalid mapping '{item}'. Metric name cannot be blank")
        pairs[key] = value
    return pairs


def _resolve_metric_map(metric_columns: list[str], raw_map: dict):
    resolved = {}
    for key, value in raw_map.items():
        selector = str(key).strip()
        selector_low = selector.lower()
        keys = []
        for metric in metric_columns:
            title, _ = _split_title_unit(metric)
            if selector_low == str(metric).strip().lower() or selector_low == title.lower():
                keys.append(metric)

        if not keys:
            keys = specified_args(metric_columns, key)

        has_pattern = any(char in selector for char in ('*', '-', ',', '~')) or selector.isdigit()
        if (not keys) or (len(metric_columns) > 1 and keys == metric_columns and not has_pattern):
            raise Exception(f"Metric selector '{key}' did not match any selected metric")
        for name in keys:
            resolved[name] = value
    return resolved


def _mode_score(df, metric_columns, id_columns, variable_columns,
                score_weights='', score_directions='', score_column='Score',
                score_normalization='minmax', top_n=0,
                show='both', chart_title='Scenario Score Analysis', chart_type='bars'):
    variation_column = id_columns[0]
    output_df = df[id_columns + variable_columns + metric_columns].copy()

    if str(score_normalization).strip().lower() != 'minmax':
        raise Exception("score_normalization currently supports only 'minmax'")

    raw_weights = _parse_metric_map(score_weights)
    raw_directions = _parse_metric_map(score_directions)
    weights_map = _resolve_metric_map(metric_columns, raw_weights)
    directions_map = _resolve_metric_map(metric_columns, raw_directions)

    weights = {}
    directions = {}
    for metric in metric_columns:
        if metric in weights_map:
            weights[metric] = float(weights_map[metric])
        else:
            weights[metric] = 1.0

        direction = directions_map.get(metric, 'high').strip().lower()
        if direction in ('high', 'higher', 'max', 'desc'):
            directions[metric] = 'high'
        elif direction in ('low', 'lower', 'min', 'asc'):
            directions[metric] = 'low'
        else:
            raise Exception(f"Unknown score direction '{direction}' for metric '{metric}'")

    normalized = {metric: [] for metric in metric_columns}
    for metric in metric_columns:
        vals = [_as_float(value) for value in output_df[metric].tolist()]
        valid_vals = [value for value in vals if value is not None]
        if not valid_vals:
            normalized[metric] = [None] * len(vals)
            continue

        min_val = min(valid_vals)
        max_val = max(valid_vals)
        span = max_val - min_val
        direction = directions[metric]
        nvals = []
        for value in vals:
            if value is None:
                nvals.append(None)
            elif abs(span) <= 1e-12:
                nvals.append(1.0)
            elif direction == 'high':
                nvals.append((value - min_val) / span)
            else:
                nvals.append((max_val - value) / span)
        normalized[metric] = nvals

    scores = []
    for row_index in range(len(output_df)):
        weighted_sum = 0.0
        weight_sum = 0.0
        for metric in metric_columns:
            score_value = normalized[metric][row_index]
            weight = weights[metric]
            if score_value is None or abs(weight) <= 1e-12:
                continue
            weighted_sum += score_value * weight
            weight_sum += weight
        scores.append((weighted_sum / weight_sum) if weight_sum > 0 else None)

    output_df[score_column] = scores
    output_df = output_df.sort_values(
        by=score_column,
        ascending=False,
        na_position='last',
    ).reset_index(drop=True)
    output_df['Rank'] = list(range(1, len(output_df) + 1))

    if int(top_n) > 0:
        output_df = output_df.head(int(top_n)).reset_index(drop=True)

    chart = None
    if show in ('both', 'chart') and len(output_df) > 0:
        chart_df = output_df[[variation_column, score_column]]
        chart = _safe_df2chart(
            chart_df,
            x_column=variation_column,
            y_columns=[score_column],
            ylabel=score_column,
            chart_title=chart_title,
            chart_type=chart_type,
        )

    summary = {
        'mode': 'score',
        'metric_columns': metric_columns,
        'score_column': score_column,
        'weights': weights,
        'directions': directions,
        'score_normalization': 'minmax',
        'top_n': int(top_n),
    }
    return {'table': output_df, 'chart': chart, 'summary': _summary_as_table(summary)}


def _mode_delta(df, metric_columns, id_columns, variable_columns,
                baseline_variation='', delta_type='absolute',
                show='both', chart_title='Scenario Delta Analysis', chart_type='bars'):
    variation_column = id_columns[0]
    if variation_column not in df.columns:
        raise Exception(f"Scenario table must include '{variation_column}' column")

    labels = df[variation_column].astype(str).tolist()
    if not labels:
        raise Exception('Scenario table has no data rows')
    if baseline_variation:
        if baseline_variation not in labels:
            raise Exception(f"Baseline variation '{baseline_variation}' not found")
        baseline_index = labels.index(baseline_variation)
    else:
        baseline_index = 0
        baseline_variation = labels[0]

    output_df = df[id_columns + variable_columns + metric_columns].copy()
    delta_columns = []
    for column in metric_columns:
        values = output_df[column].tolist()
        base_value = _as_float(values[baseline_index])
        dcol = _delta_column_name(column, delta_type)
        output_df[dcol] = _delta_values(values, base_value, delta_type)
        delta_columns.append(dcol)

    chart = None
    if show in ('both', 'chart'):
        chart_df = output_df[[variation_column] + delta_columns]
        ylabel = 'Delta' if delta_type == 'absolute' else ('Delta (%)' if delta_type == 'percent' else 'Index')
        chart = _safe_df2chart(
            chart_df,
            x_column=variation_column,
            y_columns=delta_columns,
            ylabel=ylabel,
            chart_title=chart_title,
            chart_type=chart_type,
        )

    summary = {
        'mode': 'delta',
        'baseline_variation': baseline_variation,
        'metric_columns': metric_columns,
        'delta_type': delta_type,
    }
    return {'table': output_df, 'chart': chart, 'summary': _summary_as_table(summary)}


def postprocess_scenarios(
    scenario_table,
    mode='delta',
    metric_columns: str = '',
    metric_units: str = '',
    id_columns: str = 'Variation',
    variable_columns: str = '',
    baseline_variation: str = '',
    delta_type='absolute',
    rank_by: str = '',
    rank_order='desc',
    top_n=0,
    filter_by: str = '',
    filter_operator='>=',
    filter_value='0',
    filter_value2='',
    score_weights: str = '',
    score_directions: str = '',
    score_column='Score',
    score_normalization='minmax',
    show='both',
    chart_title='Scenario Analysis',
    chart_type='bars',
):
    df = _to_df(scenario_table)
    id_cols = css2strs(id_columns)
    if not id_cols:
        id_cols = ['Variation']
    var_cols = css2strs(variable_columns)

    for column in id_cols + var_cols:
        if column not in df.columns:
            raise Exception(f"Column '{column}' was not found in scenario table")

    metrics = _select_metric_columns(
        df,
        metric_columns=metric_columns,
        metric_units=metric_units,
        id_columns=id_cols,
        variable_columns=var_cols,
    )

    if mode == 'delta':
        return _mode_delta(
            df,
            metric_columns=metrics,
            id_columns=id_cols,
            variable_columns=var_cols,
            baseline_variation=baseline_variation,
            delta_type=delta_type,
            show=show,
            chart_title=chart_title,
            chart_type=chart_type,
        )

    if mode == 'rank':
        return _mode_rank(
            df,
            metric_columns=metrics,
            id_columns=id_cols,
            variable_columns=var_cols,
            rank_by=rank_by,
            rank_order=rank_order,
            top_n=top_n,
            show=show,
            chart_title=chart_title,
            chart_type=chart_type,
        )

    if mode == 'filter':
        return _mode_filter(
            df,
            metric_columns=metrics,
            id_columns=id_cols,
            variable_columns=var_cols,
            filter_by=filter_by,
            filter_operator=filter_operator,
            filter_value=filter_value,
            filter_value2=filter_value2,
            top_n=top_n,
            show=show,
            chart_title=chart_title,
            chart_type=chart_type,
        )

    if mode == 'score':
        return _mode_score(
            df,
            metric_columns=metrics,
            id_columns=id_cols,
            variable_columns=var_cols,
            score_weights=score_weights,
            score_directions=score_directions,
            score_column=score_column,
            score_normalization=score_normalization,
            top_n=top_n,
            show=show,
            chart_title=chart_title,
            chart_type=chart_type,
        )

    raise Exception(f"Mode '{mode}' is not implemented yet")
