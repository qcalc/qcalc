# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import pandas as pd
import numpy as np
from qcore import qchar, qtable, QChart, as_qtable, qhtml, qurl
from qutil import css2ints, css2floats, QThread, demo_url
import mplfinance as mpf
from calc import require_columns


def stock_chart__info():
    return {
        'title': 'Stock Candlestick, OHLC, and Other Overlay Charts',
        'desc': 'Plot OHLC stock data as a candlestick, OHLC, line, Renko, Point & Figure, or Heikin-Ashi chart with optional volume and moving averages',
        'tags': 'stock, candlestick, ohlc, technical analysis, indicators, renko, point and figure, heikin-ashi',
        'proper': 'RSI, EMA, PSAR, MACD, ATR, CCI, OBV',
        'layout': 'lr',
        'interactive': True,
        'input_columns': 1,
        'input_blocks': [
            {
                'column': 1,
                'tabs': [
                    {
                        'title': 'Data',
                        'fields': ['csv_url', 'load_csv', 'data', 'show_mapping'],
                    },
                    {
                        'title': 'Mapping',
                        'fields': [
                            'date_column_name',
                            'open_column_name',
                            'high_column_name',
                            'low_column_name',
                            'close_column_name',
                            'volume_column_name',
                        ],
                    },
                    {
                        'title': 'Chart',
                        'fields': [
                            'title',
                            'chart_type',
                            'style',
                            'timeframe',
                            'chart_width',
                            'chart_height',
                            'show_nontrading',
                            'log_scale',
                        ],
                    },
                    {
                        'title': 'Overlays',
                        'fields': [
                            'show_volume',
                            'show_moving_average',
                            'show_ema',
                            'show_bollinger',
                            'show_donchian',
                            'show_psar',
                            'show_rsi',
                            'show_macd',
                            'show_atr',
                            'show_cci',
                            'show_williams_r',
                            'show_obv',
                        ],
                    },
                    {
                        'title': 'Markers',
                        'fields': [
                            'marker_symbol_table',
                        ],
                    },
                    {
                        'title': 'Moving Average',
                        'fields': [
                            'moving_average_periods',
                            'show_ma_cross_markers',
                        ],
                    },
                    {
                        'title': 'EMA',
                        'fields': [
                            'ema_periods',
                            'show_ema_cross_markers',
                        ],
                    },
                    {
                        'title': 'Bollinger',
                        'fields': [
                            'bollinger_period',
                            'bollinger_std',
                            'show_bollinger_band_markers',
                        ],
                    },
                    {
                        'title': 'Donchian',
                        'fields': [
                            'donchian_period',
                            'show_donchian_breakout_markers',
                        ],
                    },
                    {
                        'title': 'Parabolic SAR',
                        'fields': [
                            'psar_af_step',
                            'psar_af_max',
                            'show_psar_flip_markers',
                        ],
                    },
                    {
                        'title': 'RSI',
                        'fields': [
                            'rsi_period',
                            'rsi_overbought',
                            'rsi_oversold',
                            'show_rsi_cross_markers',
                        ],
                    },
                    {
                        'title': 'MACD',
                        'fields': [
                            'macd_fast_period',
                            'macd_slow_period',
                            'macd_signal_period',
                            'show_macd_cross_markers',
                        ],
                    },
                    {
                        'title': 'ATR',
                        'fields': [
                            'atr_period',
                            'atr_mav_period',
                            'show_atr_cross_markers',
                        ],
                    },
                    {
                        'title': 'CCI',
                        'fields': [
                            'cci_period',
                            'show_cci_threshold_markers',
                        ],
                    },
                    {
                        'title': 'Williams %R',
                        'fields': [
                            'williams_r_period',
                            'show_williams_r_threshold_markers',
                        ],
                    },
                    {
                        'title': 'OBV',
                        'fields': [
                            'obv_smoothing_period',
                            'show_obv_cross_markers',
                        ],
                    },
                    {
                        'title': 'Levels',
                        'fields': [
                            'support_levels',
                            'resistance_levels',
                        ],
                    },
                    {
                        'title': 'Renko / PnF',
                        'fields': [
                            'renko_brick_size',
                            'pnf_box_size',
                            'pnf_reversal',
                        ],
                    },
                ],
            },
        ],
        'showhide': {
            'show_mapping': {
                'fields': [
                    'date_column_name',
                    'open_column_name',
                    'high_column_name',
                    'low_column_name',
                    'close_column_name',
                    'volume_column_name',
                ],
                'callback': 'toggle_mapping_fields',
            },
            'show_moving_average': {
                'fields': ['moving_average_periods', 'show_ma_cross_markers'],
                'callback': 'toggle_moving_average_fields',
            },
            'show_ema': {
                'fields': ['ema_periods', 'show_ema_cross_markers'],
                'callback': 'toggle_ema_fields',
            },
            'show_bollinger': {
                'fields': ['bollinger_period', 'bollinger_std', 'show_bollinger_band_markers'],
                'callback': 'toggle_bollinger_fields',
            },
            'show_donchian': {
                'fields': ['donchian_period', 'show_donchian_breakout_markers'],
                'callback': 'toggle_donchian_fields',
            },
            'show_psar': {
                'fields': ['psar_af_step', 'psar_af_max', 'show_psar_flip_markers'],
                'callback': 'toggle_psar_fields',
            },
            'show_rsi': {
                'fields': ['rsi_period', 'rsi_overbought', 'rsi_oversold', 'show_rsi_cross_markers'],
                'callback': 'toggle_rsi_fields',
            },
            'show_macd': {
                'fields': ['macd_fast_period', 'macd_slow_period', 'macd_signal_period', 'show_macd_cross_markers'],
                'callback': 'toggle_macd_fields',
            },
            'show_atr': {
                'fields': ['atr_period', 'atr_mav_period', 'show_atr_cross_markers'],
                'callback': 'toggle_atr_fields',
            },
            'show_cci': {
                'fields': ['cci_period', 'show_cci_threshold_markers'],
                'callback': 'toggle_cci_fields',
            },
            'show_williams_r': {
                'fields': ['williams_r_period', 'show_williams_r_threshold_markers'],
                'callback': 'toggle_williams_r_fields',
            },
            'show_obv': {
                'fields': ['obv_smoothing_period', 'show_obv_cross_markers'],
                'callback': 'toggle_obv_fields',
            },
            'chart_type': {
                'fields': ['renko_brick_size', 'pnf_box_size', 'pnf_reversal'],
                'callback': 'toggle_renko_pnf_fields',
            },
        },
        'script': '''
        function toggle_moving_average_fields(v){
            return [!!v, !!v];
        }
        function toggle_mapping_fields(v){
            return [!!v, !!v, !!v, !!v, !!v, !!v];
        }
        function toggle_ema_fields(v){
            return [!!v, !!v];
        }
        function toggle_bollinger_fields(v){
            return [!!v, !!v, !!v];
        }
        function toggle_donchian_fields(v){
            return [!!v, !!v];
        }
        function toggle_psar_fields(v){
            return [!!v, !!v, !!v];
        }
        function toggle_rsi_fields(v){
            return [!!v, !!v, !!v, !!v];
        }
        function toggle_macd_fields(v){
            return [!!v, !!v, !!v, !!v];
        }
        function toggle_atr_fields(v){
            return [!!v, !!v, !!v];
        }
        function toggle_cci_fields(v){
            return [!!v, !!v];
        }
        function toggle_williams_r_fields(v){
            return [!!v, !!v];
        }
        function toggle_obv_fields(v){
            return [!!v, !!v];
        }
        function toggle_renko_pnf_fields(v){
            return [v === 'renko', v === 'pnf', v === 'pnf'];
        }
        $(document).ready(function() {
            load_button_id = QCALC_TOK_ID_PREFIX + getCid() + '_@load_csv';
            $("#"+load_button_id).on("click", function() {
                cid = getCidOf($(this));
                updateExtra(cid, {
                    "cmd":"load", "from":"@data", "to":"@data",
                    "delimiter": ",", "quoting": "1", "url":"@csv_url"
                });
                qcalc_FullFormSubmit(cid);
            });
        });
        ''',
        'schema': {
            'data': {
                'help_text': 'Input OHLCV table with columns Date, Open, High, Low, Close, and optional Volume.',
            },
            'csv_url': {
                'help_text': 'CSV URL source to load into the Data table.',
            },
            'show_mapping': {
                'help_text': 'Show/hide custom column mapping controls for Date/OHLC/Volume fields.',
            },
            'date_column_name': {
                'help_text': 'Column name for Date values in input data.',
            },
            'open_column_name': {
                'help_text': 'Column name for Open price in input data.',
            },
            'high_column_name': {
                'help_text': 'Column name for High price in input data.',
            },
            'low_column_name': {
                'help_text': 'Column name for Low price in input data.',
            },
            'close_column_name': {
                'help_text': 'Column name for Close price in input data.',
            },
            'volume_column_name': {
                'help_text': 'Column name for Volume in input data (needed for volume/OBV overlays).',
            },
            'title': {
                'help_text': 'Chart title shown above the plotted figure.',
            },
            'chart_type': {
                'type': 'choice',
                'choices': ['candle', 'ohlc', 'line', 'renko', 'pnf', 'heikin'],
                'help_text': 'Chart mode to render. Renko/PnF ignore standard indicator overlays and show a note.',
            },
            'style': {
                'type': 'choice',
                'choices': ['yahoo', 'charles', 'classic', 'binance', 'mike'],
                'help_text': 'Visual style preset for colors and theme.',
            },
            'timeframe': {
                'type': 'choice',
                'choices': ['raw', '5m', '15m', '1h', '4h', '1d', '1w', '1mo'],
                'help_text': 'Resample frequency before plotting. Use raw to keep input frequency unchanged.',
            },
            'chart_width': {
                'type': 'integer',
                'help_text': 'Chart width in pixels. Defaults to your current chart width preference.',
            },
            'chart_height': {
                'type': 'integer',
                'help_text': 'Chart height in pixels. Defaults to your current chart height preference.',
            },
            'show_nontrading': {
                'help_text': 'When enabled, display non-trading gaps in the time axis.',
            },
            'log_scale': {
                'help_text': 'Use logarithmic price scale on the primary Y axis.',
            },
            'show_volume': {
                'help_text': 'Show volume bars in a lower panel.',
            },
            'show_moving_average': {
                'help_text': 'Enable simple moving-average overlays defined by Moving Average Periods.',
            },
            'moving_average_periods': {
                'help_text': 'Comma-separated SMA periods, e.g. 5, 10, 20.',
            },
            'show_ema': {
                'help_text': 'Enable exponential moving-average overlays defined by EMA Periods.',
            },
            'ema_periods': {
                'help_text': 'Comma-separated EMA periods, e.g. 8, 21, 55.',
            },
            'show_ema_cross_markers': {
                'help_text': 'Enable EMA-crossover buy/sell markers using the first two values from EMA Periods.',
            },
            'show_bollinger': {
                'help_text': 'Enable Bollinger Bands overlay.',
            },
            'bollinger_period': {
                'help_text': 'Rolling lookback period for Bollinger middle band.',
            },
            'bollinger_std': {
                'help_text': 'Standard-deviation multiplier for Bollinger upper/lower bands.',
            },
            'show_bollinger_band_markers': {
                'help_text': 'Enable Bollinger re-entry markers (buy above lower band, sell below upper band).',
            },
            'show_donchian': {
                'help_text': 'Enable Donchian channel overlay.',
            },
            'donchian_period': {
                'help_text': 'Lookback period for Donchian channel high/low bands.',
            },
            'show_psar': {
                'help_text': 'Enable Parabolic SAR dot overlay on the price panel.',
            },
            'psar_af_step': {
                'help_text': 'Parabolic SAR acceleration-factor step increment (AF step).',
            },
            'psar_af_max': {
                'help_text': 'Parabolic SAR maximum acceleration factor (AF max).',
            },
            'show_psar_flip_markers': {
                'help_text': 'Enable markers when Parabolic SAR trend flips between bullish and bearish.',
            },
            'show_rsi': {
                'help_text': 'Enable RSI indicator in a separate lower panel.',
            },
            'rsi_period': {
                'help_text': 'RSI lookback period.',
            },
            'rsi_overbought': {
                'help_text': 'RSI overbought reference level (commonly 70).',
            },
            'rsi_oversold': {
                'help_text': 'RSI oversold reference level (commonly 30).',
            },
            'show_macd': {
                'help_text': 'Enable MACD indicator panel with line, signal, and histogram.',
            },
            'macd_fast_period': {
                'help_text': 'Fast EMA period used in MACD.',
            },
            'macd_slow_period': {
                'help_text': 'Slow EMA period used in MACD (must be greater than fast period).',
            },
            'macd_signal_period': {
                'help_text': 'Signal EMA period for MACD line smoothing.',
            },
            'show_macd_cross_markers': {
                'help_text': 'Enable markers for MACD line crossing above/below MACD signal line.',
            },
            'show_atr': {
                'help_text': 'Enable ATR volatility indicator in a lower panel.',
            },
            'atr_period': {
                'help_text': 'ATR lookback period.',
            },
            'atr_mav_period': {
                'help_text': 'ATR moving-average period used for ATR markers and ATR MAV panel line.',
            },
            'show_atr_cross_markers': {
                'help_text': 'Enable markers for ATR crossing above/below its ATR moving average.',
            },
            'show_cci': {
                'help_text': 'Enable Commodity Channel Index (CCI) panel.',
            },
            'cci_period': {
                'help_text': 'CCI lookback period.',
            },
            'show_cci_threshold_markers': {
                'help_text': 'Enable markers for CCI threshold crosses (-100 upward for buy, +100 downward for sell).',
            },
            'show_williams_r': {
                'help_text': 'Enable Williams %R momentum panel.',
            },
            'williams_r_period': {
                'help_text': 'Williams %R lookback period.',
            },
            'show_williams_r_threshold_markers': {
                'help_text': 'Enable markers for Williams %R threshold crosses (-80 upward for buy, -20 downward for sell).',
            },
            'show_obv': {
                'help_text': 'Enable On-Balance Volume panel (requires Volume column).',
            },
            'obv_smoothing_period': {
                'help_text': 'Optional OBV smoothing period. Use 1 for raw OBV.',
            },
            'show_obv_cross_markers': {
                'help_text': 'Enable markers for OBV crossing above/below its smoothing average.',
            },
            'show_ma_cross_markers': {
                'help_text': 'Enable MA-crossover buy/sell markers using the first two values from Moving Average Periods.',
            },
            'show_rsi_cross_markers': {
                'help_text': 'Enable RSI-based buy/sell markers using RSI period with oversold/overbought levels.',
            },
            'show_donchian_breakout_markers': {
                'help_text': 'Enable Donchian breakout buy/sell markers using Donchian period.',
            },
            'marker_symbol_table': {
                'help_text': 'Per-chart marker symbols table with columns: chart, buy, sell. Allowed symbols: ^, v, o, *, +, X, s, D.',
            },
            'support_levels': {
                'help_text': 'Comma-separated horizontal support price levels, e.g. 410, 395.',
            },
            'resistance_levels': {
                'help_text': 'Comma-separated horizontal resistance price levels, e.g. 450, 470.',
            },
            'renko_brick_size': {
                'help_text': 'Renko brick size. Use a positive number or "atr".',
            },
            'pnf_box_size': {
                'help_text': 'Point & Figure box size. Use a positive number or "atr".',
            },
            'pnf_reversal': {
                'help_text': 'Point & Figure reversal size in boxes (positive integer).',
            },
        },
    }



