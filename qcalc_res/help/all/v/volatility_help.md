# Volatility and Drift from Historical Values

## Purpose

This calculator estimates volatility and drift from a historical value series and returns the latest observed value for follow-up forecasting.

It is useful as a preparation step before generating future value scenarios with the related forecast path calculator.

## Background

### Log-return estimation

The calculator first converts historical values to period-by-period log returns:

$$r_t=\ln\left(\frac{V_t}{V_{t-1}}\right)$$

Then it estimates:

- Volatility as the population standard deviation of log returns.
- Drift as mean log return plus half the variance.

## Inputs

- **historical_values**: Table with a `Values` column containing numeric historical values in time order.

## Results

- **Volatility**: Population standard deviation of log returns.
- **Drift**: Mean log return plus $0.5\times\text{variance}$.
- **Last Value**: Final value from the input series.
- **Historical chart**: Line chart of the historical values by period index.

## Understanding the Calculation

1. Read the `Values` series as numeric.
2. Compute log returns between consecutive rows:

$$r_t=\ln(V_t/V_{t-1})$$

3. Compute volatility:

$$\sigma=\text{pstdev}(r_t)$$

4. Compute drift:

$$\mu=\overline{r_t}+0.5\sigma^2$$

5. Return volatility, drift, the last observed value, and a chart.

## Example

Example scenario:

- historical_values has one `Values` column with sequential asset observations (for example daily closes).

Expected interpretation:

- Higher variability in adjacent observations increases Volatility.
- If average log returns are positive, Drift tends to be higher.
- `Last Value` can be passed directly into the related future-value forecast calculator as starting price.

## Important Assumptions and Interpretation

- Values are interpreted in their entered sequence order; no date parsing or sorting is performed in this function.
- The method uses log returns and population standard deviation as implemented.
- The function does not add interval estimates or risk metrics beyond these two parameters.
- A related next-step action is available to open future value forecasting with `starting_price`, `volatility`, and `drift` prefilled.
