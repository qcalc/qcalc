# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from math import sqrt
from statistics import NormalDist

from qcore import qtbl, QChart, qhtml


def _qtbl(columns, data_rows):
    return {
        'columns': columns,
        'data': data_rows,
    }


def _to_float(value, field_name):
    try:
        fval = float(value)
    except Exception as exc:
        raise Exception(f'{field_name} must be numeric') from exc
    if fval != fval or fval in (float('inf'), float('-inf')):
        raise Exception(f'{field_name} must be finite')
    return fval


def _extract_series(historical_data):
    if not isinstance(historical_data, dict):
        raise Exception('Historical observations must be a qtbl dictionary')

    columns = historical_data.get('columns', [])
    rows = historical_data.get('data', [])

    if not columns or not rows:
        raise Exception('Historical observations table cannot be empty')

    col_lookup = {str(name).strip().lower(): idx for idx, name in enumerate(columns)}
    period_idx = col_lookup.get('period', 0)
    value_idx = col_lookup.get('value', 1 if len(columns) > 1 else 0)

    periods = []
    values = []

    for row_no, row in enumerate(rows, start=1):
        if not isinstance(row, (list, tuple)):
            raise Exception(f'Row {row_no} in historical observations must be a row array')
        if len(row) <= max(period_idx, value_idx):
            raise Exception(f'Row {row_no} does not contain expected Period and Value columns')

        period = str(row[period_idx]).strip()
        value = _to_float(row[value_idx], f'Value at row {row_no}')

        periods.append(period if period else f'R{row_no}')
        values.append(value)

    return periods, values


def _mean(values):
    return sum(values) / len(values)


def _mae(actual, pred):
    n = len(actual)
    if n == 0:
        return None
    return sum(abs(a - p) for a, p in zip(actual, pred)) / n


def _rmse(actual, pred):
    n = len(actual)
    if n == 0:
        return None
    return sqrt(sum((a - p) ** 2 for a, p in zip(actual, pred)) / n)


def _mape(actual, pred):
    pairs = [(a, p) for a, p in zip(actual, pred) if a > 0]
    if not pairs:
        return None
    return 100.0 * sum(abs((a - p) / a) for a, p in pairs) / len(pairs)


def _safe_round(value, digits=4):
    if value is None:
        return ''
    return round(float(value), digits)


def _grid_points(step=0.1):
    p = []
    x = step
    while x < 1.0:
        p.append(round(x, 4))
        x += step
    return p


def _fit_constant(values):
    level = _mean(values)
    fitted = [level for _ in values]
    residuals = [v - f for v, f in zip(values, fitted)]
    level_series = [level for _ in values]
    trend_series = [0.0 for _ in values]
    seasonal_series = [0.0 for _ in values]
    return {
        'params': {},
        'fitted': fitted,
        'residuals': residuals,
        'level': level_series,
        'trend': trend_series,
        'seasonal': seasonal_series,
        'state': {'level': level, 'trend': 0.0, 'seasonals': []},
    }


def _fit_ses(values, alpha):
    n = len(values)
    level = values[0]
    fitted = [values[0]]
    level_series = [level]

    for i in range(1, n):
        fitted.append(level)
        level = alpha * values[i] + (1 - alpha) * level
        level_series.append(level)

    residuals = [v - f for v, f in zip(values, fitted)]
    return {
        'params': {'alpha': alpha},
        'fitted': fitted,
        'residuals': residuals,
        'level': level_series,
        'trend': [0.0 for _ in values],
        'seasonal': [0.0 for _ in values],
        'state': {'level': level, 'trend': 0.0, 'seasonals': []},
    }


def _fit_holt(values, alpha, beta):
    n = len(values)
    level = values[0]
    trend = values[1] - values[0] if n > 1 else 0.0

    fitted = [values[0]]
    level_series = [level]
    trend_series = [trend]

    for i in range(1, n):
        fitted.append(level + trend)
        prev_level = level
        level = alpha * values[i] + (1 - alpha) * (level + trend)
        trend = beta * (level - prev_level) + (1 - beta) * trend
        level_series.append(level)
        trend_series.append(trend)

    residuals = [v - f for v, f in zip(values, fitted)]
    return {
        'params': {'alpha': alpha, 'beta': beta},
        'fitted': fitted,
        'residuals': residuals,
        'level': level_series,
        'trend': trend_series,
        'seasonal': [0.0 for _ in values],
        'state': {'level': level, 'trend': trend, 'seasonals': []},
    }


def _initial_seasonals_add(values, season_len):
    n = len(values)
    seasonals = [0.0 for _ in range(season_len)]

    if n >= season_len * 2:
        cycles = n // season_len
        season_means = []
        for c in range(cycles):
            start = c * season_len
            season_means.append(_mean(values[start:start + season_len]))

        for i in range(season_len):
            accum = 0.0
            for c in range(cycles):
                accum += values[c * season_len + i] - season_means[c]
            seasonals[i] = accum / cycles
        return seasonals

    base = _mean(values[:season_len])
    for i in range(season_len):
        seasonals[i] = values[i] - base
    return seasonals


