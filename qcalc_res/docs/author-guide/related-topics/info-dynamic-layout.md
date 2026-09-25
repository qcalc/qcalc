# Dynamic Layout Spec in __info()

Use this guide when you need explicit control over calculator layout using block and tab metadata.

This is the preferred layout model for new calculators.

## 1. Keys overview

Dynamic layout uses the following metadata keys:

- layout: page direction, lr (left-right) or tb (top-bottom)
- input_columns: number of input columns, 1 or 2
- output_columns: number of output columns, 1 or 2
- input_blocks: ordered block definitions for input form fields
- output_blocks: ordered block definitions for output fields

If input_blocks or output_blocks is present, qCalc uses the dynamic renderer.

## 2. Required block shape

input_blocks and output_blocks must be lists.

Each list item is a block dictionary.

Supported block shapes:

- Field block:

```python
{
    'column': 1,
    'fields': ['x', 'y', 'z'],
}
```

- Tab block:

```python
{
    'column': 1,
    'tabs': [
        {'title': 'Main', 'fields': ['x', 'y']},
        {'title': 'Advanced', 'fields': ['z']},
    ],
}
```

Do not pass a single dictionary as input_blocks. It must be a list of dictionaries.

## 3. Field selector syntax

fields supports the same field-spec syntax as other qCalc selectors:

- exact names: ['radius', 'height']
- wildcard names: ['strict_*', '*_decimal']
- all fields: ['*']
- ranges by argument order: ['x-y']

## 4. Minimal working examples

### 4.1 One-column tabbed input layout

```python
def mycalc__info():
    return {
        'title': 'My Calculator',
        'layout': 'tb',
        'input_columns': 1,
        'input_blocks': [
            {
                'column': 1,
                'tabs': [
                    {'title': 'General', 'fields': ['x', 'y']},
                    {'title': 'Advanced', 'fields': ['strict_*']},
                ],
            }
        ],
    }
```

### 4.2 Two-column mixed blocks

```python
def mycalc__info():
    return {
        'title': 'My Calculator',
        'layout': 'lr',
        'input_columns': 2,
        'input_blocks': [
            {'column': 1, 'fields': ['x', 'y']},
            {'column': 1, 'tabs': [
                {'title': 'Rates', 'fields': ['rate_*']},
                {'title': 'Limits', 'fields': ['min_*', 'max_*']},
            ]},
            {'column': 2, 'fields': ['notes']},
        ],
    }
```

### 4.3 Easy breakdown pattern

For layout-heavy calculators, this pattern keeps metadata readable:

1. Group related fields.
2. Turn groups into tabs.
3. Place tabs into a block list.
4. Set column count and layout direction.

```python
def user_prefs__info():
    # 1) Group fields by topic.
    general_fields = "theme, interactive, defa_currency, memory, execution_timeout"
    number_fields = "ignore_decimal_format, decimal, *_decimal, thousands_separator, exponent_*"
    chart_fields = "chart_*"

    # 2) Convert groups into tabs.
    tabs = [
        {"title": "General", "fields": general_fields},
        {"title": "Number", "fields": number_fields},
        {"title": "Chart", "fields": chart_fields},
    ]

    # 3) Build dynamic blocks. input_blocks must be a list of block dictionaries.
    input_blocks = [
        {
            "column": 1,
            "tabs": tabs,
        }
    ]

    # 4) Return normal __info metadata.
    return {
        "title": "User Preferences",
        "layout": "tb",
        "input_columns": 1,
        "input_blocks": input_blocks,
    }
```

## 5. Relationship with simple split layout and compatibility keys

You can still use these keys for simple split layout:

- layout
- inp1
- out1

For simple split behavior, see info-specify-layout.md.

## 6. Troubleshooting

If tabs or custom blocks do not appear:

- Verify input_blocks or output_blocks is a list, not a dictionary.
- Verify each block entry is a dictionary.
- Verify each tab has a title and non-empty fields list.
- Verify listed field names match argument names or output names.
- Verify you are using valid column values (1 or 2).
