# Stock Candlestick, OHLC, and Other Overlay Charts

## Purpose

This calculator plots OHLC market data as a price chart and lets you add multiple technical overlays and indicator panels on top of the same dataset.

It is designed to help you inspect trend, momentum, volatility, breakout behavior, and volume confirmation in one view, then form a structured buy/sell decision process.

## Background

### Price chart types

- `Candle`: Standard candlesticks that show Open, High, Low, Close per bar.
- `OHLC`: Bar format for the same OHLC values.
- `Line`: Close-only line chart.
- `Heikin-Ashi`: Smoothed candle construction using transformed OHLC values.
- `Renko`: Brick-based chart that focuses on price movement size rather than regular time bars.
- Point and Figure (`PnF`): Box-and-reversal chart focused on directional moves and reversals.

`Renko` and `PnF` are regime-style charts; in this calculator, most overlays/indicators are intentionally ignored for these types.

### Indicator groups

- Trend/overlay: `SMA`, `EMA`, `Bollinger` Bands, `Donchian`, `PSAR`, Support/Resistance.
- Momentum: `RSI`, `MACD`, `CCI`, `Williams %R`.
- Volatility: `ATR`.
- Volume flow: `OBV`.

## Inputs

### Data and Mapping

- Data: OHLCV table. Required logical fields are Date, Open, High, Low, Close; Volume is required when Volume panel or OBV is enabled.
- CSV URL and Load CSV: Optional quick load into Data.
- Show Mapping and mapping fields: Use when your input column names differ from default Date/OHLC/Volume names.

### Chart Setup

- Title: Chart title.
- Chart Type: candle, ohlc, line, renko, pnf, or heikin.
- Style: Visual preset.
- Timeframe: raw or resampled bars (5m, 15m, 1h, 4h, 1d, 1w, 1mo).
- Chart width/height: Figure size.
- Show nontrading: Include or hide non-trading gaps.
- Log scale: Logarithmic price axis.

### Overlays and Indicator Panels

- Volume panel toggle.
- `SMA`, `EMA`, `Bollinger`, `Donchian`, `PSAR` toggles and parameter fields.
- `RSI`, `MACD`, `ATR`, `CCI`, `Williams %R`, `OBV` toggles and parameter fields.

### Marker and Level Inputs

- Marker symbol table: Per-indicator buy/sell marker symbols.
- Support levels and Resistance levels: Horizontal guide lines.
- Marker toggles: Per-indicator crossover/breakout marker generation.

### Renko and PnF Inputs

- Renko brick size: Positive number or atr.
- PnF box size: Positive number or atr.
- PnF reversal: Positive integer.

## Results

- chart: Rendered price chart with selected overlays/panels.
- Note: Optional note listing overlays ignored for the selected chart type (mainly renko/pnf, or insufficient-data cases).

## Understanding the Calculation

### Data validation and preprocessing

The calculator validates:

- Date values are valid datetimes.
- Open, High, Low, Close are numeric finite values.
- High >= Low, and Open/Close each lie between Low and High.
- Volume (if required) is numeric, finite, and non-negative.

If duplicate timestamps exist, rows are aggregated by timestamp using first-open, max-high, min-low, last-close, and summed volume.

If timeframe is not raw, data is resampled using OHLC aggregation and volume sum.

### Overlay math used

- `SMA`: Rolling mean over selected periods.
- `EMA`: Exponential moving mean with selected spans.
- `Bollinger`: Mid = rolling mean; upper/lower = mid +/- std_multiplier * rolling std.
- `Donchian`: Rolling highest high and lowest low.
- `PSAR`: Iterative Parabolic SAR using AF step and AF max.
- `RSI`: Derived from rolling average gains/losses over RSI period.
- `MACD`: `EMA`(fast) - `EMA`(slow), plus signal `EMA` and histogram.
- `ATR`: Rolling mean of true range.
- `CCI`: (Typical price - rolling mean) / (0.015 * mean absolute deviation).
- `Williams %R`: Position of close within rolling high-low range, scaled to [-100, 0].
- `OBV`: Cumulative signed volume by close direction, optionally smoothed.

### Marker logic used by this calculator

Buy/sell markers are generated only when the corresponding marker toggle is on and the required base overlay is enabled.

