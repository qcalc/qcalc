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
- **Result Suffixes**: Names automatically resolve across result suffixes if any (e.g., `__r`, `__rf`, `__ri`, `__rq`).
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
Supply a numeric value between `0` and `1` (exclusive) to select a proportion of total parameters.

| Specification | Action |
|---|---|
| `0.5` | Selects the first 50% of parameters |
| `0.3` | Selects the first 30% of parameters |

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
