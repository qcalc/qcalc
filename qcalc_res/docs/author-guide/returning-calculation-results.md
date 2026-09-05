# Returning Calculation Results in qCalc
<!-- TOC -->
* [Returning Calculation Results in qCalc](#returning-calculation-results-in-qcalc)
  * [Return parameter name](#return-parameter-name-)
  * [1. Returning a single value](#1-returning-a-single-value)
    * [Numbers](#numbers)
  * [2. Returning a quantity](#2-returning-a-quantity)
    * [Important](#important)
  * [3. Returning a string](#3-returning-a-string)
    * [Practical recommendation](#practical-recommendation)
  * [4. Returning a date or time](#4-returning-a-date-or-time)
  * [5. Returning HTML](#5-returning-html)
    * [`qhtml`](#qhtml)
  * [6. Returning `qvstr`](#6-returning-qvstr)
  * [7. Returning a `qpage`](#7-returning-a-qpage)
  * [8. Returning a Pandas DataFrame](#8-returning-a-pandas-dataframe)
    * [Important](#important-1)
* [9. Returning a list or tuple](#9-returning-a-list-or-tuple)
  * [A single-item list or tuple](#a-single-item-list-or-tuple)
  * [Multiple simple values](#multiple-simple-values)
    * [Example](#example)
  * [Multiple complex values](#multiple-complex-values)
* [10. Returning a dictionary](#10-returning-a-dictionary)
    * [Recommended use](#recommended-use)
* [11. Nested dictionaries](#11-nested-dictionaries)
* [12. Nested lists and tuples](#12-nested-lists-and-tuples)
* [13. Returning a qCalc table (`qtbl`)](#13-returning-a-qcalc-table-qtbl)
    * [Recommendation](#recommendation)
* [14. Returning a `QChart`](#14-returning-a-qchart)
* [15. Returning a `QMap`](#15-returning-a-qmap)
* [16. Returning a `QImage`](#16-returning-a-qimage)
* [17. Returning a set](#17-returning-a-set)
    * [Important](#important-2)
* [18. Boolean values](#18-boolean-values)
* [19. Choosing the appropriate return type](#19-choosing-the-appropriate-return-type)
* [21. Examples](#21-examples)
    * [Single result](#single-result)
    * [Quantity result](#quantity-result)
    * [Multiple named results](#multiple-named-results)
    * [Multiple values](#multiple-values)
    * [Table](#table)
    * [Named results containing quantities](#named-results-containing-quantities)
    * [Chart](#chart)
* [22. Recommended authoring principle](#22-recommended-authoring-principle)
<!-- TOC -->
A calculator function can return a single value, a quantity, a collection of values, a dictionary, a table, or one of qCalc's special output objects. qCalc automatically converts the returned value into the appropriate output format for display in the calculator result form.

The way a value is displayed depends on both its **Python type** and its **position within a returned structure**.

## Return parameter name 

The result field name is derived from the result name. For an unnamed single result, the default name is `result`.

Result parameter name is represented internally by the converted variable name and a suffix `__r`. 
For example if a return label is `Total Cost` the resulting output variable will be `total_cost__r`
As you see, name is in lowercase, space is converted to `_` and a suffix `__r` is added.

Similarly, if a chart label is 'Chart' it's corresponding output variable will be `chart__r`.

The quantity result receives the following internal fields:

* `<name>` — quantity value
* `<name>_uom` — unit of measurement

For example, a result named `Length` may internally become something similar to:

```text
length__r
length__r_uom
```


## 1. Returning a single value

The simplest calculator result is a single value:

```python
return 125
```

or:

```python
return 125.5
```

or:

```python
return "Hello"
```

qCalc displays the result as a read-only result field.

### Numbers

| Returned value | Result field              |
| -------------- | ------------------------- |
| `int`          | Formatted character field |
| `float`        | Formatted character field |

For example:

```python
return 1250
```

is displayed using qCalc's number formatting preferences.

Similarly:

```python
return 1250.5678
```

is formatted according to the user's qCalc preferences.

---

## 2. Returning a quantity

A qCalc quantity is displayed as a value together with its unit.

For example:

```python
return 25 * m
```

or another qCalc quantity object.

The result is split into two read-only fields:

```text
25        m
```

The numeric value and unit are formatted according to the user's preferences.


### Important

Returning a qCalc quantity is preferable to returning a numeric value and unit separately when the result represents a physical quantity.

For example:

```python
return 12.5 * m
```

is preferable to:

```python
return 12.5
```

when the result represents a length.

---

## 3. Returning a string

A short string is displayed as a read-only character field:

```python
return "Approved"
```

Long text is displayed as a text area.

Currently, qCalc uses a length of **more than 25 characters** as the threshold for long text.

For example:

```python
return "This is a relatively long explanation of the calculation."
```

is displayed as a text area rather than a single-line field.

### Practical recommendation

Use a normal string for short textual results and return longer explanatory text when the result is intended to be read as a block of text.

---

## 4. Returning a date or time

The following Python types are recognized:

```python
date
datetime
dt_time
QDateTime
```

They are displayed as read-only character fields.

Examples:

```python
return date.today()
```

```python
return datetime.now()
```

```python
return QDateTime(...)
```

Python `date` and `time` values are converted to ISO-formatted strings.

A `datetime` is formatted using a space between the date and time components.

---

## 5. Returning HTML

qCalc provides special HTML-oriented result types.

### `qhtml`

Returning a `qhtml` value causes qCalc to display it as HTML:

```python
return qhtml("<b>Calculation completed</b>")
```

The HTML is rendered rather than displayed as ordinary text.

Because this is considered rendered content rather than ordinary form data, qCalc treats the result as an HTML output.

---

## 6. Returning `qvstr`

A `qvstr` result is treated as HTML output:

```python
return qvstr(...)
```

It is therefore suitable when the calculator needs to return a value that qCalc should handle as rendered output rather than as an ordinary input field.

---

## 7. Returning a `qpage`

A `qpage` is intended for a page or block of explanatory text.

For example, a calculator can return a generated `qpage` containing formatted documentation or calculation details.

qCalc displays it as a rendered text block rather than as a normal result field.

The output is placed inside a `<pre>` element, so the page is treated as a block of text.

A `qpage` result also causes qCalc to disable normal result looping for that output.

---

## 8. Returning a Pandas DataFrame

A `pandas.DataFrame`, which can be used by backend calculator, is displayed as an HTML table. For a fronend calculator use 'qtbl' dict (section 13).

For example:

```python
return pd.DataFrame({
    "Year": [2024, 2025, 2026],
    "Value": [100, 125, 150],
})
```

qCalc converts the DataFrame into an HTML table and applies qCalc's table formatting.

The table is displayed as a table output rather than as individual form fields.

### Important

A DataFrame is therefore the preferred return type when the calculator produces **tabular results**.

For example:

```text
Year    Value
2024    100
2025    125
2026    150
```

rather than returning a collection of individual values.

---

# 9. Returning a list or tuple

Lists and tuples receive special processing.

The result depends on their length and contents.

## A single-item list or tuple

If the list or tuple contains only one item:

```python
return [125]
```

or:

```python
return (125,)
```

qCalc treats the item essentially as a single result.

It does **not** create a table merely because the result was returned as a list or tuple.

---

## Multiple simple values

If a list or tuple contains multiple values and **all values are one of the following types**:

* `float`
* `Qty`
* `int`
* `str`
* `bool`
* `date`
* `datetime`
* `dt_time`

qCalc displays the values as a **one-column table**.

For example:

```python
return [10, 20, 30, 40]
```

produces a table conceptually like:

| Result |
| -----: |
|     10 |
|     20 |
|     30 |
|     40 |

This is useful when a calculator produces a sequence of homogeneous values.

### Example

```python
return [12.5, 15.2, 18.7, 21.4]
```

is presented as a table rather than as four separate result fields.

---

## Multiple complex values

If a list or tuple contains values other than the simple types listed above, qCalc processes each item separately.

For example:

```python
return [10, 20, {"minimum": 5, "maximum": 25}]
```

is processed as individual results rather than as a one-column table.

Nested lists and tuples are processed recursively.

---

# 10. Returning a dictionary

A dictionary is particularly useful when a calculator has several named results.

For example:

```python
return {
    "Area": 125.5,
    "Perimeter": 48.2,
}
```

qCalc processes each dictionary item as a separate result.

Conceptually, the output becomes:

```text
Area        125.5
Perimeter    48.2
```

The dictionary key becomes part of the result name.

### Recommended use

Use a dictionary when the calculator produces **multiple logically named results**.

For example:

```python
return {
    "total": total,
    "average": average,
    "maximum": maximum,
}
```

is generally preferable to:

```python
return [total, average, maximum]
```

because the dictionary explicitly identifies each result.

---

# 11. Nested dictionaries

Dictionaries can contain other dictionaries.

For example:

```python
return {
    "Cost": {
        "Material": 500,
        "Labor": 250,
    },
    "Area": 125,
}
```

qCalc recursively processes the structure.

Nested names are combined to form the result name.

Conceptually:

```text
Cost Material    500
Cost Labor      250
Area             125
```

The exact field names generated internally are handled by qCalc.

This allows calculator authors to use nested dictionaries to organize related results.

---

# 12. Nested lists and tuples

Lists and tuples can also be nested.

For example:

```python
return [
    [10, 20],
    [30, 40],
]
```

qCalc recursively processes the structure and generates names based on the position of each item.

For multiple items, positional names are added to the parent name.

Therefore, nested collections should generally be used when the structure itself is meaningful.

If the intended result is actually a table, a `DataFrame` is usually clearer and more predictable.

---

# 13. Returning a qCalc table (`qtbl`)

qCalc also accepts a dictionary representing a table:

```python
return {
    "data": [
        [2024, 100],
        [2025, 125],
        [2026, 150],
    ],
    "columns": [
        "Year",
        "Value",
    ],
}
```

When a returned dictionary contains both:

```python
"data"
```

and:

```python
"columns"
```

qCalc interprets it as a **qCalc table (`qtbl`)**.

An optional:

```python
"index"
```

can also be supplied.

Conceptually:

| Year | Value |
| ---: | ----: |
| 2024 |   100 |
| 2025 |   125 |
| 2026 |   150 |

This is converted internally to a Pandas DataFrame and displayed as a table.

### Recommendation

Use a DataFrame when you already have a DataFrame.

Use the `data`/`columns` dictionary form when a calculator naturally produces table data without first creating a DataFrame.

---

# 14. Returning a `QChart`

A `QChart` result is displayed as a chart image.

For example:

```python
return my_chart
```

where `my_chart` is a `QChart`.

qCalc generates the chart image and embeds it into the result form.

The result is therefore presented as a **visual chart**, not as a normal form field.

Chart output also disables normal result looping for that result.

---

# 15. Returning a `QMap`

A `QMap` is handled in the same way as a `QChart`.

It is converted into a chart image and displayed in the result form.

Therefore:

```python
return my_map
```

produces visual output rather than an ordinary character field.

---

# 16. Returning a `QImage`

A `QImage` result is displayed as an image.

qCalc converts the image to PNG data and embeds it in the result form.

For example, a calculator can return a generated image:

```python
return my_image
```

and qCalc displays the image directly.

This is useful for calculators that generate:

* diagrams
* drawings
* plots
* graphical layouts
* other calculated images

---

# 17. Returning a set

A Python `set` is converted to a list before qCalc processes it.

For example:

```python
return {10, 20, 30}
```

is effectively processed as:

```python
return [10, 20, 30]
```

Consequently, if the resulting collection consists entirely of supported simple values, it may be displayed as a one-column table.

### Important

A Python set has no guaranteed meaningful ordering for presentation. Therefore, **do not use a set when the order of the displayed results matters**.

Use a list instead.

---

# 18. Boolean values

Boolean values are supported as simple result values:

```python
return True
```

or:

```python
return False
```

They can also occur inside lists or tuples.

For example:

```python
return [True, False, True]
```

qualifies as a collection of simple values and is therefore displayed as a one-column table.

---

# 19. Choosing the appropriate return type

As a general rule, calculator authors should choose the return structure according to the intended presentation.

| Calculator output                 | Recommended return                      |
| --------------------------------- | --------------------------------------- |
| One number                        | `int` / `float`                         |
| One physical quantity             | qCalc quantity                          |
| Short text                        | `str`                                   |
| Long text                         | `str`                                   |
| Date/time                         | `date`, `datetime`, `time`, `QDateTime` |
| Multiple named results            | `dict`                                  |
| Ordered sequence of simple values | `list` / `tuple`                        |
| Tabular data                      | `DataFrame`                             |
| Table data without a DataFrame    | `qtbl` (`data` + `columns`)             |
| Formatted HTML                    | `qhtml`                                 |
| Formatted text page               | `qpage`                                 |
| Chart                             | `QChart`                                |
| Map/plot                          | `QMap`                                  |
| Generated image                   | `QImage`                                |

---

# 21. Examples

### Single result

```python
def calculate():
    return 125.5
```

**Displayed as:** one read-only numeric result.

---

### Quantity result

```python
def calculate():
    return 25 * m
```

**Displayed as:** value + unit.

---

### Multiple named results

```python
def calculate():
    return {
        "Area": 125.5,
        "Perimeter": 48.2,
    }
```

**Displayed as:** two separate read-only result fields.

---

### Multiple values

```python
def calculate():
    return [10, 20, 30, 40]
```

**Displayed as:** one-column table.

---

### Table

```python
def calculate():
    return pd.DataFrame({
        "Length": [10, 20, 30],
        "Area": [100, 200, 300],
    })
```

**Displayed as:** HTML table.

---

### Named results containing quantities

```python
def calculate():
    return {
        "Width": 5 * m,
        "Height": 3 * m,
        "Area": 15 * m**2,
    }
```

**Displayed as:** three named quantity results, each with its value and unit.

---

### Chart

```python
def calculate():
    return my_chart
```

where `my_chart` is a `QChart`.

**Displayed as:** chart image.

---

# 22. Recommended authoring principle

The **return value is also a description of how the result should be presented**.

Use:

* a **scalar** for one result;
* a **dictionary** for several named results;
* a **list/tuple** for an ordered sequence;
* a **DataFrame or qtbl** for tabular data;
* qCalc's **special output classes** when the result is intended to be rendered as HTML, a page, chart, map, or image.

When the intended output is tabular, prefer a `DataFrame` (backend) or `qtbl` (frontend). When the results have meaningful names, prefer a dictionary so that those names are preserved in the result form.
