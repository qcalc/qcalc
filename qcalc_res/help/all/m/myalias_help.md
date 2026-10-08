# Manage My Calculator Aliases

## Purpose

Use `myalias()` to create and save your personal calculator aliases. An alias is
an alternate short name that **Add Calculator** can resolve to a real calculator
name.

This is useful when you want faster, custom naming for calculators you use often
(for example, mapping `mybmi` to `bmi`).

Aliases saved here are personal and are **not** used by expression evaluation.

## Input

`myalias()` takes one table input named **aliases** with two columns:

- **Alias**
- **Calculator**

You can add multiple rows. A row where both values are blank is ignored.

## Alias Rules

Each alias is normalized to lowercase and must follow all rules below:

- 1 to 32 characters
- must start with a letter (`a-z`)
- remaining characters can be letters, digits, or underscore (`_`)
- cannot match an existing calculator name

If a row has an invalid alias, save fails with an explicit error.

## Calculator Rules

The **Calculator** value must refer to an existing calculator. It is normalized
to lowercase and resolved against the calculator catalog.

If a calculator is missing or invalid, save fails with an explicit error.

## Save Behavior

Saving aliases **replaces your entire previously saved alias list**.

If duplicate aliases are entered, the last value wins before saving.

## Results

`myalias()` returns:

- **Saved Aliases**: number of aliases saved
- **Aliases**: normalized, saved alias table sorted by alias name

## Example

If you save:

| Alias | Calculator |
|---|---|
| `mybmi` | `bmi` |
| `solve` | `equation_solver` |

Then **Add Calculator** can use `mybmi` and `solve` as your personal shortcuts.
