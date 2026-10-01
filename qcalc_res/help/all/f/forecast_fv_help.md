# Forecast Future Values of an Asset based on Volatility and Drift

## Purpose

This calculator simulates one future value path for an asset using drift and volatility inputs.

It is useful for quick scenario exploration when you want a stochastic (randomized) path rather than a fixed deterministic curve.

## Background

### Drift-volatility path simulation

The path uses multiplicative random returns of the form:

$$R_t=\exp(\mu+\sigma Z_t)$$

where $\mu$ is Drift, $\sigma$ is Volatility, and $Z_t$ is a standard normal random draw.

## Inputs

- **starting_price**: Initial asset value used as the first plotted point.
- **periods**: Number of simulated points in the returned series.
- **volatility**: Dispersion factor of the random return term.
- **drift**: Mean-growth component applied inside the exponential return term.

## Results

- **Forecast Values**: One simulated value path as a list.
- **Forecast chart**: Line chart of the simulated path versus forecast step index.

## Understanding the Calculation

1. qCalc generates `periods` random multiplicative returns:

$$R_t=\exp(\text{drift}+\text{volatility}\times Z_t)$$

2. The path starts with `starting_price`.

3. For each next step, the previous price is multiplied by the generated return for that step index.

4. The output path is charted as `Forecast Value Path`.

## Example

Example scenario:

- starting_price `100`
- periods `10`
- volatility `0.05`
- drift `0.0`

Expected interpretation:

- The first value is the starting price.
- Later values move up or down depending on random draws, with larger swings when volatility is higher.

## Important Assumptions and Interpretation

- This function produces a single random path per run. Running again with the same inputs generally gives different values.
- No random seed input is provided in this calculator, so results are not fixed/reproducible by default.
- The model is a simplified stochastic path generator for exploration, not a calibrated market model.
- The returned list length follows the `periods` setting; when `periods` is 1, the path contains only the starting value.
