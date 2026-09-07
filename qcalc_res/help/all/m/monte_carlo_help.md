# Monte Carlo Simulation

## Overview

The **Monte Carlo Simulation** calculator repeats an expression many times while randomly sampling one variable from a chosen probability distribution, then summarizes the resulting outcomes as a histogram, a table, and summary statistics.

It is useful when an input is uncertain and you want to see the *range* of likely results rather than a single answer for one assumed value.

Monte Carlo randomly samples values. It does not sweep a fixed range and is not the same as **Redo**, which performs a deterministic parameter sweep.

## How It Works

For each of the requested trials, Monte Carlo:

1. Draws a random value for the selected variable from the chosen distribution.
2. Substitutes the value for the variable in the expression.
3. Evaluates the resulting expression.
4. Extracts a scalar result value.
5. Repeats until all trials are drawn, then summarizes the collected results.

```text
random samples (per trial)
    -> substitute variable
    -> evaluate expression
    -> collect scalar result
    -> histogram + table + summary stats
```

A trial that fails to produce a usable numeric result (invalid substitution, evaluation error, or a non-numeric result) is counted separately and excluded from the statistics, rather than stopping the whole run.

## Inputs

### Expression

The expression or calculator call to repeat. The expression should contain the variable named in **Variable**.

The default expression is:

```python
sine('x deg')
```

### Variable

The variable name to replace with a randomly sampled value on each trial, for example:

```text
x
```

### Distribution

The probability distribution to sample the variable from:

- `normal` — bell-shaped, can produce values on either side of the mean.
- `uniform` — every value between the low and high bound is equally likely.
- `triangular` — a low, high, and most likely (mode) value; useful for simple estimates.
- `lognormal` — right-skewed and always positive; useful for prices, durations, or growth rates that cannot go negative.

### Param1, Param2, Param3

The meaning of these depends on the selected distribution:

| Distribution | Param1        | Param2         | Param3                     |
|--------------|---------------|----------------|-----------------------------|
| normal       | mean          | stdev          | not used                    |
| uniform      | low           | high           | not used                    |
| triangular   | low           | high           | mode (defaults to midpoint) |
| lognormal    | mu            | sigma          | not used                    |

`mu`/`sigma` for `lognormal` describe the underlying normal distribution, not the mean/stdev of the sampled values themselves.

### Trials

The number of random samples to draw and evaluate. More trials produce a smoother histogram and more stable statistics, at the cost of more computation. Trials are capped by the configured range limit.

### Bin Count

The number of histogram bins used to group the results.

### Round Off

The number of decimal places used to round each sampled value before substitution.

### Result Columns / Result Units / Chart Column

Optional filters, matching the same convention as Redo, for when the expression returns more than one scalar value. **Chart Column** selects which single result column the histogram is built from; if more than one column would otherwise qualify, specify one explicitly.

### Show

Controls whether the result is displayed as a table, chart (histogram), or both. Summary statistics are always computed regardless of this setting.

### Chart Title

An optional title for the histogram.

## Outputs

Along with the table/chart (depending on **Show**), Monte Carlo always returns:

- `trials_used` — number of trials that produced a usable numeric result.
- `trials_failed` — number of trials excluded (evaluation error or non-numeric result).
- `mean`, `stdev`, `min`, `max` — summary statistics over the used trials.
- `p5`, `p50`, `p95` — the 5th, 50th (median), and 95th percentiles, a common way to express a confidence range (e.g. "90% of outcomes fall between p5 and p95").

## Example: Angle with Measurement Uncertainty

Use:

```python
sine('x deg')
```

with:

```text
Variable: x
Distribution: normal
Param1 (mean): 180
Param2 (stdev): 90
Trials: 500
```

Even though `x` is sampled from a symmetric bell curve, `sine()` is nonlinear, so the resulting histogram is not a bell curve — it piles up near `+1`/`-1`. This illustrates why Monte Carlo is most useful for *nonlinear* expressions: a linear/identity expression would just reproduce the input distribution's shape.

## Example: Cost Estimate with a Triangular Distribution

Use an expression that computes a total cost from an uncertain unit price:

```python
x * 120
```

with:

```text
Variable: x
Distribution: triangular
Param1 (low): 8
Param2 (high): 15
Param3 (mode): 10
Trials: 1000
```

This reflects a typical estimation scenario: a low, high, and most-likely value for an uncertain input, producing a realistic spread of possible total costs rather than one fixed number.

## Choosing Distribution Parameters

- Use `normal` when you have a typical value and know how much it usually varies (mean and standard deviation).
- Use `uniform` when you only know a plausible low and high bound, with no reason to favor any value in between.
- Use `triangular` when you have a low, high, and best-guess (most likely) value — common in cost and schedule estimation.
- Use `lognormal` when the quantity cannot be negative and tends to have a long tail on the high side (e.g. prices, durations).

## Expression Rules

The expression must remain valid after substitution. If a quantity requires a unit, include the unit around the variable, for example:

```python
q('x usd') * 1.2
```

Avoid using a short variable such as `x` when the expression also contains similarly named identifiers, e.g. `x_value`.

## Errors and Performance

A trial can fail when the substituted value makes the expression invalid. Common causes include:

- A value outside a calculator's valid range.
- A missing or incompatible unit.
- An invalid expression after substitution.
- A result that cannot be converted into a single scalar number.

Failed trials are counted in `trials_failed` and excluded from the statistics rather than stopping the whole simulation. If every trial fails, an error is raised instead of returning empty statistics.

Each trial re-evaluates the full expression, so a large number of trials on an expensive expression (e.g. one that calls another involved calculator) can take noticeably longer than a single ordinary calculation. Start with a moderate trial count, such as 200 to 500, before increasing it.

## Redo and Monte Carlo

Redo is a deterministic parameter sweep:

```text
known values
    -> one value at a time
    -> repeat calculation
    -> chart sensitivity
```

Monte Carlo is a random simulation:

```text
randomly sampled values
    -> many repeated calculations
    -> probability distribution of outcomes
```

Use Redo first to understand the controlled, deterministic relationship between a variable and the result. Use Monte Carlo afterward, once you have a plausible distribution in mind for an uncertain input, to see the realistic range and likelihood of outcomes.

## Summary

Use Monte Carlo to:

- Repeat a qCalc expression many times with a randomly sampled variable.
- Model an input whose exact value is uncertain but whose typical range is known.
- Generate a histogram, table, and summary statistics (mean, stdev, min, max, percentiles) of the outcomes.
- Understand how uncertainty in one input propagates through a (often nonlinear) calculation.
