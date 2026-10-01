# Forecasting Model (Decomposition-Based)

## Purpose

This calculator builds a time-series forecast from historical observations by combining level, trend, and seasonality choices. It supports both automatic model selection and manual component control.

Use it when you want future values plus fit diagnostics, decomposition details, and optional uncertainty intervals.

## Background

### Model family and components

The calculator uses decomposition-style exponential smoothing models. Depending on your selected structure, it can behave like:

- Constant baseline
- Simple Exponential Smoothing (changing level)
- Seasonal models without trend (additive or multiplicative)
- Holt linear trend
- Holt-Winters (trend + seasonality)

In Automatic mode, qCalc selects among these candidates using RMSE.

## Inputs

- **Historical observations**: Input table with columns Period and Value. Value must be numeric and finite.
- **Forecast periods**: Number of future periods to produce. Must be at least 1 and at most 120.
- **Forecast method**: Choose `Automatic` or `Manual components`. The initial mode is `Automatic`, which changes model structure and smoothing parameters automatically.
- **Level**: Used in Manual components mode (`Constant` or `Changing`).
- **Alpha (level smoothing)**: Used in Manual components mode; must satisfy $0<\alpha<1$.
- **Trend**: Used in Manual components mode (`None` or `Linear`).
- **Beta (trend smoothing)**: Used only for trend models in Manual components mode; must satisfy $0<\beta<1$.
- **Seasonality**: Used in Manual components mode (`None`, `Additive`, `Multiplicative`).
- **Gamma (seasonality smoothing)**: Used only for seasonal models in Manual components mode; must satisfy $0<\gamma<1$.
- **Random fluctuations**: `None` gives point forecast only; `Historical` adds interval bounds from residual history.
- **Seasonal period**: Required when seasonality is additive or multiplicative; must be at least 2.
- **Confidence level (%)**: Used when Random fluctuations is Historical; must be from 50 to 99.9.
- **Validation mode**: `Holdout` or `In-sample`. In Holdout mode, recent rows are split for validation.
- **Holdout split (%)**: Used when Validation mode is Holdout; must be from 5 to 50.

## Results

- **Forecast table**: Future rows `F1..Fm` with point forecast and, when enabled, lower/upper bounds at the chosen confidence level.
- **Forecast chart**: Combined chart of Actual, Fitted, Forecast, and optional interval bounds.
- **Forecast chart note**: Clarifies axis labels as `P1..Pn` (historical) and `F1..Fm` (forecast).
- **Decomposition**: Table by historical period with Level, Trend, Seasonal, Residual, Fitted, and Actual.
- **Model summary**: Selected model family/components, observation count, method mode, random mode, residual standard deviation, trend slope, and fitted parameter values.
- **Forecast accuracy**: Validation mode, training/test row counts, and MAE/RMSE/MAPE.
- **Model selection diagnostics**: In Automatic mode only. Candidate model eligibility and RMSE values, with selected model and selection basis.
- **Model selection note**: In Automatic mode only. Explains that selection prefers Holdout RMSE when feasible.

## Understanding the Calculation

1. qCalc reads Period/Value from Historical observations and validates limits.
2. Model choice:

- In `Automatic`, qCalc evaluates candidate models and selects the best RMSE model.
- In `Manual components`, qCalc maps your Level/Trend/Seasonality choices to one supported model key.

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
- Forecast method: `Automatic`
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
- If holdout training size is insufficient for a model, holdout scoring for that case is skipped and selection may rely on in-sample RMSE.
- The chart uses index labels (`P*`, `F*`) rather than original period text on the axis.
