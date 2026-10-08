# Scalar and Unit-Aware Equation Solver

## Purpose

Use `equation_solver()` to solve a **single equation with one unknown**.

It supports:

- Plain scalar equations (numbers only), and
- Unit-aware equations (qCalc quantity/unit expressions), including automatic
  unit propagation when quantity context is present.

This is useful for engineering/science formulas where you may want either:

- direct numeric roots, or
- roots expressed in units.

## Inputs

### Left

Left-hand side expression of the equation.

Examples:

- `2*x + 3`
- `pi*radius^2`
- `P*V`

### Right

Right-hand side expression of the equation.

Examples:

- `0`
- `11`
- `area`
- `n*R*T`

### Known Values

Optional known values, one per row, in `name=value` format.

Examples:

- `area=100 sft`
- `y=23`
- `v=10 m/s`

Notes:

- `Right` must be provided; blank right side is not evaluated as a standalone expression.
- Provide enough known values so exactly one unknown remains unsolved.

### Result Unit

Optional target output unit for the solved unknown.

Examples:

- `ft`
- `inch`
- `kPa`

Important:

- `result_unit` works only when the solved result is unit-bearing.
- If the solved result is dimensionless, qCalc raises an explicit error instead
  of attaching a unit blindly.

### Units in Expression

Boolean switch (default: **off**).

- **Off**: tokens inside expressions are treated as symbols.
- **On**: known unit tokens embedded in expressions are treated as units.

Example:

- With this **on**, `12ft^2` in the equation is interpreted as a quantity.
- With this **off**, `ft` is treated as a symbol name.

## Outputs

### Unknown

The inferred unknown symbol name.

### Solutions

A result table containing all solved roots.

### Status

Current solve status is:

- `ok` for successful solve.

For invalid or unsolved cases, this calculator currently raises an error message
instead of returning alternate status labels.

### Solutions Found

Number of roots returned.

### Mode

Internal execution mode:

- `scalar` for numeric-only path
- `qty` for unit-aware path

## Examples

### Example 1: Scalar roots

- Left: `x^2+y`
- Right: `16`
- Known Values: `y=23`

Returns two imaginary roots for `x`.

### Example 2: Unit-aware circle radius

- Left: `pi*radius^2`
- Right: `area`
- Known Values: `area=100 sft`
- Result Unit: `inch`

Returns both `+radius` and `-radius` in inches.

### Example 3: Unit token inside expression

- Left: `pi*radius^2`
- Right: `12ft^2`
- Units in Expression: **on**

Interprets `ft` as a unit token and solves for `radius` (you can not use `r` as a symbol in this case because `r` is a qCalc unit)

## Error Behavior (Important)

- If qCalc cannot infer exactly one unknown, it reports interpreted symbols.
- If unit-like tokens are detected while **Units in Expression** is off, qCalc
  suggests enabling it.
- If `result_unit` is given without quantity context, qCalc reports that
  quantity context is required.
- Complex-valued results cannot be converted to quantity with `result_unit`.
