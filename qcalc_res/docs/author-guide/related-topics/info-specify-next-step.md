# Define Next Step using `Step2` in `__info()` Function

This guide explains how to define `step2` inside a calculator metadata function (`<name>__info()`), so users can open a follow-up calculator with prefilled data.

---

## What Step2 Does

`step2` adds one or more Next Step buttons under calculation results.
When a step is clicked, qCalc opens another calculator (or action) using data from the source calculator's latest run.

Typical uses:

- Open another calculator with selected output values
- Open a chart editor from an output chart
- Open cost calculation (`cost`) from material quantities (e.g. `brickwork`, `ccwork`)
- Open scenario analysis (`scenario`) from scenario comparison (`compare`)

---

## Step2 Structure

Use a list of step objects in `__info()`:

```python
'step2': [
    {
        'step': 'run',
        'func': 'target_function_name',
        'caption': 'Button Label',
        'spec': 'selector_or_mapping'
    }
]
```

Each item commonly uses:

- `step`: action type (`run` or `chart`)
- `func`: target calculator for `run`
- `caption`: button text shown to user
- `spec`: mapping/filter details (format depends on step)

---

## Step Type: run

Use `step: 'run'` to open another calculator and prefill inputs.

### A. Mapping mode (dict): destination arg → source field

```python
'step2': [
    {
        'step': 'run',
        'func': 'bmr',
        'caption': 'Calculate BMR',
        'spec': {
            'weight': 'weight',
            'height': 'height',
        }
    }
]
```

Meaning:

- target arg `weight` gets source value from field `weight`
- target arg `height` gets source value from field `height`

Use mapping mode whenever source field names differ from target argument names, for example:

```python
'spec': {
    'starting_price': 'Last Value',
    'volatility': 'Volatility',
    'drift': 'Drift',
}
```

### B. Selector mode (string/list): `specified_args()` syntax

For `step: 'run'`, selector mode picks source fields and auto-maps each picked field to an argument name using qCalc normalization (`title_to_variable`).

```python
'spec': 'weight,height'
```

This is convenient when source field names already match target argument names after normalization.

### C. Cost flow using run (`func: 'cost'`)


```python
'step2': [
    {
        'step': 'run',
        'func': 'cost',
        'caption': 'Calculate Cost of Materials',
        'spec': '~Brick Work Volume'
    }
]
```

For `func: 'cost'`, qCalc treats `spec` as a selector over output fields, then prepares the `cost` calculator's `items` table automatically from the selected Qty outputs.

Supported patterns:

- `'~Some Field'` (exclude one field)
- `'~Field A, ~Field B'` (exclude many fields)
- `'*'` or empty spec to include all output fields
- dict mapping still works if you explicitly provide `items` (for advanced/custom flows)

Selector mode uses `specified_args()` behavior, including:
- names (case-insensitive)
- wildcard patterns (`*`)
- indexes/ranges (`1`, `2-4`)
- exclusions (`~name`)

---

## Step Type: chart

Use `step: 'chart'` when output contains chart data and you want to open a chart function.

```python
'step2': [
    {
        'step': 'chart',
        'caption': 'Modify Chart',
        'spec': 'Chart'
    }
]
```

`spec` must select the output field that contains chart data.

Also supported (legacy-compatible form):

```python
'spec': {'field': 'Chart'}
```

---

## Multiple Step2 Buttons

You can add more than one step in order:

```python
'step2': [
    {
        'step': 'run',
        'func': 'scenario',
        'caption': 'Open Scenario Postprocessor',
        'spec': {'scenarios': 'table'}
    },
    {
        'step': 'chart',
        'caption': 'Modify Chart',
        'spec': 'Chart'
    }
]
```

---

## Common Mistakes

- Using `step: 'run'` without `func`
- Using wrong output/source field names in `spec`
- Using selector mode when you actually need explicit destination mapping (use dict mode instead)
- Expecting dict `include/exclude` keys to work (use selector syntax such as `~Field`)
- Misspelling `step2` key

---

## Quick Checklist

Before saving a step2 config:

- `step2` is a list
- each item has `step` and `caption`
- `run` steps include `func`
- `spec` matches intended mode:
  - dict for destination→source mapping
  - selector string/list for `specified_args()` style picking/filtering
- if target is `cost`, use run-style with `func: 'cost'`

---