def _initial_seasonals_mul(values, season_len):
    n = len(values)
    seasonals = [1.0 for _ in range(season_len)]

    if n >= season_len * 2:
        cycles = n // season_len
        season_means = []
        for c in range(cycles):
            start = c * season_len
            season_means.append(_mean(values[start:start + season_len]))

        for i in range(season_len):
            accum = 0.0
            for c in range(cycles):
                mean_c = season_means[c]
                accum += values[c * season_len + i] / mean_c if mean_c != 0 else 1.0
            seasonals[i] = accum / cycles
        return seasonals

    base = _mean(values[:season_len])
    for i in range(season_len):
        seasonals[i] = values[i] / base if base != 0 else 1.0
    return seasonals


def _fit_hw_add(values, alpha, beta, gamma, season_len):
    n = len(values)
    seasonals = _initial_seasonals_add(values, season_len)
    level = _mean(values[:season_len])
    trend = 0.0
    if n >= season_len * 2:
        trend = (_mean(values[season_len:season_len * 2]) - _mean(values[:season_len])) / season_len

    fitted = []
    level_series = []
    trend_series = []
    seasonal_series = []

    for i in range(n):
        if i < season_len:
            s_tm = seasonals[i]
        else:
            s_tm = seasonals[i - season_len]

        if i == 0:
            fitted_val = values[0]
        else:
            fitted_val = level + trend + s_tm
        fitted.append(fitted_val)

        prev_level = level
        level = alpha * (values[i] - s_tm) + (1 - alpha) * (level + trend)
        trend = beta * (level - prev_level) + (1 - beta) * trend
        s_new = gamma * (values[i] - level) + (1 - gamma) * s_tm

        if i < season_len:
            seasonals[i] = s_new
        else:
            seasonals.append(s_new)

        level_series.append(level)
        trend_series.append(trend)
        seasonal_series.append(s_tm)

    residuals = [v - f for v, f in zip(values, fitted)]
    return {
        'params': {'alpha': alpha, 'beta': beta, 'gamma': gamma},
        'fitted': fitted,
        'residuals': residuals,
        'level': level_series,
        'trend': trend_series,
        'seasonal': seasonal_series,
        'state': {'level': level, 'trend': trend, 'seasonals': seasonals, 'season_len': season_len},
    }


def _fit_hw_mul(values, alpha, beta, gamma, season_len):
    n = len(values)
    seasonals = _initial_seasonals_mul(values, season_len)
    level = _mean(values[:season_len])
    trend = 0.0
    if n >= season_len * 2:
        trend = (_mean(values[season_len:season_len * 2]) - _mean(values[:season_len])) / season_len

    fitted = []
    level_series = []
    trend_series = []
    seasonal_series = []

    for i in range(n):
        if i < season_len:
            s_tm = seasonals[i]
        else:
            s_tm = seasonals[i - season_len]

        if i == 0:
            fitted_val = values[0]
        else:
            fitted_val = (level + trend) * s_tm
        fitted.append(fitted_val)

        safe_stm = s_tm if s_tm != 0 else 1.0
        prev_level = level
        level = alpha * (values[i] / safe_stm) + (1 - alpha) * (level + trend)
        trend = beta * (level - prev_level) + (1 - beta) * trend

        safe_level = level if level != 0 else 1.0
        s_new = gamma * (values[i] / safe_level) + (1 - gamma) * s_tm

        if i < season_len:
            seasonals[i] = s_new
        else:
            seasonals.append(s_new)

        level_series.append(level)
        trend_series.append(trend)
        seasonal_series.append(s_tm)

    residuals = [v - f for v, f in zip(values, fitted)]
    return {
        'params': {'alpha': alpha, 'beta': beta, 'gamma': gamma},
        'fitted': fitted,
        'residuals': residuals,
        'level': level_series,
        'trend': trend_series,
        'seasonal': seasonal_series,
        'state': {'level': level, 'trend': trend, 'seasonals': seasonals, 'season_len': season_len},
    }


def _fit_seasonal_add(values, alpha, gamma, season_len):
    n = len(values)
    seasonals = _initial_seasonals_add(values, season_len)
    level = _mean(values[:season_len])

    fitted = []
    level_series = []
    seasonal_series = []

    for i in range(n):
        if i < season_len:
            s_tm = seasonals[i]
        else:
            s_tm = seasonals[i - season_len]

        if i == 0:
            fitted_val = values[0]
        else:
            fitted_val = level + s_tm
        fitted.append(fitted_val)

        level = alpha * (values[i] - s_tm) + (1 - alpha) * level
        s_new = gamma * (values[i] - level) + (1 - gamma) * s_tm

        if i < season_len:
            seasonals[i] = s_new
        else:
            seasonals.append(s_new)

        level_series.append(level)
        seasonal_series.append(s_tm)

    residuals = [v - f for v, f in zip(values, fitted)]
    return {
        'params': {'alpha': alpha, 'gamma': gamma},
        'fitted': fitted,
        'residuals': residuals,
        'level': level_series,
        'trend': [0.0 for _ in values],
        'seasonal': seasonal_series,
        'state': {'level': level, 'trend': 0.0, 'seasonals': seasonals, 'season_len': season_len},
    }


