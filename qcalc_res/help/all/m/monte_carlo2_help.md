# Monte Carlo Simulation 2

## Purpose

**Monte Carlo Simulation 2** repeats an expression many times while randomly
sampling several uncertain input variables. It summarizes the resulting
outcomes as a histogram, a table, and statistics such as the mean, standard
deviation, minimum, maximum, and percentiles.

Compared with the original Monte Carlo calculator, this version can propagate
uncertainty from multiple inputs at the same time. Variables are sampled
independently by default. One pair of normally distributed variables may
optionally be sampled with a specified correlation, which is useful when two
inputs tend to move together, such as inflation and interest rates.

## Background

### Multi-variable uncertainty

An ordinary calculation uses one fixed value for every input. A Monte Carlo
calculation instead treats uncertain inputs as probability distributions. Each
trial draws one value for every variable and evaluates the complete expression.

For example, if the expression is:

```python
x * y + z
```

one trial might use `x = 10.2`, `y = 4.8`, and `z = 3.1`. The next trial uses a
new combination. The output histogram shows how uncertainty in all three
inputs combines and passes through the expression.

This is especially useful for nonlinear expressions, products, ratios, totals,
and other calculations where the uncertainty in the result is not obvious from
the uncertainty in any single input.

### Independent and correlated inputs

By default, each variable is sampled independently. This means that a high
sample for one variable does not cause another variable's sample to be high or
low.

If two variables are related, enter their names in **Correlated Variables** and
enter their relationship in **Correlation**. A positive correlation makes the
two variables tend to move in the same direction; a negative correlation makes
them tend to move in opposite directions. A correlation of zero represents no
linear relationship in this model.

## Inputs

### Expression

The expression or calculator call to repeat. It should contain the variable
names listed in the **Inputs Table**.

The default expression is:

```python
(price - unit_cost) * demand - fixed_cost
```

### Vary By

Select what the sampled values change:

- `Parameters` (`p`) replaces named parameter values inside a calculator
  call.
- `Variables` (`v`) replaces standalone variables in an expression, such as
  `x + y`.

Use `Parameters` for calculator or function arguments and `Variables` for
direct expression variables. The default is `Parameters`.

For a multi-variable calculation, every variable that should be sampled must
be represented by its name in the expression. For example:

```python
inflation * principal + interest
```

### Inputs Table

Enter all sampled variables in one editable table. The calculator expects these
columns:

| Column | Meaning |
|---|---|
| Variable | The variable name used in the expression. |
| Distribution | One of `normal`, `uniform`, `triangular`, or `lognormal`. |
| Param 1 | Mean, low, or mu depending on the distribution. |
| Param 2 | Stdev, high, or sigma depending on the distribution. |
| Param 3 | Triangular mode only; leave blank for the other distributions. |

Each row describes one variable. The column names are validated, so keep them
as `Variable`, `Distribution`, `Param 1`, `Param 2`, and `Param 3`.

The parameter rules are:

- `normal`: Param 1 = mean, Param 2 = stdev, Param 3 = blank
- `uniform`: Param 1 = low, Param 2 = high, Param 3 = blank
- `triangular`: Param 1 = low, Param 2 = high, Param 3 = mode
- `lognormal`: Param 1 = mu, Param 2 = sigma, Param 3 = blank

Names must begin with a letter or underscore and may contain letters, numbers,
and underscores. Standard deviations and lognormal sigma values cannot be
negative. Uniform and triangular low values cannot exceed their corresponding
high values. The triangular mode must lie between the low and high values.

For example:

| Variable | Distribution | Param 1 | Param 2 | Param 3 |
|---|---|---:|---:|---:|
| inflation | normal | 3 | 1 |  |
| interest | normal | 5 | 1.5 |  |
| demand | uniform | 80 | 120 |  |

This table replaces the earlier comma-separated Variables, Distributions,
Param1s, Param2s, and Param3s fields.

| Variable | Distribution | Param 1 | Param 2 | Param 3 |
|---|---|---:|---:|---:|
| price | triangular | 8 | 15 | 10 |
| demand | normal | 100 | 20 |  |
| duration | triangular | 2 | 10 | 5 |

The mode must lie between the low and high values. If a row does not use the
triangular distribution, leave Param 3 blank.

### Trials

The number of random trials to perform. Each trial samples every variable and
evaluates the expression once. More trials generally make the histogram and
percentiles more stable, but increase computation time. The configured qCalc
range limit applies.

### Bin Count

The number of bins used to group calculated outcomes in the histogram. More
bins show more detail but can make a small simulation look irregular; fewer
bins give a more compressed view.

### Correlated Variables

An optional comma-separated pair of variable names:

```text
inflation, interest
```

Both names must already appear in the **Inputs Table**. Leave this field blank when
all variables should be sampled independently.

The pair must use the `normal` distribution. This version supports only one
correlated pair; it does not accept three-way correlation or a general
correlation matrix.

### Correlation

The correlation coefficient for the pair in **Correlated Variables**. It must
be between `-1` and `1`:

- `1` — perfect movement in the same direction.
- `0` — no linear correlation in the model.
- `-1` — perfect movement in opposite directions.

