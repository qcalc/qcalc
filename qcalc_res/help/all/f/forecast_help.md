# Forecasting Model

## Purpose

This calculator builds a time-series forecast from historical observations and supports:

- automatic model selection
- manual exponential-smoothing configuration
- manual Moving Average and Linear Regression selection

Use it when you want future values, fit diagnostics, decomposition details, and optional uncertainty intervals.

## Background: what is forecasting?

Forecasting estimates future values of a quantity (such as monthly demand, sales, or call volume) from what has been observed in the past. It is used to plan inventory, production, staffing, and budgets before the actual outcome is known.

This calculator uses **time-series forecasting**: your data is a single series of values recorded at regular intervals (days, months, quarters, and so on), and the future is projected from patterns found in that series alone. No other explanatory variables are used.

### Patterns found in a time series

A series is usually described as a combination of these components:

- **Level**: the underlying average value of the series at a point in time.
- **Trend**: a steady rise or fall in the level over time.
- **Seasonality**: a pattern that repeats at a fixed interval, such as higher sales every December. The interval is the *seasonal period* (12 for monthly data with a yearly cycle, 4 for quarterly data).
- **Random fluctuation (noise)**: variation that no model can explain. It is the reason a forecast is never exact.

Seasonality can be **additive** (the seasonal swing is a constant amount added to the level) or **multiplicative** (the swing is a percentage of the level, so it grows as the level grows).

### How the methods work

- **Constant baseline**: forecasts a fixed value equal to the historical average.
- **Simple Exponential Smoothing (SES)**: the level is updated after each observation as a weighted average of the newest value and the previous level: $L_t = \alpha y_t + (1-\alpha)L_{t-1}$. A larger $\alpha$ reacts faster to recent changes; a smaller $\alpha$ gives smoother, more stable forecasts. Older observations receive exponentially smaller weights, which gives the method its name.
- **Holt linear trend**: extends SES with a second smoothing equation for the trend (controlled by $\beta$), so the forecast continues rising or falling.
- **Seasonal models and Holt-Winters**: add seasonal indices (controlled by $\gamma$) that are learned from the history and applied again for each future period. Holt-Winters combines level, trend, and seasonality.
- **Moving Average**: forecasts the average of the most recent *window* observations. It is simple and smooth, but it cannot represent trend or seasonality.
- **Linear Regression**: fits a straight line through the whole history against time and extends it forward.

### How a model is judged

A model is only useful if it forecasts data it has not seen. To test this, qCalc can hold back the most recent rows (**Holdout** validation), fit the model on the earlier rows, and compare its predictions with the held-out actual values. The differences are the forecast errors, summarised as MAD/MAE, MSE, RMSE, and MAPE. In **Automatic** mode, the eligible models are compared on RMSE and the lowest is chosen. A model that fits the history very closely is not necessarily a good forecaster, which is why out-of-sample (Holdout) scoring is preferred when enough rows are available.

### Uncertainty

Every forecast is an estimate. With **Random fluctuations** set to `Historical`, qCalc measures how far past fitted values were from the actual values (the residuals) and uses their spread to place lower and upper bounds around each forecast. The bounds widen further into the future because uncertainty accumulates.

### Limitations to keep in mind

- The forecast assumes that the patterns in the past continue. Sudden changes (new products, policy changes, disruptions) are not anticipated.
- More history gives more reliable estimates, especially for seasonal models, which need at least two full cycles.
- Long forecast horizons are less reliable than short ones.
- Treat the forecast as decision support alongside business judgement, not as a certainty.

## Supported methods

### Exponential smoothing family
- Constant baseline
- Simple Exponential Smoothing (changing level)
- Seasonal models without trend (additive or multiplicative)
- Holt linear trend
- Holt-Winters (trend + seasonality)

### Additional families
- Moving Average
- Linear Regression

In Automatic mode, qCalc compares eligible candidates using RMSE.

## Inputs

- **Historical observations**: Input table with columns Period and Value. Value must be numeric and finite.
- **Forecast periods**: Number of future periods to produce. Must be at least 1 and at most 120.
- **Method mode**:
  - `Automatic`: qCalc selects model structure/parameters
  - `Manual components`: choose smoothing components or a preset
  - `Manual model family`: choose Moving Average or Linear Regression directly
