# Define Next Step using `Step2` in `__info()` Function

This guide explains how to define `step2` inside a calculator metadata function (`<name>__info()`), so users can open a follow-up calculator with prefilled data.

---

## What Step2 Does

`step2` adds one or more Next Step buttons under calculation results.
When a step is clicked, qCalc opens another calculator (or action) using data from the source calculator's latest run.

Typical uses:

- Open another calculator with selected output values
- Open a chart editor from an output chart
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
- `source` (optional): where the data comes from. `input` reads the live form and the button appears before Calculate; `output` or `both` (default; `output` for `chart`) read the latest result and the button appears after Calculate
- `place` (optional): put the button in an insert slot such as `form_top`, `form_bottom` or `out_top` instead of the default position

Prefer the `step2_spec()` helper from `qutil`, which fills these keys:

```python
from qutil import step2_spec

'step2': [
    step2_spec(func='bmr', caption='Calculate BMR', spec={'weight': 'weight', 'height': 'height'}, source='input'),
]
```

To position a button between fields, declare a `btn:0` parameter and bind the step under the `button` key of its schema entry
(use `source='input'`, or the button works only after Calculate):

```python
def mycal(weight, show_bmr: 'btn:0' = 'Calculate BMR', height=170): ...

'schema': {'show_bmr': {'button': step2_spec('bmr', 'Calculate BMR', spec={'weight': 'weight'}, source='input')}},
```

The same `button` key binds a same-card action instead of opening another calculator. `action_spec(cmd, caption='', spec=None, args=None, kwargs=None, extra=None, sync_table=False, update_after_swap=False)` takes the command the calculator hooks receive, `spec` maps payload properties to field names, `args`/`kwargs` name the fields a `__modify` command changes, and `extra` holds literal values. It needs no script. For a custom layout, `action_button(func, caption, cmd, ...)` takes the same arguments and returns the button HTML for any insert slot of calculator `func`:

```python
def csv_editor(upload_csv: qfile = None, csv_table: qtable = ..., load: 'btn:0' = 'Load CSV'): ...

'schema': {'load': {'button': action_spec('load', spec={'from': 'upload_csv', 'to': 'csv_table'})}},
```

Field names are plain; no `@` prefix is needed (the prefix of a nested calculator is added automatically).

For custom layouts, `step2_button(func, caption, step, spec, source)` returns the button HTML for any insert slot.
Do not list the same step in `step2` and also place it by hand, or it appears twice.

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

---