def _to_heikin_ashi(ohlc: pd.DataFrame) -> pd.DataFrame:
    ha = pd.DataFrame(index=ohlc.index)
    ha_close = (ohlc['Open'] + ohlc['High'] + ohlc['Low'] + ohlc['Close']) / 4.0

    ha_open = np.empty(len(ohlc), dtype=float)
    open_vals = ohlc['Open'].to_numpy(dtype=float)
    close_vals = ohlc['Close'].to_numpy(dtype=float)
    ha_close_vals = ha_close.to_numpy(dtype=float)

    ha_open[0] = (open_vals[0] + close_vals[0]) / 2.0
    for i in range(1, len(ohlc)):
        ha_open[i] = (ha_open[i - 1] + ha_close_vals[i - 1]) / 2.0

    ha['Open'] = ha_open
    ha['Close'] = ha_close_vals
    ha['High'] = np.maximum.reduce([ohlc['High'].to_numpy(dtype=float), ha['Open'].to_numpy(), ha['Close'].to_numpy()])
    ha['Low'] = np.minimum.reduce([ohlc['Low'].to_numpy(dtype=float), ha['Open'].to_numpy(), ha['Close'].to_numpy()])

    if 'Volume' in ohlc.columns:
        ha['Volume'] = ohlc['Volume'].to_numpy(dtype=float)
    return ha


def _parse_box_size(value, name):
    sval = str(value).strip().lower()
    if sval == 'atr':
        return 'atr'
    try:
        fval = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f'{name} must be a positive number or "atr"') from exc
    if fval <= 0:
        raise ValueError(f'{name} must be greater than 0')
    return fval


