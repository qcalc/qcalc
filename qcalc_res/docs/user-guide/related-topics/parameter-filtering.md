# Parameter Filtering Specification

This guide explains how to use parameter specifications to select, filter, arrange, and exclude specific parameters or calculation outputs for display in tables, charts, and page layouts across qCalc.

---

## Overview

Parameter specifications allow you to selectively display a subset of inputs or calculated results. You can specify parameters using:

- **1-based positional indices** (e.g. `1`, `3`)
- **Positional index ranges** (e.g. `1-3`, `3-1`)
- **Parameter names** (case-insensitive, e.g. `cost_chart`, `Gold`)
- **Parameter name ranges** (e.g. `arg2-arg5`, `cost_chart-total_price`)
- **Mixed name and index ranges** (e.g. `2-cost_chart`, `cost_chart-5`)
- **Exclusions** using the `~` prefix (e.g. `~3`, `~vat_rate`)
- **Fractions / Proportions** (e.g. `0.5` selects the first 50% of items)
- **Wildcard** (`*`) to include all items
- **Table cells** (e.g. `Income Statement: Net Income`) when picking results from tabular output with `result_cells` (see section 7)

Specifications can be supplied as a comma-separated string (e.g. `"1-3, ~2"`), a list of strings (e.g. `["1-3", "~2"]`), or a numeric fraction.

---

## Specification Syntax & Rules

### 1. Wildcard & Default (`*` / `None`)
To include all available parameters or results, use `*` or leave the specification empty (`None`).

```yaml
# Selects all items
spec: "*"
```

---

### 2. Positional Selection (1-based Index)
Refer to parameters by their 1-based position in the input or output list.

| Specification | Description |
|---|---|
| `"1"` | Selects the 1st parameter |
| `"1, 3, 5"` | Selects the 1st, 3rd, and 5th parameters |
| `"1-3"` | Range: selects the 1st, 2nd, and 3rd parameters |
| `"3-1"` | Reverse range: selects the 3rd, 2nd, and 1st parameters in reverse order |

#### Example:
For parameters `[Width, Height, Depth, Weight, Price]`:
- `"1-3"` -> `[Width, Height, Depth]`
- `"3, 1"` -> `[Depth, Width]`

---

### 3. Name-Based Selection & Wildcard Matching
Parameter names can be matched flexibly:

- **Case-Insensitive**: `GOLD`, `Gold`, and `gold` all match the parameter `gold`.
- **Title Case & Display Names**: `Cost Chart` matches `cost_chart` or `cost_chart__r`.
- **Result Suffixes**: Names automatically resolve across result suffixes if any (e.g., `__r`).
- **Partial Pattern Matching (`*`)**: Use `*` anywhere within a string pattern to match parameter names (e.g. `agr*nt` matches `argument`, `*cost*` matches all cost columns).

| Specification | Target Parameter(s) | Result |
|---|---|---|
| `"cost_chart"` | `cost_chart__r` | Matched |
| `"Cost Chart"` | `cost_chart__r` | Matched |
| `"gold_value"` | `Gold Value` | Matched |
| `"agr*nt"` | `argument_1` | Matched |
| `"*cost*"` | `cost_chart`, `total_cost` | Matched |

---

### 4. Parameter Name Ranges
Ranges can be formed between parameter names, between positions, or mixing both.

| Specification | Description |
|---|---|
| `"arg2-arg5"` | Includes all parameters from `arg2` through `arg5` inclusive |
| `"cost_chart-total_price"` | Includes parameters from `cost_chart` to `total_price` inclusive |
| `"2-total_price"` | Starts at 2nd parameter and ends at `total_price` |
| `"Cost Chart-User Count"` | Range between Title Case names |

---

### 5. Exclusions (`~`)
Prefix any item, position, or range with `~` to exclude it from the final selection.