- `MA` cross markers: Buy when fast `SMA` crosses above slow `SMA`; sell on opposite cross.
- `EMA` cross markers: Buy when fast EMA crosses above slow `EMA`; sell on opposite cross.
- `RSI` cross markers: Buy when `RSI` crosses up through oversold level; sell when `RSI` crosses down through overbought level.
- `Donchian` breakout markers: Buy when close breaks above prior upper channel; sell when close breaks below prior lower channel.
- `Bollinger` band markers: Buy when close re-enters upward above lower band; sell when close re-enters downward below upper band.
- `PSAR` flip markers: Buy on bearish-to-bullish `PSAR` flip; sell on bullish-to-bearish flip.
- `MACD` cross markers: Buy when `MACD` line crosses above signal; sell on opposite cross.
- `ATR` cross markers: Buy when `ATR` crosses above `ATR` moving average; sell when crossing below.
- `CCI` threshold markers: Buy when `CCI` crosses up through -100; sell when crossing down through +100.
- `Williams %R` threshold markers: Buy when %R crosses up through -80; sell when crossing down through -20.
- `OBV` cross markers: Buy when `OBV` crosses above `OBV` smoothing average; sell when crossing below.

## How to Make Buy/Sell Decisions with These Charts

### Practical interpretation by indicator

#### `RSI`:

- Background: Momentum oscillator from 0 to 100.
- Common interpretation: below oversold threshold suggests recovery potential; above overbought threshold suggests exhaustion risk.
- In this calculator, marker logic is threshold-cross based (cross up from oversold for buy, cross down from overbought for sell).

#### `MACD`:

- Background: Trend-following momentum from two `EMA`s.
- Common interpretation: bullish when `MACD` rises above signal, bearish when below.
- In this calculator, marker logic follows `MACD`-signal cross events.

#### `CCI` and `Williams %R`:

- Background: Mean-reversion style momentum oscillators.
- Common interpretation: threshold exits can indicate momentum turning points.
- In this calculator, marker logic is threshold-cross based as listed above.

#### `Donchian` and `Bollinger`:

- Background: Channel/band frameworks for breakout or reversion behavior.
- Donchian markers here are breakout-style; Bollinger markers here are re-entry-style.

#### `PSAR`:

- Background: Trend-following stop-and-reverse framework.
- Marker events indicate trend regime flips.

#### `ATR`:

- Background: Volatility magnitude, not direction.
- `ATR` cross markers indicate volatility regime shifts, best used with directional indicators.

#### `OBV`:

- Background: Volume-pressure proxy.
- `OBV` cross markers can support or weaken confidence in price-direction signals.


### Structured decision workflow

1. Start with trend context (price structure + `MA`/`EMA` + `PSAR`).
2. Confirm momentum direction (`MACD`, `RSI`, `CCI`, or `Williams %R`).
3. Check volatility regime (`ATR`) and volume confirmation (`OBV`).
4. Use support/resistance and channel context (`Donchian`/`Bollinger`) for entry location.
5. Prefer decisions where multiple independent signals agree, instead of any single marker.

### Important caution

Marker events are mechanical signal hints, not guaranteed trade outcomes. Use risk controls (position sizing, stop logic, invalidation levels) and validate against your strategy horizon and market conditions.

## Example

Example setup for directional swing review:

- Chart Type: candle
- Timeframe: 1d
- Overlays: `EMA` enabled with periods 8,21 and `EMA` cross markers on
- Panels: `RSI` (period 14, 70/30) and `MACD` (12,26,9), with markers on
- Context lines: selected support/resistance levels

How to read it:

- A higher-quality long setup typically appears when `EMA` bullish cross, `MACD` bullish cross, and `RSI` recovering from oversold are aligned near support.
- A higher-quality exit/short-risk warning typically appears when opposite conditions cluster near resistance.

## Important Assumptions and Interpretation

- `Renko`/`PnF` modes suppress most overlays and can return a Note about ignored features.
- Some overlays/markers are skipped when there is insufficient data length for selected periods.
- Volume column is mandatory when Volume panel or `OBV` is enabled.
- Timeframe resampling changes bar construction and therefore indicator values.
- This calculator is a technical-analysis visualization tool; it does not include transaction costs, slippage, liquidity impact, or portfolio/risk constraints.

**Important**: Use technical analysis as one input only, and combine it with risk management, position sizing, market context, and (when relevant) fundamental factors before making real trading decisions.
