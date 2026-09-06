# Command Line

## Purpose

The qCalc Command Line lets you enter calculations, use qCalc calculators,
work with values that have units, and save your own temporary variables. Type
a command after the `>>` prompt and press **Enter** to see the result.

## Basic Calculations

Enter an arithmetic expression to calculate it:

```text
(2 + 3 * 5 - 12) / 3
```

You can also use qCalc values with units. qCalc accepts both a space and no
space between a number and its unit:

```text
3.5 m + 2.5 ft
3.5*m + 2.5*ft
```

## Unit Conversion

Use `to` to convert a value to another unit:

```text
3.5 m to ft
60 ft/s to m/s
```

Use `as` to display a value in one or more equivalent units:

```text
3.5 m as yd, ft, inch
```

## Using Calculators

Enter the name of a qCalc calculator followed by its input values. For
example:

```text
bmi(weight='60 kg')
```

Use `help` followed by a calculator or symbol name to see available details:

```text
help bmi
```

Use `find` with `*` or `?` to search qCalc symbols. For example:

```text
find bm*
```

## Variables

Assign a result to a variable when you want to use it again later in the
console:

```text
x = 60 ft/s
y = 35 m/s
x + y to m/s
```

Variables are kept for your console session. Enter `forget` to clear all
variables you have assigned.

## Commands

| Command | What it does |
| --- | --- |
| `?` or `help` | Shows console help. |
| `help name` or `?name` | Shows help for a qCalc calculator or symbol. |
| `find pattern` | Finds qCalc symbols matching a pattern; use `*` or `?` as wildcards. |
| `strict` | Shows whether strict assignment is enabled. |
| `strict on` / `strict off` | Turns protection of built-in qCalc names on or off. |
| `forget` | Clears variables assigned in the console. |
| `cls` or `clear` | Clears the displayed console screen. It does not clear assigned variables. |
| `qtypes()` | Lists qCalc calculator field types. |
| `qsymbols()` | Lists qCalc symbols. |
| `qmodules()` | Lists modules available in the command line. |

## Tips

Use the **Up Arrow** and **Down Arrow** keys to move through commands entered
earlier in the current open console. You can also select and copy text from
the console.

The command line is intended for calculations and qCalc functions. If a
command is not valid, qCalc displays the resulting error or message so you can
correct the entry and try again.