# What-If Scenario Comparison

## Purpose

**What-If Scenario Comparison** evaluates an expression for several input
scenarios and presents the results in a table and grouped bar chart.

## Inputs

### Expression

The expression or calculator call to evaluate for every populated value
column. The default is:

```python
x + y
```

### Vary By

Select what the discrete values vary:

- `Parameters` (`p`) replaces named parameter values inside a calculator or
  function call.
- `Variables` (`v`) replaces standalone variables in an expression, such as
  `x + y * z`.

Use `Parameters` for calculator or function arguments and `Variables` for
direct expression variables. The default for Compare is `Variables`.

### Input Table

Use exactly these input columns:

```text
Variable | V1 | V2 | V3
```

Enter one variable name per row in **Variable**, and enter its
value for each discrete case:

```text
Variable  | V1 | V2 | V3
x         |  1 |  2 |  3
y         |  2 |  3 |  4
z         |  3 |  4 |  5
```

This represents three evaluations: `V1` uses `x=1, y=2, z=3`, `V2` uses
`x=2, y=3, z=4`, and `V3` uses `x=3, y=4, z=5`. Parameter names must be
unique valid variable names. A value column may be entirely blank, but a
partially filled value column is invalid. Put any unit context in the
expression; table entries are the discrete values.

### Table Columns

Optional result columns to include in the output table. The input parameter
columns are included with the selected calculated result columns.

### Table Units

Optional result units to include in the output table. This is an alternative
to naming result columns explicitly. For example, enter `kg` to include all
calculated result columns whose unit is kilograms. Multiple units can be
separated by commas.

### Chart Columns

Optional result columns to display in the grouped bar chart. Each selected
result column becomes a bar series, with `V1`, `V2`, and `V3` as categories.

### Chart Units

Optional result units to include in the grouped bar chart. This is an
alternative to naming chart columns explicitly; for example, `USD` selects
all chartable result columns with that unit. Multiple units can be separated
by commas.

Column and unit filters can be used together. A result is included when it
matches one of the supplied column names or units.

### Show

Choose whether to display the table, chart, or both.

### Chart Title

The title displayed above the comparison chart.

## Results

The result table has one row per successfully evaluated value column. Its
first column, **Variation**, contains the corresponding input-table label
(`V1`, `V2`, or `V3`) so that each result row can be cross-checked directly
against the input. It then shows the input values for each variable followed
by the selected result columns.
The chart uses grouped vertical bars to compare the selected results across
the discrete cases.

If a case cannot be evaluated, that case is omitted. If no case produces a
numeric result, the calculator raises an error.

## Example

With **Vary By** set to `Variables`, evaluate:

```python
x + y * z
```

using the table above. The results are `7`, `14`, and `23` for `V1`, `V2`,
and `V3`.

## Interpretation

Compare is a deterministic discrete-case comparison. Use Redo for a generated
continuous range and Monte Carlo for randomly sampled uncertainty.