def _compute_ma_cross_markers(plot_data: pd.DataFrame, moving_average_periods):
    marker_ma_periods = tuple(css2ints(moving_average_periods)) if str(moving_average_periods).strip() else tuple()
    marker_ma_periods = tuple(period for period in marker_ma_periods if period > 0)
    marker_ma_periods = tuple(sorted(set(marker_ma_periods)))
    if len(marker_ma_periods) < 2:
        return None, None, 'MA Cross Markers (need at least two MA periods)'

    marker_ma_fast_period, marker_ma_slow_period = marker_ma_periods[0], marker_ma_periods[1]
    if marker_ma_slow_period > len(plot_data.index):
        return None, None, 'MA Cross Markers (insufficient data)'

    fast_ma = plot_data['Close'].rolling(window=marker_ma_fast_period, min_periods=marker_ma_fast_period).mean()
    slow_ma = plot_data['Close'].rolling(window=marker_ma_slow_period, min_periods=marker_ma_slow_period).mean()
    cross_up = (fast_ma > slow_ma) & (fast_ma.shift(1) <= slow_ma.shift(1))
    cross_dn = (fast_ma < slow_ma) & (fast_ma.shift(1) >= slow_ma.shift(1))
    buy_markers = pd.Series(np.nan, index=plot_data.index, dtype=float)
    sell_markers = pd.Series(np.nan, index=plot_data.index, dtype=float)
    buy_markers.loc[cross_up] = plot_data['Low'][cross_up] * 0.995
    sell_markers.loc[cross_dn] = plot_data['High'][cross_dn] * 1.005
    return buy_markers, sell_markers, None


def _compute_ema_cross_markers(plot_data: pd.DataFrame, ema_periods):
    marker_ema_periods = tuple(css2ints(ema_periods)) if str(ema_periods).strip() else tuple()
    marker_ema_periods = tuple(period for period in marker_ema_periods if period > 0)
    marker_ema_periods = tuple(sorted(set(marker_ema_periods)))
    if len(marker_ema_periods) < 2:
        return None, None, 'EMA Cross Markers (need at least two EMA periods)'

    marker_ema_fast_period, marker_ema_slow_period = marker_ema_periods[0], marker_ema_periods[1]
    if marker_ema_slow_period > len(plot_data.index):
        return None, None, 'EMA Cross Markers (insufficient data)'

    fast_ema = plot_data['Close'].ewm(span=marker_ema_fast_period, adjust=False).mean()
    slow_ema = plot_data['Close'].ewm(span=marker_ema_slow_period, adjust=False).mean()
    cross_up = (fast_ema > slow_ema) & (fast_ema.shift(1) <= slow_ema.shift(1))
    cross_dn = (fast_ema < slow_ema) & (fast_ema.shift(1) >= slow_ema.shift(1))
    buy_markers = pd.Series(np.nan, index=plot_data.index, dtype=float)
    sell_markers = pd.Series(np.nan, index=plot_data.index, dtype=float)
    buy_markers.loc[cross_up] = plot_data['Low'][cross_up] * 0.995
    sell_markers.loc[cross_dn] = plot_data['High'][cross_dn] * 1.005
    return buy_markers, sell_markers, None