def _fit_seasonal_mul(values, alpha, gamma, season_len):
    n = len(values)
    seasonals = _initial_seasonals_mul(values, season_len)
    level = _mean(values[:season_len])

    fitted = []
    level_series = []
    seasonal_series = []

    for i in range(n):
        if i < season_len:
            s_tm = seasonals[i]
        else:
            s_tm = seasonals[i - season_len]

        if i == 0:
            fitted_val = values[0]
        else:
            fitted_val = level * s_tm
        fitted.append(fitted_val)

        safe_stm = s_tm if s_tm != 0 else 1.0
        level = alpha * (values[i] / safe_stm) + (1 - alpha) * level
        safe_level = level if level != 0 else 1.0
        s_new = gamma * (values[i] / safe_level) + (1 - gamma) * s_tm

        if i < season_len:
            seasonals[i] = s_new
        else:
            seasonals.append(s_new)

        level_series.append(level)
        seasonal_series.append(s_tm)

    residuals = [v - f for v, f in zip(values, fitted)]
    return {
        'params': {'alpha': alpha, 'gamma': gamma},
        'fitted': fitted,
        'residuals': residuals,
        'level': level_series,
        'trend': [0.0 for _ in values],
        'seasonal': seasonal_series,
        'state': {'level': level, 'trend': 0.0, 'seasonals': seasonals, 'season_len': season_len},
    }


def _forecast_from_state(model_key, fit_out, horizon):
    state = fit_out['state']
    result = []

    if model_key == 'constant':
        level = state['level']
        for _ in range(horizon):
            result.append(level)

    elif model_key == 'ses':
        level = state['level']
        for _ in range(horizon):
            result.append(level)

    elif model_key == 'holt':
        level = state['level']
        trend = state['trend']
        for h in range(1, horizon + 1):
            result.append(level + h * trend)

    elif model_key == 'seasonal_add':
        level = state['level']
        seasonals = state['seasonals']
        season_len = state['season_len']
        base_index = len(seasonals) - season_len
        for h in range(1, horizon + 1):
            s_h = seasonals[base_index + ((h - 1) % season_len)]
            result.append(level + s_h)

    elif model_key == 'seasonal_mul':
        level = state['level']
        seasonals = state['seasonals']
        season_len = state['season_len']
        base_index = len(seasonals) - season_len
        for h in range(1, horizon + 1):
            s_h = seasonals[base_index + ((h - 1) % season_len)]
            result.append(level * s_h)

    elif model_key == 'hw_add':
        level = state['level']
        trend = state['trend']
        seasonals = state['seasonals']
        season_len = state['season_len']
        base_index = len(seasonals) - season_len
        for h in range(1, horizon + 1):
            s_h = seasonals[base_index + ((h - 1) % season_len)]
            result.append(level + h * trend + s_h)

    elif model_key == 'hw_mul':
        level = state['level']
        trend = state['trend']
        seasonals = state['seasonals']
        season_len = state['season_len']
        base_index = len(seasonals) - season_len
        for h in range(1, horizon + 1):
            s_h = seasonals[base_index + ((h - 1) % season_len)]
            result.append((level + h * trend) * s_h)

    return result


def _fit_model(values, model_key, season_len=None, manual_params=None):
    if model_key == 'constant':
        return _fit_constant(values)

    if model_key == 'ses':
        if manual_params is not None:
            return _fit_ses(values, manual_params['alpha'])
        best = None
        for alpha in _grid_points(0.05):
            fit = _fit_ses(values, alpha)
            sse = sum(r * r for r in fit['residuals'][1:])
            if best is None or sse < best[0]:
                best = (sse, fit)
        return best[1]

    if model_key == 'holt':
        if manual_params is not None:
            return _fit_holt(values, manual_params['alpha'], manual_params['beta'])
        best = None
        points = _grid_points(0.1)
        for alpha in points:
            for beta in points:
                fit = _fit_holt(values, alpha, beta)
                sse = sum(r * r for r in fit['residuals'][1:])
                if best is None or sse < best[0]:
                    best = (sse, fit)
        return best[1]

    if model_key == 'seasonal_add':
        if manual_params is not None:
            return _fit_seasonal_add(
                values,
                manual_params['alpha'],
                manual_params['gamma'],
                season_len,
            )
        best = None
        points = [0.2, 0.4, 0.6, 0.8]
        for alpha in points:
            for gamma in points:
                fit = _fit_seasonal_add(values, alpha, gamma, season_len)
                sse = sum(r * r for r in fit['residuals'][season_len:])
                if best is None or sse < best[0]:
                    best = (sse, fit)
        return best[1]

    if model_key == 'seasonal_mul':
        if manual_params is not None:
            return _fit_seasonal_mul(
                values,
                manual_params['alpha'],
                manual_params['gamma'],
                season_len,
            )
        best = None
        points = [0.2, 0.4, 0.6, 0.8]
        for alpha in points:
            for gamma in points:
                fit = _fit_seasonal_mul(values, alpha, gamma, season_len)
                sse = sum(r * r for r in fit['residuals'][season_len:])
                if best is None or sse < best[0]:
                    best = (sse, fit)
        return best[1]

    if model_key == 'hw_add':
        if manual_params is not None:
            return _fit_hw_add(
                values,
                manual_params['alpha'],
                manual_params['beta'],
                manual_params['gamma'],
                season_len,
            )
        best = None
        points = [0.2, 0.4, 0.6, 0.8]
        for alpha in points:
            for beta in points:
                for gamma in points:
                    fit = _fit_hw_add(values, alpha, beta, gamma, season_len)
                    sse = sum(r * r for r in fit['residuals'][season_len:])
                    if best is None or sse < best[0]:
                        best = (sse, fit)
        return best[1]

    if model_key == 'hw_mul':
        if manual_params is not None:
            return _fit_hw_mul(
                values,
                manual_params['alpha'],
                manual_params['beta'],
                manual_params['gamma'],
                season_len,
            )
        best = None
        points = [0.2, 0.4, 0.6, 0.8]
        for alpha in points:
            for beta in points:
                for gamma in points:
                    fit = _fit_hw_mul(values, alpha, beta, gamma, season_len)
                    sse = sum(r * r for r in fit['residuals'][season_len:])
                    if best is None or sse < best[0]:
                        best = (sse, fit)
        return best[1]

    raise Exception('Unsupported model')