| Specification | Description |
|---|---|
| `"~3"` | Exclude the 3rd parameter |
| `"~vat_rate"` | Exclude the parameter `vat_rate` |
| `"~3-5"` | Exclude parameters in positions 3 through 5 |
| `"~cost_chart-total_price"` | Exclude range between `cost_chart` and `total_price` |

#### Combination Examples:
- `"1-5, ~3"` -> Selects positions 1, 2, 4, 5 (excluding 3).
- `"cost_chart-gold_value, ~vat_rate"` -> Selects all items from `cost_chart` to `gold_value`, excluding `vat_rate`.

---

### 6. Fractions & Proportions
Supply a numeric value between `0` and `1` (inclusive) to select a proportion of total parameters.

| Specification | Action |
|---|---|
| `0.5` | Selects the first 50% of parameters |
| `0.3` | Selects the first 30% of parameters |

---

### 7. Result Cells (Tabular Results)
Calculators like `redo`, `compare`, `monte_carlo` and `monte_carlo2` repeat an expression and tabulate its scalar results. When the expression returns tables (e.g. `finstate()`, which returns `Income Statement`, `Balance Sheet` and `Ratios`), use the **`result_cells`** argument to pick the table cells to treat as results. Without `result_cells`, tables are ignored.

#### Cell syntax
Each entry is `Table[: Row[: Column]]`, with entries separated by commas:

| Specification | Description |
|---|---|
| `"Income Statement: Net Income"` | One cell. The table has a single value column |
| `"Income Statement: EBIT"` | Row matched through another text column of the row (here an `Acronym` column) |
| `"Income Statement: Net Income: Period"` | Same cell with the value column spelled out |
| `"Ratios: *margin*"` | Wildcard over rows |
| `"Balance Sheet: 1-6"` | Rows 1 to 6 by position |
| `"Income Statement: ~Interest*"` | All rows except the matches |
| `"Ratios"` | Whole table |
| `"Income Statement: Sales, Ratios: ROE"` | Several cells |

Each part (table, row, column) follows the rules above: names (case-insensitive), 1-based positions, ranges, `*` wildcards and `~` exclusions.

- **Row matching**: a row is matched by any of its text columns, not just the first one. In an income statement both `Line Item` and `Acronym` work; in the `Stock` table below both `item` and `size` work. A name or wildcard selects every row sharing the value (e.g. all rows with size `large`). Row numbers always count the table's rows and never match text.
- **Value columns**: columns holding numbers, quantities or percentages. Text columns are used only to find rows. Percent text such as `8.28%` becomes the fraction `0.0828`. Blank rows are skipped.
- **Column names**: results are named `Table: Row`, or `Table: Row: Column` when the table has several value columns. Repeated row names get a ` (2)` suffix.
- **Commas**: a row label containing a comma (e.g. `Selling, General & Administrative Expenses`) cannot be typed in full. Use another text column of that row (here the acronym `SG&A`), a wildcard (`Selling*`) or its row number.
- **Limit**: the number of extracted cells is capped by the system range limit.

#### Worked examples
Suppose an expression returns a table named `Stock`:

| item | price | size | qty |
|---|---|---|---|
| sugar | 130 | medium | 13 |
| tea | 50 | large | 10 |
| condensed milk | 90 | large | 2 |
| milk | 80 | small | 5 |

`item` and `size` are text columns, used to find rows. `price` and `qty` are value columns, so each selected row produces one result per value column.

