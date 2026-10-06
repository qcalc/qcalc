# Financial Statements Comparison

## Purpose

`finstate2()` builds the same income statement, balance sheet, and ratio tables as [`finstate()`](finstate_help.md), but for several columns at once. Use it to compare:

- **periods** of one company, e.g. last year vs. this year, or
- **companies**, e.g. X vs. Y vs. Z, to compare financial health side by side.

The calculation is exactly that of `finstate()`; each input column is calculated independently and the results are placed side by side. See the [`finstate()` help](finstate_help.md) for the meaning of each input, statement line, and ratio.

## Inputs

### Inputs table

One row per line item and one column per period or company.

- Keep the **Line Item** labels unchanged. Their order may change, but a renamed, missing, duplicated, or extra row is rejected.
- Rename the value columns (e.g. `FY2024`, `Company X`) and add or remove columns with **Resize**. Names must be unique and cannot be blank, `Line Item`, `Acronym`, or `Metric`.
- Enter rates as **decimals**: `0.40` for 40%.
- A blank cell is treated as 0.

### Figures In

The unit and scale of the monetary figures (default `1000 USD`). Change the number or the currency as needed, e.g. `1000000 BDT`. For information only; it does not affect any calculation.

### Same Basis

When checked (default), the **Tax Rate**, **Interest Rate**, and **Period (Months)** of the first value column are used for every column; the values typed in the other columns for these three rows are ignored. Clear it to use each column's own values, e.g. when comparing companies in different tax or interest environments.

## Outputs

`Income Statement`, `Balance Sheet`, and `Ratios`, with the same rows as `finstate()` and one value column per input column. In Ratios, the group heading rows (Profitability, Returns, and so on) have blank value cells, and a ratio that is undefined for a column shows **n/a**.

The tables can be used with `result_cells` in `redo`, `compare`, and `monte_carlo`, e.g. `Ratios: ROE`.