def _model_name(model_key):
    names = {
        'constant': 'Constant baseline',
        'ses': 'Simple Exponential Smoothing',
        'seasonal_add': 'Seasonal Additive (No Trend)',
        'seasonal_mul': 'Seasonal Multiplicative (No Trend)',
        'holt': 'Holt Linear Trend',
        'hw_add': 'Holt-Winters Additive',
        'hw_mul': 'Holt-Winters Multiplicative',
    }
    return names.get(model_key, model_key)


def _model_components(model_key):
    mapping = {
        'constant': ('constant', 'none', 'none'),
        'ses': ('changing', 'none', 'none'),
        'seasonal_add': ('changing', 'none', 'additive'),
        'seasonal_mul': ('changing', 'none', 'multiplicative'),
        'holt': ('changing', 'linear', 'none'),
        'hw_add': ('changing', 'linear', 'additive'),
        'hw_mul': ('changing', 'linear', 'multiplicative'),
    }
    if model_key not in mapping:
        raise Exception(f'Unsupported model key: {model_key}')
    return mapping[model_key]


def _residual_rmse_for_selection(model_key, fit_out, season_len):
    residuals = fit_out['residuals']
    start_idx = season_len if model_key in ('seasonal_add', 'seasonal_mul', 'hw_add', 'hw_mul') else 1
    used = residuals[start_idx:] if len(residuals) > start_idx else residuals
    if not used:
        return float('inf')
    return sqrt(sum(r * r for r in used) / len(used))


def _holdout_rmse_for_selection(values, model_key, season_len, holdout_rows):
    if holdout_rows <= 0 or holdout_rows >= len(values):
        return None

    train_values = values[:-holdout_rows]
    test_values = values[-holdout_rows:]

    # Candidate must be trainable on the reduced training window.
    _validate_inputs(train_values, model_key, season_len)

    fit_train = _fit_model(train_values, model_key, season_len=season_len, manual_params=None)
    pred_test = _forecast_from_state(model_key, fit_train, holdout_rows)
    rmse = _rmse(test_values, pred_test)
    return float('inf') if rmse is None else rmse


def _select_model_automatic(values, season_len, holdout_rows=0):
    candidates = ['constant', 'ses', 'seasonal_add', 'seasonal_mul', 'holt', 'hw_add', 'hw_mul']
    holdout_best = None
    insample_best = None
    diagnostics = []

    for model_key in candidates:
        row = {
            'model_key': model_key,
            'model_name': _model_name(model_key),
            'insample_rmse': None,
            'holdout_rmse': None,
            'eligible_insample': False,
            'eligible_holdout': holdout_rows <= 0,
            'note': '',
        }
        try:
            _validate_inputs(values, model_key, season_len)
            fit_out = _fit_model(values, model_key, season_len=season_len, manual_params=None)
            insample_score = _residual_rmse_for_selection(model_key, fit_out, season_len)
            row['eligible_insample'] = True
            row['insample_rmse'] = insample_score
            if insample_best is None or insample_score < insample_best[0]:
                insample_best = (insample_score, model_key)

            if holdout_rows > 0:
                try:
                    holdout_score = _holdout_rmse_for_selection(values, model_key, season_len, holdout_rows)
                    if holdout_score is not None:
                        row['eligible_holdout'] = True
                        row['holdout_rmse'] = holdout_score
                        if holdout_best is None or holdout_score < holdout_best[0]:
                            holdout_best = (holdout_score, model_key)
                except Exception as exc:
                    # Not all candidate models can be trained with the current holdout split.
                    row['note'] = str(exc)
        except Exception as exc:
            row['note'] = str(exc)

        diagnostics.append(row)

    if holdout_best is not None:
        selected_key = holdout_best[1]
        return selected_key, _model_name(selected_key), 'holdout-rmse', diagnostics

    if insample_best is None:
        raise Exception('Automatic mode could not find a valid model for the provided data')

    selected_key = insample_best[1]
    return selected_key, _model_name(selected_key), 'in-sample-residual-rmse', diagnostics


