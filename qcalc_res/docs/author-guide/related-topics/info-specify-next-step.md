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
        'spec': {
            'target_arg_1': 'source_field_1',
            'target_arg_2': 'source_field_2',
        }
    }
]
```

Each item commonly uses:

- `step`: action type (`run` or `chart`)
- `func`: target calculator for `run`
- `caption`: button text shown to user
- `spec`: mapping/filter details

---

## Step Type: run

Use `step: 'run'` to open another calculator and prefill inputs.

### A. Direct field-to-argument mapping

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

### B. Cost flow using run


```python
'step2': [
    {
        'step': 'run',
        'func': 'cost',
        'caption': 'Calculate Cost of Materials',
        'spec': {
            'exclude': ['Brick Work Volume']
        }
    }
]
```

For `func: 'cost'`, qCalc treats `spec.include` / `spec.exclude` as material-selection filters and prepares the `cost` calculator's `items` table automatically.

Supported patterns:

- `{'include': ['*'], 'exclude': ['Some Field']}`
- `{'exclude': ['Some Field']}`
- standard mapping if you explicitly provide `items` mapping

---

## Step Type: chart

Use `step: 'chart'` when output contains chart data and you want to open a chart function.

```python
'step2': [
    {
        'step': 'chart',
        'caption': 'Modify Chart',
        'spec': {'field': 'Chart'}
    }
]
```

`spec.field` must match the output field name that contains chart data.

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
        'spec': {'field': 'Chart'}
    }
]
```

---

## Common Mistakes

- Using `step: 'run'` without `func`
- Using wrong output/source field names in `spec`
- Expecting `spec.include`/`spec.exclude` to work for all target functions (they are meaningful for `func: 'cost'` flow)
- Misspelling `step2` key

---

## Quick Checklist

Before saving a step2 config:

- `step2` is a list
- each item has `step` and `caption`
- `run` steps include `func`
- `spec` field names match real input/output names
- if target is `cost`, use run-style with `func: 'cost'`

---
