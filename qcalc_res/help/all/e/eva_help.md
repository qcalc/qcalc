# Simple Expression Evaluator

## Purpose

Use the Simple Expression Evaluator to run one or more qCalc expressions in a
single calculation. It is useful when you want to carry out several related
steps, reuse intermediate values, or display more than one result.

Enter your expressions in the code editor, then select **Calculate**. Select
**Format Code** to tidy the code in the editor before calculating it.

## Input

### Code

Enter one or more expressions, with each step on its own line when helpful.
You can use qCalc functions, numbers, arithmetic operators, and values with
units. Use `q(...)` to create a quantity from text containing a value and unit.

For example:

```text
x = q('5 ft') + q('3 m')
show(x.to('inch'))
```

## Displaying Results

Use `show(...)` to add a value to the calculator results. Use one `show(...)`
statement for each value you want to display.

```text
length = q('5 ft') + q('3 m')
show(length)
show(length.to('inch'))
```

The final expression is also displayed when it produces a value, even if you
do not use `show(...)`.

You may use `print(...)` for text output. Printed text appears in the
calculator's console output area, separately from values displayed by
`show(...)`.

## Example

This example adds two lengths, converts the result, then calculates a cost:

```text
length = q('5 ft') + q('3 m')
length = length.to('inch')
show(length)

price = q('75 usd/inch')
show(length * price)
```

The first displayed result is the combined length in inches. The second is the
cost calculated from that length and the specified price per inch.

## Choosing a Tool

Use the **Command Line** for short, interactive calculations, quick unit
conversions, and temporary variables entered one command at a time. Use this
evaluator when a calculation needs several steps and several displayed results
in one code entry.

Use **Create My Calculator** (`mycal`) when you want to save named calculator
code and reuse it later as a qCalc calculator. It also provides controls to
load, check, validate, format, and delete your saved calculator code.

## Important Interpretation

The evaluator runs the expressions entered for that calculation. Values shown
with `show(...)` are limited by qCalc's configured result limit; attempting to
show more values than that limit produces an error.

If qCalc cannot evaluate an entry, it displays an error message and, where
available, the line that caused it. Correct that line and calculate again.

qCalc checks entered expressions before running them and may reject expressions
that are not permitted. This calculator is intended for qCalc calculations and
expressions, not for unrestricted program execution.