def _model_key(level_mode, trend_mode, seasonality_mode):
    if level_mode == 'constant' and trend_mode == 'none' and seasonality_mode == 'none':
        return 'constant', 'Constant baseline'
    if level_mode == 'changing' and trend_mode == 'none' and seasonality_mode == 'none':
        return 'ses', 'Simple Exponential Smoothing'
    if level_mode == 'changing' and trend_mode == 'none' and seasonality_mode == 'additive':
        return 'seasonal_add', 'Seasonal Additive (No Trend)'
    if level_mode == 'changing' and trend_mode == 'none' and seasonality_mode == 'multiplicative':
        return 'seasonal_mul', 'Seasonal Multiplicative (No Trend)'
    if level_mode == 'changing' and trend_mode == 'linear' and seasonality_mode == 'none':
        return 'holt', 'Holt Linear Trend'
    if level_mode == 'changing' and trend_mode == 'linear' and seasonality_mode == 'additive':
        return 'hw_add', 'Holt-Winters Additive'
    if level_mode == 'changing' and trend_mode == 'linear' and seasonality_mode == 'multiplicative':
        return 'hw_mul', 'Holt-Winters Multiplicative'

    raise Exception(
        'Selected component combination is not supported in phase 1. '
        'Use one of: constant baseline, changing level, seasonal without trend, Holt linear, or Holt-Winters seasonal.'
    )


def _required_min_obs(model_key, season_len):
    if model_key in ('seasonal_add', 'seasonal_mul', 'hw_add', 'hw_mul'):
        return max(8, 2 * season_len)
    return 8


def _validate_inputs(values, model_key, season_len):
    need = _required_min_obs(model_key, season_len)
    if len(values) < need:
        raise Exception(f'Not enough observations for selected model. Need at least {need} rows')

    if model_key in ('seasonal_mul', 'hw_mul') and any(v <= 0 for v in values):
        raise Exception('Multiplicative seasonality requires all Value entries to be greater than zero')


def _z_for_confidence(confidence_level):
    p = confidence_level / 100.0
    return NormalDist().inv_cdf(0.5 + p / 2.0)


def _interval_scale(model_key, horizon, model_params):
    alpha = float(model_params.get('alpha', 0.2))
    beta = float(model_params.get('beta', 0.2))
    gamma = float(model_params.get('gamma', 0.2))
    h = float(horizon)

    if model_key == 'constant':
        factor = 1.0 + 0.10 * h
    elif model_key == 'ses':
        factor = 1.0 + (alpha ** 2) * max(0.0, h - 1.0)
    elif model_key in ('seasonal_add', 'seasonal_mul'):
        factor = 1.0 + 0.20 * h + (gamma ** 2) * 0.50 * h
    elif model_key == 'holt':
        factor = 1.0 + 0.25 * h + (beta ** 2) * h * (h - 1.0) / 2.0
    elif model_key in ('hw_add', 'hw_mul'):
        factor = 1.0 + 0.25 * h + (beta ** 2) * h * (h - 1.0) / 2.0 + (gamma ** 2) * 0.40 * h
    else:
        factor = max(1.0, h)

    return sqrt(max(1e-9, factor))


def _build_forecast_table(point_forecast, confidence_level, sigma, random_mode, model_key, model_params):
    rows = []
    z = _z_for_confidence(confidence_level) if random_mode == 'historical' and sigma is not None else None

    for i, fval in enumerate(point_forecast, start=1):
        period_label = f'F{i}'
        if z is None:
            lo = ''
            hi = ''
        else:
            scale = _interval_scale(model_key, i, model_params)
            lo = fval - z * sigma * scale
            hi = fval + z * sigma * scale

        rows.append([
            period_label,
            _safe_round(fval),
            _safe_round(lo) if lo != '' else '',
            _safe_round(hi) if hi != '' else '',
        ])

    return _qtbl(['Period', 'Forecast', f'Lower {confidence_level}%', f'Upper {confidence_level}%'], rows)


def _build_model_selection_table(diagnostics_rows, selected_model_key, selection_basis):
    rows = []
    for row in diagnostics_rows:
        selected = 'Yes' if row['model_key'] == selected_model_key else ''
        rows.append([
            row['model_name'],
            row['model_key'],
            'Yes' if row['eligible_insample'] else 'No',
            _safe_round(row['insample_rmse']) if row['insample_rmse'] is not None else '',
            'Yes' if row['eligible_holdout'] else 'No',
            _safe_round(row['holdout_rmse']) if row['holdout_rmse'] is not None else '',
            selected,
            selection_basis if selected else '',
            row['note'],
        ])

    return _qtbl(
        [
            'Model',
            'Key',
            'Eligible In-Sample',
            'In-Sample RMSE',
            'Eligible Holdout',
            'Holdout RMSE',
            'Selected',
            'Selection Basis',
            'Note',
        ],
        rows,
    )