| `result_cells` | Results produced | Discussion |
|---|---|---|
| `Stock: milk` | `Stock: milk: price` = 80, `Stock: milk: qty` = 5 | An exact name matches only that row, so `condensed milk` is not included. Both value columns are taken. |
| `Stock: *milk*` | `condensed milk` and `milk`, each with `price` and `qty` (4 results) | The wildcard matches every row whose item contains "milk". |
| `Stock: milk: qty` | `Stock: milk: qty` = 5 | The third part restricts the result to one value column. |
| `Stock: *: qty` | `qty` of all four rows | `*` as the row part takes every row. |
| `Stock: large` | `tea` and `condensed milk`, each with `price` and `qty` | Names are matched against all text columns, so a category such as `size` selects every row sharing that value. |
| `Stock: large: price` | `Stock: tea: price` = 50, `Stock: condensed milk: price` = 90 | Category rows narrowed to one value column. |
| `Stock: ~large` | `sugar` and `milk`, each with `price` and `qty` | `~` takes every row except the `large` ones. |
| `Stock: 2` | `Stock: tea: price` = 50, `Stock: tea: qty` = 10 | A number is the row position (starting at 1), here the 2nd row. |
| `Stock: 1-2` | `sugar` and `tea`, each with `price` and `qty` | A range of row positions. |
| `Stock: milk: size` | nothing | `size` is a text column, not a value column, so it cannot be a result. |
| `Stock: 130` | nothing | `130` is read as a row position, and there is no 130th row. Values are never matched. |

Because `Stock` has two value columns, result names carry the column (`Stock: milk: qty`). A table with a single value column (such as `Period` in an income statement) gives shorter names (`Income Statement: Net Income`).

#### Combining with scalar results

The selected cells are appended to the expression's scalar results. `table_columns`, `table_units`, `chart_columns` and `chart_units` (and `histo_column` in Monte Carlo) then filter the combined set, using the cell names above. The other text columns of a row can be used there too, so `Income Statement: EBIT` selects the column that is displayed as `Income Statement: Earnings Before Interest and Taxes`:

```yaml
result_cells: "Break-Even Analysis: Variable Cost"

# Scalar plus all cell columns
table_columns: "contribution margin per unit, Break-Even Analysis: *"

# Everything except columns ending in "scenario"
table_columns: "~*scenario"
```

> **Note:** a filter with any positive item selects only the items it names, and `~` only removes from that selection. `"~*scenario, contribution margin per unit"` therefore shows just `contribution margin per unit`. Name the cell columns as well (`Table: *` selects all columns of a table), or use only `~` items to start from all columns.

In `redo` and `monte_carlo`, position 1 in a column filter is the varied variable, so cell and scalar positions start at 2. Names avoid this.

---

## Practical Examples for Visualizations & Layouts

### Example A: Filtering Table Columns
Given calculation outputs: `[Gold Weight, Gold Value, VAT on Gold, Making Charge, Grand Total]`

```yaml
# Display only Value, Making Charge, and Grand Total in the summary table
spec: "Gold Value, Making Charge, Grand Total"

# Or using exclusions to omit intermediate tax details:
spec: "1-5, ~VAT on Gold"
```

### Example B: Customizing Chart Series
Given parameters: `[Revenue, Cost of Goods, Gross Margin, Operating Expenses, Net Income]`

```yaml
# Select Revenue through Gross Margin, plus Net Income for the chart
spec: "Revenue-Gross Margin, Net Income"
```


---

## Summary Cheat Sheet

| Syntax | Example | Description |
|---|---|---|
| `*` | `"*"` | Select all parameters |
| Wildcard Pattern | `"agr*nt"`, `"*cost*"` | Partial pattern match parameter names |
| Index | `"1, 4"` | Select 1st and 4th parameters |
| Index Range | `"2-5"` | Select 2nd through 5th parameters |
| Name | `"Gold Value"` | Match parameter by exact or Title Case name |
| Name Range | `"arg2-arg5"` | Range between parameter names inclusive |
| Mixed Range | `"2-Gold Value"` | Range between 2nd position and `Gold Value` |
| Exclusion | `"~3"`, `"~VAT"` | Exclude specific position or name |
| Range Exclusion | `"~2-4"` | Exclude range of positions |
| Proportion | `0.6` | Select first 60% of parameters |
| Result cell | `"Income Statement: EBIT"` | `result_cells`: pick a table cell as a result (`Table: Row: Column`) |
| Whole table | `"Ratios"` | `result_cells`: every value cell of the table |
| Table wildcard | `"Ratios: *"` | In `table_columns`/`chart_columns`: all result columns from that table |