Leave this field blank when **Correlated Variables** is blank. It is treated as
zero and does not affect the independent-variable case.

### Result Columns, Result Units, and Histogram Column

These optional filters control which scalar result columns appear in the table
and which single result column supplies the histogram. If the expression
returns more than one scalar result, specify **Histogram Column** to identify
the result to plot.

### Show

Choose whether to display the table, histogram, or both. Summary statistics are
computed regardless of this choice.

### Chart Title

The title displayed above the histogram.

## Results

### Histogram

The histogram groups the calculated output values into the requested number of
bins. Its vertical axis is **Frequency**, meaning the number of successful
trials in each bin. Failed trials are not included in the histogram.

### Summary statistics

The calculator returns:

- `trials_used` — trials that produced a usable numeric result.
- `trials_failed` — trials excluded because evaluation failed or did not
  produce a numeric result.
- `mean` — arithmetic average of the successful outcomes.
- `stdev` — sample standard deviation of the successful outcomes.
- `min` and `max` — smallest and largest successful outcomes.
- `p5` — 5th percentile.
- `p50` — 50th percentile, also called the median.
- `p95` — 95th percentile.

The interval from `p5` to `p95` describes the middle 90 percent of the
simulated outcomes in the sample. It is a simulation interval, not a guarantee
that future observations must fall inside it.

## Decision Guidance

Use the histogram and percentiles as a management decision tool, not as a
promise of what will happen.

- Treat `p50` as the base-case outcome. This is the middle-ground number that
  is most useful for planning.
- Treat `p5` as the downside case. If that number is uncomfortable for cash,
  margin, capacity, or covenant planning, the proposal is exposed to risk.
- Treat `p95` as the upside case. It shows what a strong outcome could look
  like if conditions are favorable.
- Read the width of the distribution as volatility. A wide gap between `p5`
  and `p95` means the decision is less predictable and needs more buffer.
- Use `trials_failed` as a warning signal. If failures are present, the model
  may need cleaner inputs or tighter expression logic before it supports a
  business decision.
- Compare options with the same metrics. When evaluating two alternatives,
  prefer the one with the better downside protection, not just the highest
  average.

In executive terms, the question is not only "What is the average outcome?"
It is "Can the business still perform acceptably when the result lands in the
unfavorable part of the distribution?"

## Understanding the Calculation

For every trial, the calculator draws one value from each variable's selected
distribution. It combines those values into one complete input set, substitutes
that set into the expression, and evaluates the result.

Independent variables are sampled separately. For a correlated normal pair,
the calculator generates two normal samples with the requested means and
standard deviations while coupling their standardized random components to
produce the requested correlation. Other variables remain independently
sampled.

Conceptually, the calculation is:

```text
sample every input
    -> substitute the complete input set
    -> evaluate the expression
    -> collect a successful scalar result
    -> repeat for all trials
    -> histogram and summarize the outcomes
```

Each variable's values are paired by trial number. The first sampled value of
each variable belongs to trial 1, the second value of each belongs to trial 2,
and so on. This pairing is what makes a correlated pair meaningful.

## Example

Suppose a calculation estimates a result affected by inflation, interest, and
an independent demand factor:

```python
inflation * 1000 + interest * 500 + demand
```

Use:

| Variable | Distribution | Param 1 | Param 2 | Param 3 |
|---|---|---:|---:|---:|
| inflation | normal | 3 | 1 |  |
| interest | normal | 5 | 1.5 |  |
| demand | uniform | 40 | 80 |  |

Trials: 1000
Bin Count: 20
Correlated Variables: inflation, interest
Correlation: 0.65

The calculator samples inflation and interest as a positively correlated
normal pair. Demand is sampled independently and uniformly from 40 to 80.

The resulting histogram represents the simulated distribution of the complete
calculation, not the distribution of any one input. Compared with an
independent inflation/interest model, positive correlation will generally make
jointly high and jointly low input combinations more common, which can change
the spread and tail of the result.

## Important Assumptions and Interpretation

- Independent sampling is the default. The calculator does not infer
  relationships from historical data.
- Only one correlated pair can be specified.
- The correlated pair must use normal distributions. Uniform, triangular, and
  lognormal variables can be used independently, but cannot currently be part
  of the correlated pair.
- A full correlation matrix is not supported. If several variables have
  relationships with one another, representing only one pair may understate or
  distort the uncertainty in the result.
- A positive correlation is not automatically economically or scientifically
  correct. Choose it from relevant data or treat it explicitly as a scenario
  assumption.
- The selected distributions and parameters are model assumptions. They do not
  forecast the future or establish the true probability of an outcome.
- Failed trials are excluded from the statistics. A high `trials_failed` count
  may indicate invalid ranges, an unsuitable expression, missing units, or
  parameters that make the calculation invalid.
- If all trials fail, the calculator cannot produce summary statistics.
- The output has the units and meaning of the expression's result. Input units
  must be expressed in a way accepted by the expression and qCalc's quantity
  system; this calculator does not independently convert or validate a unit
  model for the sampled variables.
- The histogram's **Frequency** values are counts of successful trials, not
  probability densities or percentages.