def _build_decomposition_table(periods, values, fit_out):
    rows = []
    fitted = fit_out['fitted']
    level = fit_out['level']
    trend = fit_out['trend']
    seasonal = fit_out['seasonal']

    for i in range(len(values)):
        resid = values[i] - fitted[i]
        rows.append([
            periods[i],
            _safe_round(level[i]),
            _safe_round(trend[i]),
            _safe_round(seasonal[i]),
            _safe_round(resid),
            _safe_round(fitted[i]),
            _safe_round(values[i]),
        ])

    return _qtbl(['Period', 'Level', 'Trend', 'Seasonal', 'Residual', 'Fitted', 'Actual'], rows)


def _build_accuracy(actual, pred, mode_label, train_size, test_size):
    mape = _mape(actual, pred)
    rows = [
        ['Validation mode', mode_label],
        ['Training rows', train_size],
        ['Test rows', test_size],
        ['MAE', _safe_round(_mae(actual, pred))],
        ['RMSE', _safe_round(_rmse(actual, pred))],
        ['MAPE %', _safe_round(mape) if mape is not None else ''],
    ]
    return _qtbl(['Metric', 'Value'], rows)


def _build_primary_chart(periods, values, fit_out, point_forecast, random_mode, confidence_level, sigma, model_key):
    horizon = len(point_forecast)
    total_points = len(values) + horizon
    xvals = list(range(total_points))
    xlabels = [f'P{i}' for i in range(1, len(values) + 1)] + [f'F{i}' for i in range(1, horizon + 1)]

    nan = float('nan')
    actual_series = list(values) + [nan for _ in range(horizon)]
    fitted_series = list(fit_out['fitted']) + [nan for _ in range(horizon)]
    forecast_series = [nan for _ in range(len(values))] + list(point_forecast)

    yvalsm = [actual_series, fitted_series, forecast_series]
    ylabels = ['Actual', 'Fitted', 'Forecast']

    if random_mode == 'historical' and sigma is not None:
        z = _z_for_confidence(confidence_level)
        model_params = fit_out.get('params', {})
        lower_series = [nan for _ in range(len(values))]
        upper_series = [nan for _ in range(len(values))]
        for i, fval in enumerate(point_forecast, start=1):
            scale = _interval_scale(model_key, i, model_params)
            lower_series.append(fval - z * sigma * scale)
            upper_series.append(fval + z * sigma * scale)
        yvalsm.extend([lower_series, upper_series])
        ylabels.extend([f'Lower {confidence_level}%', f'Upper {confidence_level}%'])

    chart = QChart()
    chart.render_lines(
        xvals=xvals,
        yvalsm=yvalsm,
        xlabel='Period',
        ylabels=ylabels,
        ylabel='Value',
        title='Forecast: Actual, Fitted, and Future Projection',
        x_tick_labels=xlabels,
        x_tick_max_labels=12,
        x_tick_rotation=25,
    )
    return chart


def _validate_smoothing(name, value):
    fvalue = _to_float(value, name)
    if not (0.0 < fvalue < 1.0):
        raise Exception(f'{name} must be greater than 0 and less than 1')
    return fvalue


def _manual_params(method_mode, model_key, alpha, beta, gamma):
    if method_mode != 'manual-components':
        return None

    params = {'alpha': _validate_smoothing('alpha', alpha)}

    if model_key in ('holt', 'hw_add', 'hw_mul'):
        params['beta'] = _validate_smoothing('beta', beta)

    if model_key in ('seasonal_add', 'seasonal_mul', 'hw_add', 'hw_mul'):
        params['gamma'] = _validate_smoothing('gamma', gamma)

    return params


def _fit_and_forecast(values, model_key, horizon, season_len, manual_params=None):
    fit_out = _fit_model(values, model_key, season_len=season_len, manual_params=manual_params)
    point_forecast = _forecast_from_state(model_key, fit_out, horizon)
    return fit_out, point_forecast


