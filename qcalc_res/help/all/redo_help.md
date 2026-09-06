# Redo Calculation

## Overview

The **Redo Calculation** calculator repeats an expression over a range of values for one variable and displays the resulting values as a table and/or chart.

It is useful for exploring how a result changes when one input changes. This is also called a **parameter sweep** or **sensitivity analysis**.

Redo performs a deterministic sweep. It does not randomly sample values and is not a Monte Carlo simulation.

## How It Works

For each value in the selected range, Redo:

1. Substitutes the value for the selected variable in the expression.
2. Evaluates the resulting expression.
3. Extracts scalar result values.
4. Collects the results for that range value.
5. Builds the requested table and/or chart.

```text
range values
    -> substitute variable
    -> evaluate expression
    -> collect scalar results
    -> display table/chart
```

## Inputs

### Expression

The expression or calculator call to repeat. The expression should contain the variable selected in **Variable**.

The default expression is:

```python
sine('x deg')
```

Expressions may call qCalc calculators. For example:

```python
retirement_sustainability(
    portfolio='500000 USD',
    withdrawal='30000 USD/yr',
    investment_return='9 pct/yr',
    inflation='x pct/yr',
    investment_tax='15 pct',
    retirement_period='30 yr'
)
```

### Variable

The variable name to replace at each sweep point. For the examples above, use:

```text
x
```

The variable should appear as a standalone token or as the numeric part of a quantity string such as:

```python
inflation='x pct/yr'
```

### Variation Start

The first value in the sweep range.

### Variation Stop

The end value in the sweep range.

### Variation Step

The increment between consecutive values. For example:

```text
Start: 1
Stop: 6
Step: 1
```

produces values such as:

```text
1, 2, 3, 4, 5, 6
```

The valid-range helper limits the number of sweep points so that an accidentally tiny step over a large range does not create excessive work.

### Step Round Off

The number of decimal places used to round generated values before substitution. A step of `0.5` with round-off `2` produces values such as `1.00`, `1.50`, `2.00`, and `2.50`.

### Result Columns

Optional result names to include in the output. This is useful when the expression returns several scalar values and only some are relevant.

For a retirement calculation, useful names may include:

```text
Final Balance
Sustainable Withdrawal
Depletion Year
```

### Result Units

Optional units for selected result columns.

### Chart Columns

Optional result columns to draw as chart series. For example:

```text
Final Balance
Sustainable Withdrawal
```

### Chart Units

Optional units for the selected chart columns.

### Show

Controls whether the result is displayed as a table, chart, or both.

### Chart Title

An optional title for the chart.

### Chart Type

Available chart styles include:

- `lines`
- `bars`
- `stack`

Line charts are generally useful for showing how a result changes across an ordered numeric range.

## Example: Trigonometric Sweep

Use:

```python
sine('x deg')
```

with:

```text
Variable: x
Variation Start: 0
Variation Stop: 360
Variation Step: 10
Step Round Off: 2
```

This evaluates sine for each angle from 0 to 360 degrees. A line chart makes the periodic shape easy to inspect.

## Example: Retirement Sensitivity Analysis

Use this expression:

```python
retirement_sustainability(
    portfolio='500000 USD',
    withdrawal='30000 USD/yr',
    investment_return='9 pct/yr',
    inflation='x pct/yr',
    investment_tax='15 pct',
    retirement_period='30 yr'
)
```

Use these sweep settings:

```text
Variable: x
Variation Start: 1
Variation Stop: 6
Variation Step: 0.5
Step Round Off: 2
```

This runs the complete retirement calculator repeatedly while changing inflation from 1% to 6% per year.

Useful result or chart columns include:

```text
Final Balance
Sustainable Withdrawal
Depletion Year
```

This helps answer questions such as:

- How does final portfolio balance change as inflation increases?
- At what inflation rate does the portfolio become depleted?
- How does the sustainable withdrawal estimate change?

Each point runs the complete retirement calculation, including its annual projection, so a large sweep can take longer than one ordinary calculation.

## Choosing a Good Sweep

Change one meaningful variable while keeping the other inputs fixed. Good examples include:

- Inflation from 1% to 6%.
- Investment return from 4% to 10%.
- Withdrawal from 20,000 USD/yr to 50,000 USD/yr.
- Retirement period from 20 yr to 40 yr.
- An angle from 0 to 360 degrees.

Start with a moderate number of points, such as 10 to 25. Increase the range or reduce the step only when more detail is needed.

## Expression Rules

The expression must remain valid after substitution. If a quantity requires a unit, include the unit around the variable:

```python
inflation='x pct/yr'
```

Avoid using a short variable such as `x` when the expression also contains names such as `x_value`. Use a clear variable name such as `x`, `rate`, or `inflation_rate` and keep it separate from other identifiers.

## Errors and Performance

A sweep point can fail when the substituted value makes the expression invalid. Common causes include:

- A value outside a calculator's valid range.
- A missing or incompatible unit.
- An invalid expression after substitution.
- A result that cannot be converted into scalar values.
- An invalid variation step.

Test the expression with one ordinary value first, then try a small range before increasing the number of points.

Each range value causes another evaluation. Calculators that perform long projections may take noticeably longer than simple expressions. Avoid combining a very small step with a very large range.

## Redo and Simulation

Redo is a deterministic parameter sweep:

```text
known values
    -> one value at a time
    -> repeat calculation
    -> chart sensitivity
```

A Monte Carlo simulation is different:

```text
randomly sampled values
    -> many repeated calculations
    -> probability distribution
```

Redo is useful when you want to understand a controlled relationship between one variable and the result. It is often a clear first step before uncertainty analysis or random simulation.

## Summary

Use Redo to:

- Repeat a qCalc expression over a numeric range.
- Study sensitivity to one variable.
- Sweep an input of another calculator.
- Generate a table or chart of the results.
- Perform deterministic analysis before considering random simulation.
