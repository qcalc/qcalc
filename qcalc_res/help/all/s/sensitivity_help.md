# Sensitivity Analysis

## Purpose

`sensitivity()` estimates which uncertain inputs drive your output most.

Monte Carlo alone answers **"how wide is the output range?"**.  
Sensitivity analysis answers **"which assumptions are causing that range?"**

In short:

- **Monte Carlo** = output uncertainty distribution
- **Sensitivity** = contribution/importance of each input to that uncertainty

---

## When to use

Use this calculator when:

- you have multiple uncertain assumptions,
- you need driver ranking for decisions,
- you need direction (+/-) and strength of each driver.

Typical use cases:

- pricing and demand planning,
- project economics (CAPEX/OPEX uncertainty),
- operational risk analysis.

---

## Background knowledge (quick)

### What this calculator estimates

This calculator builds many sampled scenarios from your input distributions,
evaluates your model, and then estimates input importance using:

- **SRC** (Standardized Regression Coefficient): linear effect size after
  standardizing variables.
- **PRCC** (Partial Rank Correlation Coefficient): monotonic relationship
  strength, controlling for other variables, based on ranked data.

### Why two methods?

- **SRC** is easy to interpret and strong when relationships are roughly linear.
- **PRCC** is often more robust when relationships are monotonic but not strictly linear.
- If **both agree** on top drivers and sign, confidence is higher.

### What sensitivity scores are not

- They are **not** percentages of total variance.
- They do not prove causality beyond your model structure.
- They depend on your chosen input distributions/ranges.

If you widen or narrow a variable’s uncertainty range, its sensitivity score can
change substantially.

---

## Inputs

### Expression (`xpr`)

Your business/model equation. Default model:

```python
(price - unit_cost) * demand - fixed_cost
```

### Vary By (`variation_target`)

- `Variables` (`v`): vary expression variables directly.
- `Parameters` (`p`): vary named parameters inside function/calculator calls.

### Inputs table (`inputs`)

Use one row per uncertain variable with these columns:

```text
Variable | Distribution | Param 1 | Param 2 | Param 3
```

Supported distributions:

- `normal`: Param 1 = mean, Param 2 = stdev
- `uniform`: Param 1 = low, Param 2 = high
- `triangular`: Param 1 = low, Param 2 = high, Param 3 = mode
- `lognormal`: Param 1 = mu, Param 2 = sigma

Default example input:

```text
price      | normal     | 120   | 8    |
unit_cost  | normal     | 70    | 6    |
demand     | triangular | 700   | 1300 | 1000
fixed_cost | normal     | 25000 | 3000 |
```

### Analysis options

- `trials`: number of samples (start with 500+, often 2000+ for stable ranking)
- `method`:
  - `src` (Standardized Regression Coefficients)
  - `prcc` (Partial Rank Correlation Coefficients)
  - `both`
- `target_column`: required when multiple numeric outputs are returned
- `correlated_variables` + `correlation`: optional correlated pair
- `top_n`: keep top-ranked drivers only
- `random_seed`: reproducible runs
- `result_cells`: pick numeric cells if expression returns tables

---

## Outputs

### Summary

Shows:

- method used,
- target metric analyzed,
- trials requested / used / failed,
- SRC R² (when SRC is computed).

About **SRC R²**:

- closer to 1.0 => linear approximation explains most variation in target
- low value => target behavior may be nonlinear/interaction-heavy; rely more on
  PRCC and model-specific checks

### Table (ranked)

Main output columns include:

- `Variable`
- `SRC`, `SRC Abs`, `SRC Rank` (if SRC used)
- `PRCC`, `PRCC Abs`, `PRCC Rank` (if PRCC used)
- `Primary Score`, `Primary Abs`, `Direction`, `Rank`

How ranking is chosen:

- `method='src'`: ranking is based on SRC absolute value
- `method='prcc'`: ranking is based on PRCC absolute value
- `method='both'`: primary ranking favors PRCC-style monotonic signal while
  still showing SRC for cross-checking

### Chart

A tornado-style directional impact chart for quick driver comparison.

---

## Interpretation guide

### Core interpretation

- Larger absolute score => stronger driver.
- Positive score => increasing input tends to increase output.
- Negative score => increasing input tends to decrease output.
- Agreement between SRC and PRCC strengthens confidence.

### Practical reading pattern

1. **Check trial quality**
   - Review `Trials used` vs `Trials failed`.
   - High failure share means rankings may be unstable or biased by invalid regions.

2. **Check target definition**
   - Ensure `Target` is the exact metric you intend to optimize/control.
   - In multi-output models, wrong `target_column` means wrong conclusions.

3. **Read top drivers first**
   - Focus on top 3-5 ranks for action prioritization.
   - Use `Direction` to decide whether mitigation should increase, decrease, hedge, or stabilize a driver.

4. **Cross-check methods**
   - If SRC and PRCC disagree strongly, relationship may be nonlinear or non-monotonic.
   - Increase trials and inspect model structure before acting.

5. **Treat near-zero scores carefully**
   - Very small absolute values usually indicate weak influence within current uncertainty ranges.
   - They are not proof of irrelevance outside those ranges.

### Decision-oriented examples

- **Cost variable top-ranked negative**:
  prioritize procurement hedging, supplier contracts, or process efficiency.
- **Demand variable top-ranked positive**:
  prioritize forecast accuracy, demand sensing, and commercial planning.
- **Fixed cost low-ranked**:
  avoid over-investing effort on fixed-cost precision if other drivers dominate.

---

## Good practice

1. Start with `method='both'`.
2. Explicitly set `target_column` for multi-output expressions.
3. Use realistic distributions/units.
4. Re-run with more trials to check rank stability.
5. Re-test after major assumption changes (ranges/distributions) before comparing with earlier rankings.