def forecast__info():
    return {
        'title': 'Forecasting Model (Decomposition-Based)',
        'desc': (
            'Create forecasts from choices for level, trend, seasonality, and random variation. '
        ),
        'calculate': 'Forecast',
        'schema': {
            'historical_data': {
                'label': 'Historical observations',
                'help_text': 'Input table with columns Period and Value',
            },
            'forecast_periods': {
                'label': 'Forecast periods',
                'help_text': 'Number of future periods to forecast',
            },
            'method_mode': {
                'label': 'Forecast method',
                'type': 'choice',
                'choices': {
                    'automatic': 'Automatic',
                    'manual-components': 'Manual components',
                },
                'help_text': 'Automatic estimates smoothing parameters; manual uses your alpha, beta, gamma values',
            },
            'level_mode': {
                'label': 'Level',
                'type': 'choice',
                'choices': {
                    'constant': 'Constant',
                    'changing': 'Changing',
                },
                'help_text': 'Baseline behavior: Constant uses one level, Changing allows level adaptation over time',
            },
            'alpha': {
                'label': 'Alpha (level smoothing)',
                'help_text': 'Used in manual-components mode. Range: 0 < alpha < 1',
            },
            'trend_mode': {
                'label': 'Trend',
                'type': 'choice',
                'choices': {
                    'none': 'None',
                    'linear': 'Linear',
                },
                'help_text': 'Trend structure: None or linear growth/decline over time',
            },
            'beta': {
                'label': 'Beta (trend smoothing)',
                'help_text': 'Used in manual-components mode for trend models. Range: 0 < beta < 1',
            },
            'seasonality_mode': {
                'label': 'Seasonality',
                'type': 'choice',
                'choices': {
                    'none': 'None',
                    'additive': 'Additive',
                    'multiplicative': 'Multiplicative',
                },
                'help_text': 'Seasonal structure: additive for fixed seasonal amplitude, multiplicative for level-scaled amplitude',
            },
            'gamma': {
                'label': 'Gamma (seasonality smoothing)',
                'help_text': 'Used in manual-components mode for seasonal models. Range: 0 < gamma < 1',
            },
            'random_mode': {
                'label': 'Random fluctuations',
                'type': 'choice',
                'choices': {
                    'none': 'None',
                    'historical': 'Historical',
                },
                'help_text': 'Uncertainty handling: None for point forecast only, Historical for interval estimation from residuals',
            },
            'seasonal_period': {
                'label': 'Seasonal period',
                'help_text': 'Required when seasonality is additive or multiplicative',
            },
            'confidence_level': {
                'label': 'Confidence level (%)',
                'help_text': 'Used for interval bounds when random mode is Historical',
            },
            'validation_mode': {
                'label': 'Validation mode',
                'type': 'choice',
                'choices': {
                    'holdout': 'Holdout',
                    'in_sample': 'In-sample',
                },
                'help_text': 'Accuracy evaluation mode: Holdout tests future-like data, In-sample evaluates fit on all rows',
            },
            'holdout_percent': {
                'label': 'Holdout split (%)',
                'help_text': 'Used when validation mode is Holdout',
            },
        },
        'showhide': {
            'seasonality_mode': {
                'fields': ['seasonal_period', 'gamma'],
                'callback': 'showSeasonalityDependents',
            },
            'trend_mode': {
                'fields': ['beta'],
                'callback': 'showTrendDependents',
            },
            'random_mode': {
                'fields': ['confidence_level'],
                'callback': 'showConfidence',
            },
            'validation_mode': {
                'fields': ['holdout_percent'],
                'callback': 'showHoldoutPct',
            },
            'method_mode': {
                'fields': ['level_mode', 'alpha', 'trend_mode', 'beta', 'seasonality_mode', 'gamma', 'seasonal_period'],
                'callback': 'showMethodDependents',
            },
        },
        'script': """
        function getModeValue(fieldName){
            const elem = document.querySelector(`[id$='_${fieldName}']`);
            return elem ? elem.value : '';
        }
        function showSeasonalityDependents(v){
            const methodValue = getModeValue('method_mode');
            const isSeasonal = v !== 'none';
            const showGamma = methodValue === 'manual-components' && isSeasonal;
            return [isSeasonal, showGamma];
        }
        function showTrendDependents(v){
            const methodValue = getModeValue('method_mode');
            return [methodValue === 'manual-components' && v === 'linear'];
        }
        function showConfidence(v){
            return [v === 'historical'];
        }
        function showHoldoutPct(v){
            return [v === 'holdout'];
        }
        function showMethodDependents(v){
            const trendValue = getModeValue('trend_mode');
            const seasonalityValue = getModeValue('seasonality_mode');
            const isManual = v === 'manual-components';
            return [
                isManual,
                isManual,
                isManual,
                isManual && trendValue === 'linear',
                isManual,
                isManual && seasonalityValue !== 'none',
                isManual && seasonalityValue !== 'none'
            ];
        }
        """,
        'tags': 'business, forecasting, decomposition, holt, holt-winters, time series',
    }