- **Manual method preset**: Used in Manual components mode. Presets (SES, Holt, Holt-Winters, etc.) auto-configure Level/Trend/Seasonality. `Custom` enables direct component editing.
- **Level / Trend / Seasonality**: Used in Manual components mode when preset is `Custom`.
- **Alpha (level smoothing)**: Used by smoothing models that include level update; must satisfy $0<\alpha<1$.
- **Beta (trend smoothing)**: Used by linear-trend smoothing models; must satisfy $0<\beta<1$.
- **Gamma (seasonality smoothing)**: Used by seasonal smoothing models; must satisfy $0<\gamma<1$.
- **Manual model family**: Used in Manual model family mode (`Moving Average`, `Linear Regression`).
- **Moving average window**: Used when Manual model family is `Moving Average`; must be at least 2 and smaller than observation count.
- **Random fluctuations**: `None` gives point forecast only; `Historical` adds interval bounds from residual history.
- **Seasonal period**: Required by seasonal smoothing models; must be at least 2.
- **Confidence level (%)**: Used when Random fluctuations is Historical; must be from 50 to 99.9.
- **Validation mode**: `Holdout` or `In-sample`. In Holdout mode, recent rows are split for validation.
- **Holdout split (%)**: Used when Validation mode is Holdout; must be from 5 to 50.

## Results

- **Forecast table**: Future rows `F1..Fm` with point forecast and, when enabled, lower/upper bounds at the chosen confidence level.
- **Forecast chart**: Combined chart of Actual, Fitted, Forecast, and optional interval bounds.
- **Forecast chart note**: Clarifies axis labels as `P1..Pn` (historical) and `F1..Fm` (forecast).
- **Decomposition**: Table by historical period with Level, Trend, Seasonal, Residual, Fitted, and Actual. Residual is Actual minus Fitted from the model fitted on all rows. With Holdout validation in effect, it also shows `Holdout forecast` and `Holdout error` (Actual minus Holdout forecast) for the held-out rows, using a model trained on earlier rows only.
- **Model summary**: Selected model family/components, observation count, method mode, random mode, residual standard deviation, trend slope, and fitted parameter values.
- **Forecast accuracy**: Validation mode, training/test row counts, MAD (MAE), MAE, MSE, RMSE, and MAPE.
- **Model selection diagnostics**: In Automatic mode only. Candidate model eligibility and RMSE values, with selected model and selection basis.
- **Model selection note**: In Automatic mode only. Explains that selection prefers Holdout RMSE when feasible.

## Understanding the Calculation

1. qCalc reads Period/Value from Historical observations and validates limits.
2. Model choice:

- In `Automatic`, qCalc evaluates eligible candidates and selects the best RMSE model.
- In `Manual components`, qCalc uses either:
  - preset mapping (e.g., Holt-Winters Additive), or
  - custom Level/Trend/Seasonality choices.
- In `Manual model family`, qCalc uses your direct selection (`Moving Average` or `Linear Regression`).

3. Validation scoring:

- `Holdout`: last percentage of rows is held out when enough training rows remain.
- If holdout would leave too few training rows for the selected model, qCalc falls back to in-sample scoring.

4. Fit and forecast:

- The selected model is fitted to history.
- Point forecasts are generated for `Forecast periods`.

5. Optional interval bounds:

- When Random fluctuations is `Historical`, residual standard deviation is estimated from fitted residuals.
- Bounds are then computed around each point forecast using a confidence z-score and a horizon-dependent scale factor.

6. Multiplicative seasonality condition:

- For multiplicative seasonal models, all historical Value entries must be greater than zero.

## Example

Example scenario:

- Historical observations: monthly values with a stable upward pattern
- Forecast periods: `12`
- Method mode: `Automatic`
- Random fluctuations: `Historical`
- Validation mode: `Holdout`, Holdout split: `20`

Expected interpretation:

- `Forecast table` shows `F1..F12` point estimates.
- Interval columns are populated because Random fluctuations is Historical.
- `Model selection diagnostics` identifies which candidate model had the best RMSE basis.

## Important Assumptions and Interpretation

- Automatic mode compares only the supported phase-1 model set, not every possible time-series model.
- Interval bounds are residual-history based and model-form dependent; they are uncertainty estimates, not guarantees.
- MAPE excludes rows where actual value is not greater than zero.
- For Moving Average, the window must be strictly smaller than total observations.
- If holdout training size is insufficient for a model, holdout scoring for that case is skipped and selection may rely on in-sample RMSE.
- The chart uses index labels (`P*`, `F*`) rather than original period text on the axis.