def _compute_rsi_cross_markers(plot_data: pd.DataFrame, rsi_period, rsi_oversold, rsi_overbought):
    try:
        marker_rsi_period = int(rsi_period)
    except (TypeError, ValueError) as exc:
        raise ValueError('RSI period must be an integer greater than 1') from exc
    if marker_rsi_period <= 1:
        raise ValueError('RSI period must be an integer greater than 1')
    try:
        marker_rsi_buy_level = float(rsi_oversold)
        marker_rsi_sell_level = float(rsi_overbought)
    except (TypeError, ValueError) as exc:
        raise ValueError('RSI overbought/oversold levels must be numeric values') from exc
    if not (0 <= marker_rsi_buy_level <= 100 and 0 <= marker_rsi_sell_level <= 100):
        raise ValueError('RSI overbought/oversold levels must be between 0 and 100')
    if marker_rsi_buy_level >= marker_rsi_sell_level:
        raise ValueError('RSI oversold must be lower than RSI overbought')
    if marker_rsi_period > len(plot_data.index):
        return None, None, 'RSI Cross Markers (insufficient data)'

    close = plot_data['Close']
    delta = close.diff()
    gains = delta.clip(lower=0)
    losses = -delta.clip(upper=0)
    avg_gain = gains.rolling(window=marker_rsi_period, min_periods=marker_rsi_period).mean()
    avg_loss = losses.rolling(window=marker_rsi_period, min_periods=marker_rsi_period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    marker_rsi = 100 - (100 / (1 + rs))
    marker_rsi = marker_rsi.where(avg_loss != 0, 100.0)
    marker_rsi = marker_rsi.where(~((avg_gain == 0) & (avg_loss == 0)), 50.0)
    cross_up = (marker_rsi > marker_rsi_buy_level) & (marker_rsi.shift(1) <= marker_rsi_buy_level)
    cross_dn = (marker_rsi < marker_rsi_sell_level) & (marker_rsi.shift(1) >= marker_rsi_sell_level)
    buy_markers = pd.Series(np.nan, index=plot_data.index, dtype=float)
    sell_markers = pd.Series(np.nan, index=plot_data.index, dtype=float)
    buy_markers.loc[cross_up] = plot_data['Low'][cross_up] * 0.995
    sell_markers.loc[cross_dn] = plot_data['High'][cross_dn] * 1.005
    return buy_markers, sell_markers, None


def _compute_donchian_breakout_markers(plot_data: pd.DataFrame, donchian_period):
    try:
        marker_donchian_period = int(donchian_period)
    except (TypeError, ValueError) as exc:
        raise ValueError('Donchian period must be an integer greater than 1') from exc
    if marker_donchian_period <= 1:
        raise ValueError('Donchian period must be an integer greater than 1')
    if marker_donchian_period > len(plot_data.index):
        return None, None, 'Donchian Breakout Markers (insufficient data)'

    upper = plot_data['High'].rolling(window=marker_donchian_period, min_periods=marker_donchian_period).max().shift(1)
    lower = plot_data['Low'].rolling(window=marker_donchian_period, min_periods=marker_donchian_period).min().shift(1)
    breakout_up = (plot_data['Close'] > upper) & upper.notna()
    breakout_dn = (plot_data['Close'] < lower) & lower.notna()
    buy_markers = pd.Series(np.nan, index=plot_data.index, dtype=float)
    sell_markers = pd.Series(np.nan, index=plot_data.index, dtype=float)
    buy_markers.loc[breakout_up] = plot_data['Low'][breakout_up] * 0.995
    sell_markers.loc[breakout_dn] = plot_data['High'][breakout_dn] * 1.005
    return buy_markers, sell_markers, None


def _compute_bollinger_reentry_markers(plot_data: pd.DataFrame, bollinger_period, bollinger_std):
    try:
        marker_period = int(bollinger_period)
    except (TypeError, ValueError) as exc:
        raise ValueError('Bollinger period must be an integer greater than 1') from exc
    if marker_period <= 1:
        raise ValueError('Bollinger period must be an integer greater than 1')
    if marker_period > len(plot_data.index):
        return None, None, 'Bollinger Band Markers (insufficient data)'
    try:
        marker_std = float(bollinger_std)
    except (TypeError, ValueError) as exc:
        raise ValueError('Bollinger std must be a positive number') from exc
    if marker_std <= 0:
        raise ValueError('Bollinger std must be a positive number')

    bb_mid = plot_data['Close'].rolling(window=marker_period, min_periods=marker_period).mean()
    bb_std = plot_data['Close'].rolling(window=marker_period, min_periods=marker_period).std(ddof=0)
    bb_upper = bb_mid + (marker_std * bb_std)
    bb_lower = bb_mid - (marker_std * bb_std)
    cross_up_lower = (plot_data['Close'] > bb_lower) & (plot_data['Close'].shift(1) <= bb_lower.shift(1))
    cross_dn_upper = (plot_data['Close'] < bb_upper) & (plot_data['Close'].shift(1) >= bb_upper.shift(1))
    buy_markers = pd.Series(np.nan, index=plot_data.index, dtype=float)
    sell_markers = pd.Series(np.nan, index=plot_data.index, dtype=float)
    buy_markers.loc[cross_up_lower] = plot_data['Low'][cross_up_lower] * 0.995
    sell_markers.loc[cross_dn_upper] = plot_data['High'][cross_dn_upper] * 1.005
    return buy_markers, sell_markers, None


def _compute_psar_flip_markers(plot_data: pd.DataFrame, psar_af_step, psar_af_max):
    try:
        af_step = float(psar_af_step)
        af_max = float(psar_af_max)
    except (TypeError, ValueError) as exc:
        raise ValueError('Parabolic SAR AF step/max must be numeric values') from exc
    if af_step <= 0 or af_max <= 0:
        raise ValueError('Parabolic SAR AF step/max must be greater than 0')
    if af_step > af_max:
        raise ValueError('Parabolic SAR AF step must be less than or equal to AF max')
    if len(plot_data.index) < 2:
        return None, None, 'PSAR Flip Markers (insufficient data)'

    high = plot_data['High'].to_numpy(dtype=float)
    low = plot_data['Low'].to_numpy(dtype=float)
    close = plot_data['Close'].to_numpy(dtype=float)
    bull = bool(close[1] >= close[0])
    af = af_step
    ep = high[0] if bull else low[0]
    psar_prev = low[0] if bull else high[0]
    flip_up = np.zeros(len(plot_data), dtype=bool)
    flip_dn = np.zeros(len(plot_data), dtype=bool)

    for i in range(1, len(plot_data)):
        psar_i = psar_prev + af * (ep - psar_prev)
        if bull:
            if i >= 2:
                psar_i = min(psar_i, low[i - 1], low[i - 2])
            else:
                psar_i = min(psar_i, low[i - 1])
            if low[i] < psar_i:
                bull = False
                flip_dn[i] = True
                psar_i = ep
                ep = low[i]
                af = af_step
            else:
                if high[i] > ep:
                    ep = high[i]
                    af = min(af_max, af + af_step)
        else:
            if i >= 2:
                psar_i = max(psar_i, high[i - 1], high[i - 2])
            else:
                psar_i = max(psar_i, high[i - 1])
            if high[i] > psar_i:
                bull = True
                flip_up[i] = True
                psar_i = ep
                ep = high[i]
                af = af_step
            else:
                if low[i] < ep:
                    ep = low[i]
                    af = min(af_max, af + af_step)
        psar_prev = psar_i

    buy_markers = pd.Series(np.nan, index=plot_data.index, dtype=float)
    sell_markers = pd.Series(np.nan, index=plot_data.index, dtype=float)
    buy_markers.loc[flip_up] = plot_data['Low'][flip_up] * 0.995
    sell_markers.loc[flip_dn] = plot_data['High'][flip_dn] * 1.005
    return buy_markers, sell_markers, None


def _compute_macd_cross_markers(plot_data: pd.DataFrame, macd_fast_period, macd_slow_period, macd_signal_period):
    try:
        fast_period = int(macd_fast_period)
        slow_period = int(macd_slow_period)
        signal_period = int(macd_signal_period)
    except (TypeError, ValueError) as exc:
        raise ValueError('MACD periods must be integers') from exc
    if fast_period <= 0 or slow_period <= 0 or signal_period <= 0:
        raise ValueError('MACD periods must be positive integers')
    if fast_period >= slow_period:
        raise ValueError('MACD fast period must be lower than MACD slow period')
    if slow_period > len(plot_data.index):
        return None, None, 'MACD Cross Markers (insufficient data)'

    ema_fast = plot_data['Close'].ewm(span=fast_period, adjust=False).mean()
    ema_slow = plot_data['Close'].ewm(span=slow_period, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    macd_signal = macd_line.ewm(span=signal_period, adjust=False).mean()
    cross_up = (macd_line > macd_signal) & (macd_line.shift(1) <= macd_signal.shift(1))
    cross_dn = (macd_line < macd_signal) & (macd_line.shift(1) >= macd_signal.shift(1))
    buy_markers = pd.Series(np.nan, index=plot_data.index, dtype=float)
    sell_markers = pd.Series(np.nan, index=plot_data.index, dtype=float)
    buy_markers.loc[cross_up] = plot_data['Low'][cross_up] * 0.995
    sell_markers.loc[cross_dn] = plot_data['High'][cross_dn] * 1.005
    return buy_markers, sell_markers, None


def _compute_cci_threshold_markers(plot_data: pd.DataFrame, cci_period):
    try:
        marker_period = int(cci_period)
    except (TypeError, ValueError) as exc:
        raise ValueError('CCI period must be an integer greater than 1') from exc
    if marker_period <= 1:
        raise ValueError('CCI period must be an integer greater than 1')
    if marker_period > len(plot_data.index):
        return None, None, 'CCI Threshold Markers (insufficient data)'

    typical_price = (plot_data['High'] + plot_data['Low'] + plot_data['Close']) / 3.0
    cci_ma = typical_price.rolling(window=marker_period, min_periods=marker_period).mean()
    mad = (typical_price - cci_ma).abs().rolling(window=marker_period, min_periods=marker_period).mean()
    cci = (typical_price - cci_ma) / (0.015 * mad.replace(0, np.nan))
    cross_up = (cci > -100.0) & (cci.shift(1) <= -100.0)
    cross_dn = (cci < 100.0) & (cci.shift(1) >= 100.0)
    buy_markers = pd.Series(np.nan, index=plot_data.index, dtype=float)
    sell_markers = pd.Series(np.nan, index=plot_data.index, dtype=float)
    buy_markers.loc[cross_up] = plot_data['Low'][cross_up] * 0.995
    sell_markers.loc[cross_dn] = plot_data['High'][cross_dn] * 1.005
    return buy_markers, sell_markers, None


def _compute_williams_r_threshold_markers(plot_data: pd.DataFrame, williams_r_period):
    try:
        marker_period = int(williams_r_period)
    except (TypeError, ValueError) as exc:
        raise ValueError('Williams %R period must be an integer greater than 1') from exc
    if marker_period <= 1:
        raise ValueError('Williams %R period must be an integer greater than 1')
    if marker_period > len(plot_data.index):
        return None, None, 'Williams %R Threshold Markers (insufficient data)'

    hh = plot_data['High'].rolling(window=marker_period, min_periods=marker_period).max()
    ll = plot_data['Low'].rolling(window=marker_period, min_periods=marker_period).min()
    denom = (hh - ll).replace(0, np.nan)
    wr = -100.0 * (hh - plot_data['Close']) / denom
    cross_up = (wr > -80.0) & (wr.shift(1) <= -80.0)
    cross_dn = (wr < -20.0) & (wr.shift(1) >= -20.0)
    buy_markers = pd.Series(np.nan, index=plot_data.index, dtype=float)
    sell_markers = pd.Series(np.nan, index=plot_data.index, dtype=float)
    buy_markers.loc[cross_up] = plot_data['Low'][cross_up] * 0.995
    sell_markers.loc[cross_dn] = plot_data['High'][cross_dn] * 1.005
    return buy_markers, sell_markers, None


def _compute_obv_cross_markers(plot_data: pd.DataFrame, obv_smoothing_period):
    try:
        marker_period = int(obv_smoothing_period)
    except (TypeError, ValueError) as exc:
        raise ValueError('OBV smoothing period must be an integer greater than 0') from exc
    if marker_period <= 0:
        raise ValueError('OBV smoothing period must be an integer greater than 0')
    if marker_period > len(plot_data.index):
        return None, None, 'OBV Cross Markers (insufficient data)'

    direction = np.sign(plot_data['Close'].diff().fillna(0.0))
    obv_raw = (direction * plot_data['Volume']).fillna(0.0).cumsum()
    obv_ma = obv_raw.rolling(window=marker_period, min_periods=marker_period).mean()
    cross_up = (obv_raw > obv_ma) & (obv_raw.shift(1) <= obv_ma.shift(1))
    cross_dn = (obv_raw < obv_ma) & (obv_raw.shift(1) >= obv_ma.shift(1))
    buy_markers = pd.Series(np.nan, index=plot_data.index, dtype=float)
    sell_markers = pd.Series(np.nan, index=plot_data.index, dtype=float)
    buy_markers.loc[cross_up] = plot_data['Low'][cross_up] * 0.995
    sell_markers.loc[cross_dn] = plot_data['High'][cross_dn] * 1.005
    return buy_markers, sell_markers, None


def _compute_atr_cross_markers(plot_data: pd.DataFrame, atr_period, atr_mav_period):
    try:
        marker_period = int(atr_period)
    except (TypeError, ValueError) as exc:
        raise ValueError('ATR period must be an integer greater than 1') from exc
    if marker_period <= 1:
        raise ValueError('ATR period must be an integer greater than 1')
    try:
        marker_mav_period = int(atr_mav_period)
    except (TypeError, ValueError) as exc:
        raise ValueError('ATR MAV period must be an integer greater than 0') from exc
    if marker_mav_period <= 0:
        raise ValueError('ATR MAV period must be an integer greater than 0')
    if marker_period > len(plot_data.index):
        return None, None, 'ATR Cross Markers (insufficient data)'
    if marker_mav_period > len(plot_data.index):
        return None, None, 'ATR Cross Markers (insufficient data)'

    high = plot_data['High']
    low = plot_data['Low']
    prev_close = plot_data['Close'].shift(1)
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = true_range.rolling(window=marker_period, min_periods=marker_period).mean()
    atr_ma = atr.rolling(window=marker_mav_period, min_periods=marker_mav_period).mean()
    cross_up = (atr > atr_ma) & (atr.shift(1) <= atr_ma.shift(1))
    cross_dn = (atr < atr_ma) & (atr.shift(1) >= atr_ma.shift(1))
    buy_markers = pd.Series(np.nan, index=plot_data.index, dtype=float)
    sell_markers = pd.Series(np.nan, index=plot_data.index, dtype=float)
    buy_markers.loc[cross_up] = plot_data['Low'][cross_up] * 0.995
    sell_markers.loc[cross_dn] = plot_data['High'][cross_dn] * 1.005
    return buy_markers, sell_markers, None


def _normalize_marker_symbol(symbol):
    sval = str(symbol).strip()
    # if len(sval) != 1:
    #     raise ValueError('Marker symbols must be a single character')
    allowed = {'^', 'v', 'o', '*', '+', 'X', 's', 'D'}
    if sval in allowed:
        return sval
    if sval =='**': return '^' # trick for eva() expression
    raise ValueError('Marker symbols must be one of: ^, v, o, *, +, X, s, D')


def _parse_marker_symbol_table(marker_symbol_table):
    df = as_qtable(marker_symbol_table).copy()
    required = {'chart', 'buy', 'sell'}
    cols = {str(c).strip().lower(): c for c in df.columns}
    if not required.issubset(set(cols.keys())):
        raise ValueError('Marker symbol table must include columns: chart, buy, sell')

    c_chart = cols['chart']
    c_buy = cols['buy']
    c_sell = cols['sell']

    symbol_map = {}
    for _, row in df.iterrows():
        chart_key = str(row[c_chart]).strip().upper()
        if not chart_key:
            continue
        buy_symbol = _normalize_marker_symbol(row[c_buy])
        sell_symbol = _normalize_marker_symbol(row[c_sell])
        symbol_map[chart_key] = (buy_symbol, sell_symbol)

    default_symbol_map = {
        'MA': ('^', 'v'),
        'EMA': ('D', 'D'),
        'RSI': ('o', 'o'),
        'DONCHIAN': ('*', '*'),
        'BOLLINGER': ('+', '+'),
        'PSAR': ('X', 'X'),
        'MACD': ('s', 's'),
        'ATR': ('D', 'D'),
        'CCI': ('^', 'v'),
        'WILLIAMS_R': ('o', 'o'),
        'OBV': ('s', 's'),
    }
    for chart_key, symbols in default_symbol_map.items():
        if chart_key not in symbol_map:
            symbol_map[chart_key] = symbols
    return symbol_map


def stock_chart(
    data: qtable = pd.DataFrame({
        'Date': ['2026-01-02', '2026-01-03', '2026-01-04', '2026-01-05', '2026-01-06', '2026-01-07', '2026-01-08'],
        'Open': [100, 101, 103, 102, 104, 103, 105],
        'High': [102, 104, 105, 106, 107, 108, 110],
        'Low': [99, 100, 101, 101, 102, 102, 103],
        'Close': [101, 103, 102, 104, 103, 105, 109],
        'Volume': [1200000, 1150000, 1400000, 1320000, 1275000, 1510000, 1890000],
    }),
    title='Stock Chart',
    csv_url: qurl = demo_url('stock-closing.csv'),
    load_csv: 'btn:0' = 'Load CSV',
    show_mapping=False,
    date_column_name: qchar = 'Date',
    open_column_name: qchar = 'Open',
    high_column_name: qchar = 'High',
    low_column_name: qchar = 'Low',
    close_column_name: qchar = 'Close',
    volume_column_name: qchar = 'Volume',
    chart_type='candle',
    style='yahoo',
    show_volume=True,
    chart_width=0,
    chart_height=0,
    show_moving_average=False,
    moving_average_periods: qchar = '5, 10',
    show_ema=False,
    ema_periods: qchar = '8, 21',
    timeframe='raw',
    show_nontrading=False,
    log_scale=False,
    show_bollinger=False,
    bollinger_period=20,
    bollinger_std=2.0,
    show_donchian=False,
    donchian_period=20,
    show_psar=False,
    psar_af_step=0.02,
    psar_af_max=0.20,
    show_rsi=False,
    rsi_period=14,
    rsi_overbought=70,
    rsi_oversold=30,
    show_macd=False,
    macd_fast_period=12,
    macd_slow_period=26,
    macd_signal_period=9,
    show_atr=False,
    atr_period=14,
    atr_mav_period=14,
    show_atr_cross_markers=False,
    show_cci=False,
    cci_period=20,
    show_williams_r=False,
    williams_r_period=14,
    show_obv=False,
    obv_smoothing_period=1,
    show_bollinger_band_markers=False,
    show_psar_flip_markers=False,
    show_macd_cross_markers=False,
    show_cci_threshold_markers=False,
    show_williams_r_threshold_markers=False,
    show_obv_cross_markers=False,
    show_ma_cross_markers=False,
    show_ema_cross_markers=False,
    show_rsi_cross_markers=False,
    show_donchian_breakout_markers=False,
    marker_symbol_table: qtable = pd.DataFrame({
        'chart': ['MA', 'EMA', 'RSI', 'DONCHIAN', 'BOLLINGER', 'PSAR', 'MACD', 'ATR', 'CCI', 'WILLIAMS_R', 'OBV'],
        'buy':   ['^', 'D', 'o', '*', '+', 'X', 's', 'D', '^', 'o', 's'],
        'sell':  ['v', 'D', 'o', '*', '+', 'X', 's', 'D', 'v', 'o', 's'],
    }),
    support_levels: qchar = '',
    resistance_levels: qchar = '',
    renko_brick_size: qchar = 'atr',
    pnf_box_size: qchar = 'atr',
    pnf_reversal=3,
):
    df = as_qtable(data)

    if show_mapping:
        date_col = str(date_column_name).strip()
        open_col = str(open_column_name).strip()
        high_col = str(high_column_name).strip()
        low_col = str(low_column_name).strip()
        close_col = str(close_column_name).strip()
        volume_col = str(volume_column_name).strip()
        if not date_col or not open_col or not high_col or not low_col or not close_col:
            raise ValueError('Mapping fields for Date/Open/High/Low/Close cannot be empty')
        if (show_volume or show_obv) and not volume_col:
            raise ValueError('Volume mapping cannot be empty when Volume or OBV overlays are enabled')
    else:
        date_col = 'Date'
        open_col = 'Open'
        high_col = 'High'
        low_col = 'Low'
        close_col = 'Close'
        volume_col = 'Volume'

    required_columns = [date_col, open_col, high_col, low_col, close_col]
    if show_volume or show_obv:
        required_columns.append(volume_col)
    require_columns(df, 'data', required_columns)

    date_column = df[date_col]
    open_column = df[open_col]
    high_column = df[high_col]
    low_column = df[low_col]
    close_column = df[close_col]
    volume_column = df[volume_col] if (volume_col in df.columns) else None

    ohlc = pd.DataFrame({
        'Open': pd.to_numeric(open_column, errors='coerce'),
        'High': pd.to_numeric(high_column, errors='coerce'),
        'Low': pd.to_numeric(low_column, errors='coerce'),
        'Close': pd.to_numeric(close_column, errors='coerce'),
    })
    ohlc.index = pd.to_datetime(date_column, errors='coerce')

    if ohlc.empty:
        raise ValueError('Data table must contain at least one row')
    if ohlc.index.isna().any():
        raise ValueError(f'Date column "{date_col}" contains invalid date values')
    if ohlc[['Open', 'High', 'Low', 'Close']].isna().any().any():
        raise ValueError(
            f'Mapped Open/High/Low/Close columns ({open_col}, {high_col}, {low_col}, {close_col}) must contain numeric values'
        )
    if not np.isfinite(ohlc[['Open', 'High', 'Low', 'Close']].to_numpy(dtype=float)).all():
        raise ValueError('Open, High, Low, and Close columns must contain finite numeric values (no NaN/Inf)')
    if (ohlc['High'] < ohlc['Low']).any():
        raise ValueError('Each row must satisfy High >= Low')
    if ((ohlc['Open'] < ohlc['Low']) | (ohlc['Open'] > ohlc['High'])).any():
        raise ValueError('Each row must satisfy Low <= Open <= High')
    if ((ohlc['Close'] < ohlc['Low']) | (ohlc['Close'] > ohlc['High'])).any():
        raise ValueError('Each row must satisfy Low <= Close <= High')

    if show_volume or show_obv:
        volume_vals = pd.to_numeric(volume_column, errors='coerce')
        if volume_vals.isna().any():
            raise ValueError('Volume column must contain numeric values')
        if not np.isfinite(volume_vals.to_numpy(dtype=float)).all():
            raise ValueError('Volume column must contain finite numeric values (no NaN/Inf)')
        if (volume_vals < 0).any():
            raise ValueError('Volume must be non-negative')
        ohlc['Volume'] = volume_vals.to_numpy(dtype=float)

    ohlc = ohlc.sort_index()
    if ohlc.index.duplicated().any():
        agg = {'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last'}
        if 'Volume' in ohlc.columns:
            agg['Volume'] = 'sum'
        ohlc = ohlc.groupby(level=0).agg(agg)

    timeframe_map = {
        'raw': None,
        '5m': '5min',
        '15m': '15min',
        '1h': '1h',
        '4h': '4h',
        '1d': '1D',
        '1w': '1W',
        '1mo': '1M',
    }
    if timeframe not in timeframe_map:
        raise ValueError(f'Unsupported timeframe: {timeframe}')

    try:
        chart_width = int(chart_width) if int(chart_width) > 0 else int(QThread.get_pref('chart_width', 900))
    except (TypeError, ValueError) as exc:
        raise ValueError('Chart width must be a positive integer') from exc
    try:
        chart_height = int(chart_height) if int(chart_height) > 0 else int(QThread.get_pref('chart_height', 600))
    except (TypeError, ValueError) as exc:
        raise ValueError('Chart height must be a positive integer') from exc
    if chart_width <= 0:
        raise ValueError('Chart width must be a positive integer')
    if chart_height <= 0:
        raise ValueError('Chart height must be a positive integer')
    chart_aspect = float(chart_height) / float(chart_width)

    resample_rule = timeframe_map[timeframe]
    if resample_rule is not None:
        agg = {'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last'}
        if 'Volume' in ohlc.columns:
            agg['Volume'] = 'sum'
        ohlc = ohlc.resample(resample_rule).agg(agg).dropna(subset=['Open', 'High', 'Low', 'Close'])
        if ohlc.empty:
            raise ValueError('No data points remain after timeframe resampling')

    mav = None
    if show_moving_average:
        mav = tuple(css2ints(moving_average_periods)) if str(moving_average_periods).strip() else None
        if mav is not None and any(period <= 0 for period in mav):
            raise ValueError('Moving average periods must be positive integers')
        if mav is not None:
            data_points = len(ohlc.index)
            mav = tuple(period for period in mav if period <= data_points)
            if len(mav) == 0:
                mav = None

    mpf_type = chart_type
    plot_data = ohlc
    plot_mav = mav
    extra_kwargs = {}
    add_plots = []
    hlines = []
    ignored_overlays = []

    if chart_type == 'heikin':
        mpf_type = 'candle'
        plot_data = _to_heikin_ashi(ohlc)
    elif chart_type == 'renko':
        plot_mav = None
        brick_size = _parse_box_size(renko_brick_size, 'Renko brick size')
        renko_params = {'brick_size': brick_size}
        if brick_size == 'atr':
            if len(plot_data) < 2:
                raise ValueError('Renko with ATR brick size needs at least 2 data points')
            renko_params['atr_length'] = max(1, min(14, len(plot_data) - 1))
        extra_kwargs['renko_params'] = renko_params
    elif chart_type == 'pnf':
        plot_mav = None
        try:
            pnf_reversal = int(pnf_reversal)
        except (TypeError, ValueError) as exc:
            raise ValueError('PnF reversal must be a positive integer') from exc
        if pnf_reversal <= 0:
            raise ValueError('PnF reversal must be a positive integer')
        pnf_box = _parse_box_size(pnf_box_size, 'PnF box size')
        pnf_params = {
            'box_size': pnf_box,
            'reversal': pnf_reversal,
        }
        if pnf_box == 'atr':
            if len(plot_data) < 2:
                raise ValueError('PnF with ATR box size needs at least 2 data points')
            pnf_params['atr_length'] = max(1, min(14, len(plot_data) - 1))
        extra_kwargs['pnf_params'] = {
            **pnf_params,
        }
    elif chart_type not in {'candle', 'ohlc', 'line'}:
        raise ValueError(f'Unsupported chart_type: {chart_type}')

    if chart_type in {'renko', 'pnf'}:
        if show_moving_average:
            ignored_overlays.append('Moving Average')
            show_moving_average = False
            plot_mav = None
        if show_ema:
            ignored_overlays.append('EMA')
            show_ema = False
        if show_bollinger:
            ignored_overlays.append('Bollinger')
            show_bollinger = False
        if show_donchian:
            ignored_overlays.append('Donchian')
            show_donchian = False
        if show_psar:
            ignored_overlays.append('Parabolic SAR')
            show_psar = False
        if show_rsi:
            ignored_overlays.append('RSI')
            show_rsi = False
        if show_macd:
            ignored_overlays.append('MACD')
            show_macd = False
        if show_atr:
            ignored_overlays.append('ATR')
            show_atr = False
        if show_cci:
            ignored_overlays.append('CCI')
            show_cci = False
        if show_williams_r:
            ignored_overlays.append('Williams %R')
            show_williams_r = False
        if show_obv:
            ignored_overlays.append('OBV')
            show_obv = False
        if show_ma_cross_markers:
            ignored_overlays.append('MA Cross Markers')
            show_ma_cross_markers = False
        if show_ema_cross_markers:
            ignored_overlays.append('EMA Cross Markers')
            show_ema_cross_markers = False
        if show_rsi_cross_markers:
            ignored_overlays.append('RSI Cross Markers')
            show_rsi_cross_markers = False
        if show_donchian_breakout_markers:
            ignored_overlays.append('Donchian Breakout Markers')
            show_donchian_breakout_markers = False
        if show_bollinger_band_markers:
            ignored_overlays.append('Bollinger Band Markers')
            show_bollinger_band_markers = False
        if show_psar_flip_markers:
            ignored_overlays.append('PSAR Flip Markers')
            show_psar_flip_markers = False
        if show_macd_cross_markers:
            ignored_overlays.append('MACD Cross Markers')
            show_macd_cross_markers = False
        if show_atr_cross_markers:
            ignored_overlays.append('ATR Cross Markers')
            show_atr_cross_markers = False
        if show_cci_threshold_markers:
            ignored_overlays.append('CCI Threshold Markers')
            show_cci_threshold_markers = False
        if show_williams_r_threshold_markers:
            ignored_overlays.append('Williams %R Threshold Markers')
            show_williams_r_threshold_markers = False
        if show_obv_cross_markers:
            ignored_overlays.append('OBV Cross Markers')
            show_obv_cross_markers = False
        if str(support_levels).strip() or str(resistance_levels).strip():
            ignored_overlays.append('Support/Resistance')
            support_levels = ''
            resistance_levels = ''

    if show_ema:
        ema_list = tuple(css2ints(ema_periods)) if str(ema_periods).strip() else None
        if not ema_list:
            raise ValueError('EMA periods must include at least one integer value')
        if any(period <= 0 for period in ema_list):
            raise ValueError('EMA periods must be positive integers')
        data_points = len(plot_data.index)
        ema_list = tuple(period for period in ema_list if period <= data_points)
        if len(ema_list) == 0:
            ignored_overlays.append('EMA (insufficient data for selected periods)')
            show_ema = False
        ema_colors = ['teal', 'darkcyan', 'cadetblue', 'steelblue', 'slategray']
        if show_ema:
            for i, period in enumerate(ema_list):
                ema = plot_data['Close'].ewm(span=period, adjust=False).mean()
                add_plots.append(mpf.make_addplot(ema, color=ema_colors[i % len(ema_colors)]))

    if show_bollinger:
        try:
            bollinger_period = int(bollinger_period)
        except (TypeError, ValueError) as exc:
            raise ValueError('Bollinger period must be an integer greater than 1') from exc
        if bollinger_period <= 1:
            raise ValueError('Bollinger period must be an integer greater than 1')
        if bollinger_period > len(plot_data.index):
            ignored_overlays.append('Bollinger (insufficient data)')
            show_bollinger = False
        try:
            bollinger_std = float(bollinger_std)
        except (TypeError, ValueError) as exc:
            raise ValueError('Bollinger std must be a positive number') from exc
        if bollinger_std <= 0:
            raise ValueError('Bollinger std must be a positive number')
        if show_bollinger:
            bb_mid = plot_data['Close'].rolling(window=bollinger_period).mean()
            bb_std = plot_data['Close'].rolling(window=bollinger_period).std(ddof=0)
            bb_upper = bb_mid + (bollinger_std * bb_std)
            bb_lower = bb_mid - (bollinger_std * bb_std)
            add_plots.append(mpf.make_addplot(bb_upper, color='purple', linestyle='--'))
            add_plots.append(mpf.make_addplot(bb_mid, color='royalblue'))
            add_plots.append(mpf.make_addplot(bb_lower, color='purple', linestyle='--'))

    if show_donchian:
        try:
            donchian_period = int(donchian_period)
        except (TypeError, ValueError) as exc:
            raise ValueError('Donchian period must be an integer greater than 1') from exc
        if donchian_period <= 1:
            raise ValueError('Donchian period must be an integer greater than 1')
        if donchian_period > len(plot_data.index):
            ignored_overlays.append('Donchian (insufficient data)')
            show_donchian = False
        if show_donchian:
            dc_upper = plot_data['High'].rolling(window=donchian_period).max()
            dc_lower = plot_data['Low'].rolling(window=donchian_period).min()
            add_plots.append(mpf.make_addplot(dc_upper, color='darkgreen', linestyle='-.'))
            add_plots.append(mpf.make_addplot(dc_lower, color='darkred', linestyle='-.'))

    if show_psar:
        try:
            psar_af_step = float(psar_af_step)
            psar_af_max = float(psar_af_max)
        except (TypeError, ValueError) as exc:
            raise ValueError('Parabolic SAR AF step/max must be numeric values') from exc
        if psar_af_step <= 0 or psar_af_max <= 0:
            raise ValueError('Parabolic SAR AF step/max must be greater than 0')
        if psar_af_step > psar_af_max:
            raise ValueError('Parabolic SAR AF step must be less than or equal to AF max')
        if len(plot_data.index) < 2:
            ignored_overlays.append('Parabolic SAR (insufficient data)')
            show_psar = False

        if show_psar:
            high = plot_data['High'].to_numpy(dtype=float)
            low = plot_data['Low'].to_numpy(dtype=float)
            close = plot_data['Close'].to_numpy(dtype=float)
            psar = np.empty(len(plot_data), dtype=float)
            bull = bool(close[1] >= close[0])
            af = psar_af_step
            ep = high[0] if bull else low[0]
            psar[0] = low[0] if bull else high[0]

            for i in range(1, len(plot_data)):
                psar_i = psar[i - 1] + af * (ep - psar[i - 1])
                if bull:
                    if i >= 2:
                        psar_i = min(psar_i, low[i - 1], low[i - 2])
                    else:
                        psar_i = min(psar_i, low[i - 1])
                    if low[i] < psar_i:
                        bull = False
                        psar_i = ep
                        ep = low[i]
                        af = psar_af_step
                    else:
                        if high[i] > ep:
                            ep = high[i]
                            af = min(psar_af_max, af + psar_af_step)
                else:
                    if i >= 2:
                        psar_i = max(psar_i, high[i - 1], high[i - 2])
                    else:
                        psar_i = max(psar_i, high[i - 1])
                    if high[i] > psar_i:
                        bull = True
                        psar_i = ep
                        ep = high[i]
                        af = psar_af_step
                    else:
                        if low[i] < ep:
                            ep = low[i]
                            af = min(psar_af_max, af + psar_af_step)
                psar[i] = psar_i

            psar_series = pd.Series(psar, index=plot_data.index)
            add_plots.append(mpf.make_addplot(psar_series, type='scatter', color='black', markersize=18, marker='.'))

    if str(support_levels).strip():
        hlines.extend(css2floats(support_levels))
    if str(resistance_levels).strip():
        hlines.extend(css2floats(resistance_levels))

    marker_symbol_map = _parse_marker_symbol_table(marker_symbol_table)
    marker_series = []

    if show_ma_cross_markers and not show_moving_average:
        show_ma_cross_markers = False
    if show_ema_cross_markers and not show_ema:
        show_ema_cross_markers = False
    if show_rsi_cross_markers and not show_rsi:
        show_rsi_cross_markers = False
    if show_donchian_breakout_markers and not show_donchian:
        show_donchian_breakout_markers = False
    if show_bollinger_band_markers and not show_bollinger:
        show_bollinger_band_markers = False
    if show_psar_flip_markers and not show_psar:
        show_psar_flip_markers = False
    if show_macd_cross_markers and not show_macd:
        show_macd_cross_markers = False
    if show_atr_cross_markers and not show_atr:
        show_atr_cross_markers = False
    if show_cci_threshold_markers and not show_cci:
        show_cci_threshold_markers = False
    if show_williams_r_threshold_markers and not show_williams_r:
        show_williams_r_threshold_markers = False
    if show_obv_cross_markers and not show_obv:
        show_obv_cross_markers = False

    if show_ma_cross_markers:
        ma_buy_markers, ma_sell_markers, ma_error = _compute_ma_cross_markers(plot_data, moving_average_periods)
        if ma_error:
            ignored_overlays.append(ma_error)
            show_ma_cross_markers = False
        else:
            marker_series.append(('MA', ma_buy_markers, ma_sell_markers))

    if show_ema_cross_markers:
        ema_buy_markers, ema_sell_markers, ema_error = _compute_ema_cross_markers(plot_data, ema_periods)
        if ema_error:
            ignored_overlays.append(ema_error)
            show_ema_cross_markers = False
        else:
            marker_series.append(('EMA', ema_buy_markers, ema_sell_markers))

    if show_rsi_cross_markers:
        rsi_buy_markers, rsi_sell_markers, rsi_error = _compute_rsi_cross_markers(
            plot_data, rsi_period, rsi_oversold, rsi_overbought
        )
        if rsi_error:
            ignored_overlays.append(rsi_error)
            show_rsi_cross_markers = False
        else:
            marker_series.append(('RSI', rsi_buy_markers, rsi_sell_markers))

    if show_donchian_breakout_markers:
        don_buy_markers, don_sell_markers, don_error = _compute_donchian_breakout_markers(plot_data, donchian_period)
        if don_error:
            ignored_overlays.append(don_error)
            show_donchian_breakout_markers = False
        else:
            marker_series.append(('DONCHIAN', don_buy_markers, don_sell_markers))

    if show_bollinger_band_markers:
        bb_buy_markers, bb_sell_markers, bb_error = _compute_bollinger_reentry_markers(
            plot_data, bollinger_period, bollinger_std
        )
        if bb_error:
            ignored_overlays.append(bb_error)
            show_bollinger_band_markers = False
        else:
            marker_series.append(('BOLLINGER', bb_buy_markers, bb_sell_markers))

    if show_psar_flip_markers:
        psar_buy_markers, psar_sell_markers, psar_error = _compute_psar_flip_markers(
            plot_data, psar_af_step, psar_af_max
        )
        if psar_error:
            ignored_overlays.append(psar_error)
            show_psar_flip_markers = False
        else:
            marker_series.append(('PSAR', psar_buy_markers, psar_sell_markers))

    if show_macd_cross_markers:
        macd_buy_markers, macd_sell_markers, macd_error = _compute_macd_cross_markers(
            plot_data, macd_fast_period, macd_slow_period, macd_signal_period
        )
        if macd_error:
            ignored_overlays.append(macd_error)
            show_macd_cross_markers = False
        else:
            marker_series.append(('MACD', macd_buy_markers, macd_sell_markers))

    if show_atr_cross_markers:
        atr_buy_markers, atr_sell_markers, atr_error = _compute_atr_cross_markers(plot_data, atr_period, atr_mav_period)
        if atr_error:
            ignored_overlays.append(atr_error)
            show_atr_cross_markers = False
        else:
            marker_series.append(('ATR', atr_buy_markers, atr_sell_markers))

    if show_cci_threshold_markers:
        cci_buy_markers, cci_sell_markers, cci_error = _compute_cci_threshold_markers(plot_data, cci_period)
        if cci_error:
            ignored_overlays.append(cci_error)
            show_cci_threshold_markers = False
        else:
            marker_series.append(('CCI', cci_buy_markers, cci_sell_markers))

    if show_williams_r_threshold_markers:
        wr_buy_markers, wr_sell_markers, wr_error = _compute_williams_r_threshold_markers(plot_data, williams_r_period)
        if wr_error:
            ignored_overlays.append(wr_error)
            show_williams_r_threshold_markers = False
        else:
            marker_series.append(('WILLIAMS_R', wr_buy_markers, wr_sell_markers))

    if show_obv_cross_markers:
        obv_buy_markers, obv_sell_markers, obv_error = _compute_obv_cross_markers(plot_data, obv_smoothing_period)
        if obv_error:
            ignored_overlays.append(obv_error)
            show_obv_cross_markers = False
        else:
            marker_series.append(('OBV', obv_buy_markers, obv_sell_markers))

    marker_offset_pct = 0.0035
    for idx, (chart_key, buy_markers, sell_markers) in enumerate(marker_series):
        buy_symbol, sell_symbol = marker_symbol_map[chart_key]
        buy_shift = 1.0 - (marker_offset_pct * idx)
        sell_shift = 1.0 + (marker_offset_pct * idx)
        buy_adjusted = buy_markers * buy_shift
        sell_adjusted = sell_markers * sell_shift
        if buy_adjusted.notna().any():
            add_plots.append(mpf.make_addplot(buy_adjusted, type='scatter', marker=buy_symbol,
                                              markersize=70, color='green'))
        if sell_adjusted.notna().any():
            add_plots.append(mpf.make_addplot(sell_adjusted, type='scatter', marker=sell_symbol,
                                              markersize=70, color='red'))

    next_panel = 2 if show_volume else 1
    has_rsi_panel = False

    if show_rsi:
        try:
            rsi_period = int(rsi_period)
        except (TypeError, ValueError) as exc:
            raise ValueError('RSI period must be an integer greater than 1') from exc
        if rsi_period <= 1:
            raise ValueError('RSI period must be an integer greater than 1')
        if rsi_period > len(plot_data.index):
            ignored_overlays.append('RSI (insufficient data)')
            show_rsi = False
        try:
            rsi_overbought = float(rsi_overbought)
            rsi_oversold = float(rsi_oversold)
        except (TypeError, ValueError) as exc:
            raise ValueError('RSI overbought/oversold levels must be numeric values') from exc
        if not (0 <= rsi_oversold <= 100 and 0 <= rsi_overbought <= 100):
            raise ValueError('RSI overbought/oversold levels must be between 0 and 100')
        if rsi_oversold >= rsi_overbought:
            raise ValueError('RSI oversold must be lower than RSI overbought')

        if show_rsi:
            close = plot_data['Close']
            delta = close.diff()
            gains = delta.clip(lower=0)
            losses = -delta.clip(upper=0)
            avg_gain = gains.rolling(window=rsi_period, min_periods=rsi_period).mean()
            avg_loss = losses.rolling(window=rsi_period, min_periods=rsi_period).mean()
            rs = avg_gain / avg_loss.replace(0, np.nan)
            rsi = 100 - (100 / (1 + rs))
            rsi = rsi.where(avg_loss != 0, 100.0)
            rsi = rsi.where(~((avg_gain == 0) & (avg_loss == 0)), 50.0)

            rsi_panel = next_panel
            next_panel += 1
            has_rsi_panel = True
            add_plots.append(mpf.make_addplot(rsi, panel=rsi_panel, color='darkorange', ylabel='RSI'))
            add_plots.append(mpf.make_addplot(pd.Series(rsi_overbought, index=plot_data.index), panel=rsi_panel,
                                              color='gray', linestyle='--'))
            add_plots.append(mpf.make_addplot(pd.Series(rsi_oversold, index=plot_data.index), panel=rsi_panel,
                                              color='gray', linestyle='--'))

    oscillator_panels = 0

    if show_macd:
        try:
            macd_fast_period = int(macd_fast_period)
            macd_slow_period = int(macd_slow_period)
            macd_signal_period = int(macd_signal_period)
        except (TypeError, ValueError) as exc:
            raise ValueError('MACD periods must be integers') from exc
        if macd_fast_period <= 0 or macd_slow_period <= 0 or macd_signal_period <= 0:
            raise ValueError('MACD periods must be positive integers')
        if macd_fast_period >= macd_slow_period:
            raise ValueError('MACD fast period must be lower than MACD slow period')
        if macd_slow_period > len(plot_data.index):
            ignored_overlays.append('MACD (insufficient data)')
            show_macd = False

        if show_macd:
            ema_fast = plot_data['Close'].ewm(span=macd_fast_period, adjust=False).mean()
            ema_slow = plot_data['Close'].ewm(span=macd_slow_period, adjust=False).mean()
            macd_line = ema_fast - ema_slow
            macd_signal = macd_line.ewm(span=macd_signal_period, adjust=False).mean()
            macd_hist = macd_line - macd_signal
            macd_panel = next_panel
            next_panel += 1
            oscillator_panels += 1
            add_plots.append(mpf.make_addplot(macd_line, panel=macd_panel, color='navy', ylabel='MACD'))
            add_plots.append(mpf.make_addplot(macd_signal, panel=macd_panel, color='darkorange'))
            add_plots.append(mpf.make_addplot(macd_hist, panel=macd_panel, type='bar', color='gray', alpha=0.5))

    if show_atr:
        try:
            atr_period = int(atr_period)
        except (TypeError, ValueError) as exc:
            raise ValueError('ATR period must be an integer greater than 1') from exc
        try:
            atr_mav_period = int(atr_mav_period)
        except (TypeError, ValueError) as exc:
            raise ValueError('ATR MAV period must be an integer greater than 0') from exc
        if atr_period <= 1:
            raise ValueError('ATR period must be an integer greater than 1')
        if atr_mav_period <= 0:
            raise ValueError('ATR MAV period must be an integer greater than 0')
        if atr_period > len(plot_data.index):
            ignored_overlays.append('ATR (insufficient data)')
            show_atr = False

        if show_atr:
            high = plot_data['High']
            low = plot_data['Low']
            prev_close = plot_data['Close'].shift(1)
            tr1 = high - low
            tr2 = (high - prev_close).abs()
            tr3 = (low - prev_close).abs()
            true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            atr = true_range.rolling(window=atr_period, min_periods=atr_period).mean()
            atr_mav = atr.rolling(window=atr_mav_period, min_periods=atr_mav_period).mean()
            atr_panel = next_panel
            next_panel += 1
            oscillator_panels += 1
            add_plots.append(mpf.make_addplot(atr, panel=atr_panel, color='brown', ylabel='ATR'))
            if atr_mav.notna().any():
                add_plots.append(mpf.make_addplot(atr_mav, panel=atr_panel, color='darkorange'))
            else:
                ignored_overlays.append('ATR MAV (insufficient data)')

    if show_cci:
        try:
            cci_period = int(cci_period)
        except (TypeError, ValueError) as exc:
            raise ValueError('CCI period must be an integer greater than 1') from exc
        if cci_period <= 1:
            raise ValueError('CCI period must be an integer greater than 1')
        if cci_period > len(plot_data.index):
            ignored_overlays.append('CCI (insufficient data)')
            show_cci = False

        if show_cci:
            typical_price = (plot_data['High'] + plot_data['Low'] + plot_data['Close']) / 3.0
            cci_ma = typical_price.rolling(window=cci_period, min_periods=cci_period).mean()
            mad = (typical_price - cci_ma).abs().rolling(window=cci_period, min_periods=cci_period).mean()
            cci = (typical_price - cci_ma) / (0.015 * mad.replace(0, np.nan))
            cci_panel = next_panel
            next_panel += 1
            oscillator_panels += 1
            add_plots.append(mpf.make_addplot(cci, panel=cci_panel, color='indigo', ylabel='CCI'))
            add_plots.append(mpf.make_addplot(pd.Series(100.0, index=plot_data.index), panel=cci_panel,
                                              color='gray', linestyle='--'))
            add_plots.append(mpf.make_addplot(pd.Series(-100.0, index=plot_data.index), panel=cci_panel,
                                              color='gray', linestyle='--'))

    if show_williams_r:
        try:
            williams_r_period = int(williams_r_period)
        except (TypeError, ValueError) as exc:
            raise ValueError('Williams %R period must be an integer greater than 1') from exc
        if williams_r_period <= 1:
            raise ValueError('Williams %R period must be an integer greater than 1')
        if williams_r_period > len(plot_data.index):
            ignored_overlays.append('Williams %R (insufficient data)')
            show_williams_r = False

        if show_williams_r:
            hh = plot_data['High'].rolling(window=williams_r_period, min_periods=williams_r_period).max()
            ll = plot_data['Low'].rolling(window=williams_r_period, min_periods=williams_r_period).min()
            denom = (hh - ll).replace(0, np.nan)
            wr = -100.0 * (hh - plot_data['Close']) / denom
            wr_panel = next_panel
            next_panel += 1
            oscillator_panels += 1
            add_plots.append(mpf.make_addplot(wr, panel=wr_panel, color='darkmagenta', ylabel='W%R'))
            add_plots.append(mpf.make_addplot(pd.Series(-20.0, index=plot_data.index), panel=wr_panel,
                                              color='gray', linestyle='--'))
            add_plots.append(mpf.make_addplot(pd.Series(-80.0, index=plot_data.index), panel=wr_panel,
                                              color='gray', linestyle='--'))

    if show_obv:
        try:
            obv_smoothing_period = int(obv_smoothing_period)
        except (TypeError, ValueError) as exc:
            raise ValueError('OBV smoothing period must be an integer greater than 0') from exc
        if obv_smoothing_period <= 0:
            raise ValueError('OBV smoothing period must be an integer greater than 0')

        direction = np.sign(plot_data['Close'].diff().fillna(0.0))
        obv = (direction * plot_data['Volume']).fillna(0.0).cumsum()
        if obv_smoothing_period > 1:
            obv = obv.rolling(window=obv_smoothing_period, min_periods=1).mean()
        obv_panel = next_panel
        next_panel += 1
        oscillator_panels += 1
        add_plots.append(mpf.make_addplot(obv, panel=obv_panel, color='darkgreen', ylabel='OBV'))

    chart = QChart(width=chart_width, aspect=chart_aspect)
    plot_kwargs = {
        'type': mpf_type,
        'style': style,
        'title': title,
        'volume': show_volume,
        'show_nontrading': show_nontrading,
        'yscale': 'log' if log_scale else 'linear',
        'figsize': chart.figsize,
        'returnfig': True,
    }
    if plot_mav is not None:
        plot_kwargs['mav'] = plot_mav
    if add_plots:
        plot_kwargs['addplot'] = add_plots
    if hlines:
        plot_kwargs['hlines'] = dict(hlines=hlines, linestyle=':', linewidths=1.0, alpha=0.7)
    if has_rsi_panel or oscillator_panels > 0:
        panel_count = 1 + (1 if show_volume else 0)
        if has_rsi_panel:
            panel_count += 1
        panel_count += oscillator_panels
        panel_ratios = [6]
        if show_volume:
            panel_ratios.append(2)
        for _ in range(panel_count - len(panel_ratios)):
            panel_ratios.append(2)
        plot_kwargs['panel_ratios'] = tuple(panel_ratios)
    plot_kwargs.update(extra_kwargs)
    fig, axes = mpf.plot(plot_data, **plot_kwargs)

    chart.fig = fig
    chart.ax = axes[0] if isinstance(axes, (list, tuple)) else axes
    chart.render_done()

    result = {'chart': chart}
    if ignored_overlays:
        result['Note'] = qhtml(
            f"<small class='text-muted'>Ignored overlays for {chart_type.upper()}: {', '.join(ignored_overlays)}.</small>"
        )
    return result