def forecast(
    historical_data: qtbl = {
        'columns': ['Period', 'Value'],
        'data': [
            ['2025-01', 125],
            ['2025-02', 138],
            ['2025-03', 151],
            ['2025-04', 149],
            ['2025-05', 162],
            ['2025-06', 171],
            ['2025-07', 176],
            ['2025-08', 180],
            ['2025-09', 188],
            ['2025-10', 192],
            ['2025-11', 201],
            ['2025-12', 210],
        ],
    },
    forecast_periods: int = 12,
    method_mode='automatic',
    level_mode='changing',
    alpha: float = 0.2,
    trend_mode='linear',
    beta: float = 0.2,
    seasonality_mode='none',
    gamma: float = 0.2,
    random_mode='historical',
    seasonal_period: int = 12,
    confidence_level: float = 95.0,
    validation_mode='holdout',
    holdout_percent: float = 20.0,
):
    periods, values = _extract_series(historical_data)
    n = len(values)

    if forecast_periods < 1:
        raise Exception('Forecast periods must be at least 1')
    if forecast_periods > 120:
        raise Exception('Forecast periods cannot exceed 120 in phase 1')

    if seasonal_period < 2:
        raise Exception('Seasonal period must be at least 2')

    if random_mode == 'historical' and not (50.0 <= confidence_level <= 99.9):
        raise Exception('Confidence level must be between 50 and 99.9')

    if validation_mode == 'holdout' and not (5.0 <= holdout_percent <= 50.0):
        raise Exception('Holdout split (%) must be between 5 and 50')

    desired_holdout_rows = 0
    if validation_mode == 'holdout':
        desired_holdout_rows = max(1, int(round(n * holdout_percent / 100.0)))

    auto_selection_basis = 'not-applicable'
    auto_selection_table = None
    if method_mode == 'automatic':
        model_key, model_name, auto_selection_basis, auto_diagnostics = _select_model_automatic(
            values,
            seasonal_period,
            holdout_rows=desired_holdout_rows,
        )
        auto_selection_table = _build_model_selection_table(auto_diagnostics, model_key, auto_selection_basis)
    else:
        model_key, model_name = _model_key(level_mode, trend_mode, seasonality_mode)

    selected_level_mode, selected_trend_mode, selected_seasonality_mode = _model_components(model_key)
    _validate_inputs(values, model_key, seasonal_period)
    manual_params = _manual_params(method_mode, model_key, alpha, beta, gamma)

    holdout_rows = 0
    validation_note = 'In-sample'

    if validation_mode == 'holdout':
        holdout_rows = max(1, int(round(n * holdout_percent / 100.0)))
        min_required_train = _required_min_obs(model_key, seasonal_period)
        if n - holdout_rows < min_required_train:
            holdout_rows = 0
            validation_note = 'In-sample (holdout skipped: not enough rows)'
        else:
            validation_note = 'Holdout'

    if holdout_rows > 0:
        train_values = values[:-holdout_rows]
        test_values = values[-holdout_rows:]
        fit_val, val_forecast = _fit_and_forecast(
            train_values,
            model_key,
            holdout_rows,
            seasonal_period,
            manual_params=manual_params,
        )
        accuracy_table = _build_accuracy(
            test_values,
            val_forecast,
            validation_note,
            len(train_values),
            len(test_values),
        )
    else:
        fit_val, val_forecast = _fit_and_forecast(
            values,
            model_key,
            len(values),
            seasonal_period,
            manual_params=manual_params,
        )
        accuracy_table = _build_accuracy(
            values,
            fit_val['fitted'],
            validation_note,
            len(values),
            len(values),
        )

    fit_full, point_forecast = _fit_and_forecast(
        values,
        model_key,
        forecast_periods,
        seasonal_period,
        manual_params=manual_params,
    )

    residuals = fit_full['residuals']
    sigma = None
    if random_mode == 'historical':
        squared = [r * r for r in residuals]
        if len(squared) > 1:
            sigma = sqrt(sum(squared) / max(1, len(squared) - 1))

    forecast_table = _build_forecast_table(
        point_forecast,
        confidence_level,
        sigma,
        random_mode,
        model_key,
        fit_full.get('params', {}),
    )
    decomposition_table = _build_decomposition_table(periods, values, fit_full)

    params = fit_full.get('params', {})
    trend_slope = fit_full['trend'][-1] if fit_full['trend'] else 0.0

    summary_rows = [
        ['Model family', model_name],
        ['Selected level', selected_level_mode],
        ['Selected trend', selected_trend_mode],
        ['Selected seasonality', selected_seasonality_mode],
        ['Observations', len(values)],
        ['Seasonal period', seasonal_period if selected_seasonality_mode != 'none' else 'Not used'],
        ['Method mode', method_mode],
        ['Auto selection basis', auto_selection_basis if method_mode == 'automatic' else 'manual-components'],
        ['Random mode', random_mode],
        ['Confidence level (%)', confidence_level if random_mode == 'historical' else 'Not used'],
        ['Residual std dev', _safe_round(sigma) if sigma is not None else 'Not available'],
        ['Trend slope (last)', _safe_round(trend_slope)],
    ]

    for p_name, p_val in params.items():
        summary_rows.append([f'Parameter {p_name}', _safe_round(p_val)])

    summary_table = _qtbl(['Metric', 'Value'], summary_rows)
    primary_chart = _build_primary_chart(
        periods,
        values,
        fit_full,
        point_forecast,
        random_mode,
        confidence_level,
        sigma,
        model_key,
    )

    result = {
        'Forecast table': forecast_table,
        'Forecast chart': primary_chart,
        'Forecast chart note': qhtml(
            '<small class="text-muted">'
            'Chart axis labels use index markers: '
            '<b>P1..Pn</b> for historical periods and <b>F1..Fm</b> for forecast periods.'
            '</small>'
        ),
        'Decomposition': decomposition_table,
        'Model summary': summary_table,
        'Forecast accuracy': accuracy_table,
    }

    if auto_selection_table is not None:
        result['Model selection diagnostics'] = auto_selection_table
        result['Model selection note'] = qhtml(
            '<small class="text-muted">'
            'Lower RMSE indicates better fit. Automatic mode prefers <b>Holdout RMSE</b> when available '
            'and falls back to <b>In-Sample RMSE</b> if holdout scoring is not feasible for all candidates.'
            '</small>'
        )

    return result
