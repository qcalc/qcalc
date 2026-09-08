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
names listed in **Variables**.

The default expression is:

```python
x + y
```

For a multi-variable calculation, every variable that should be sampled must
be represented by its name in the expression. For example:

```python
inflation * principal + interest
```

### Variables

A comma-separated list of one or more unique variable names:

```text
inflation, interest, principal
```

Names must begin with a letter or underscore and may contain letters, numbers,
and underscores. The order of this list establishes the order used by
**Distributions**, **Param1s**, **Param2s**, and **Param3s**.

### Distributions

A comma-separated distribution name for each variable. The supported choices
are:

- `normal` — uses a mean and standard deviation.
- `uniform` — samples equally between a low and high value.
- `triangular` — uses a low value, high value, and most-likely mode.
- `lognormal` — samples a positive, right-skewed quantity using the parameters
  of an underlying normal distribution.

The number and order of distributions must match **Variables**.

### Param1s and Param2s

These are comma-separated numeric lists. Each position corresponds to the same
position in **Variables** and **Distributions**.

| Distribution | Param1 | Param2 |
|--------------|--------|--------|
| `normal` | mean | standard deviation |
| `uniform` | low | high |
| `triangular` | low | high |
| `lognormal` | mu of the underlying normal distribution | sigma of the underlying normal distribution |

For example:

```text
Variables:     inflation, interest, demand
Distributions: normal,    normal,    uniform
Param1s:       3,          5,         80
Param2s:       1,          1.5,       120
```

The number of values in **Param1s** and **Param2s** must match the number of
variables. Standard deviations and lognormal sigma values cannot be negative.
Uniform and triangular low values cannot exceed their corresponding high
values.

### Param3s

An optional comma-separated list of triangular distribution modes. Its value
is used only for variables whose distribution is `triangular`; it is ignored
for the other distributions.

Use an empty entry for a non-triangular variable when positions need to be
preserved:

```text
Variables:     price, demand, duration
Distributions: triangular, normal, triangular
Param1s:       8, 100, 2
Param2s:       15, 20, 10
Param3s:       10, , 5
```

The mode must lie between the low and high values. A single Param3 value may
also be supplied; it is applied to every variable position, but it only affects
triangular distributions.

### Trials

The number of random trials to perform. Each trial samples every variable and
evaluates the expression once. More trials generally make the histogram and
percentiles more stable, but increase computation time. The configured qCalc
range limit applies.

### Bin Count

The number of bins used to group calculated outcomes in the histogram. More
bins show more detail but can make a small simulation look irregular; fewer
bins give a more compressed view.

### Round Off

The number of decimal places used to round each sampled input before it is
inserted into the expression. Rounding keeps the evaluated trial expressions
manageable and makes the sampled values consistent with the displayed
precision. It can introduce a small discretization, normally negligible for
ordinary Monte Carlo use.

### Correlated Variables

An optional comma-separated pair of variable names:

```text
inflation, interest
```

Both names must already appear in **Variables**. Leave this field blank when
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

```text
Variables:             inflation, interest, demand
Distributions:         normal, normal, uniform
Param1s:               3, 5, 40
Param2s:               1, 1.5, 80
Param3s:
Trials:                1000
Bin Count:             20
Correlated Variables:  inflation, interest
Correlation:           0.65
```

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
- Rounding sampled values before evaluation can create a small discretization,
  especially with very narrow distributions or very low precision. Use an
  appropriate **Round Off** value for the scale of the inputs.
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