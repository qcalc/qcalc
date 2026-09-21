# Configure Layout in `__info()`

This guide explains how to control calculator page layout from the metadata function `<name>__info()`.

QCalc can have 1 or 2 input sections, as well as 1 or 2 output sections.
Layout is controlled by a combination of keys:

- `layout`: overall page direction, left-input right-output (`lr`) or top-input bottom-output (`tb`)
- `inp1`: Keep selected inputs to section 1, rest to section 2
- `out1`: Keep selected outputs to section 1, rest to section 2

All of the above options are optional. The default `layout` is `lr` when not specified.
If `inp1` is not specified, it will simply place all fields in one section.
Similarly, if `out1` is not specified, all outputs will be placed in one section.

When there are two sections in the input or output area, they are presented side by side when the screen is wide enough; otherwise, they are stacked.

---

## 1. `layout`: overall layout preset

Set `layout` in `__info()` to choose a high-level arrangement.

```python
def sample__info():
    return {
        'title': 'Sample',
        'layout': 'tb',
    }
```

If omitted, qCalc defaults to:

```python
'layout': 'lr'
```

---


## 2. `inp1` and `out1`: filter for inputs and outputs

`inp1` and `out1` control which input and output fields are included in the 1st section.
If not specified, all fields are placed in the only section.

The suffix `1` designates the first section (or primary pane):

- `inp1`: fields for input section 1
- `out1`: fields for output section 1

Both accept either:

- a list specification (common)
- a CSS selector string (advanced)

### A. Default behavior

If omitted, qCalc uses all fields:

```python
'inp1': '*',
'out1': '*',
```

### B. Include specific inputs

Specify using comma-separated field names:

```python
'inp1': 'length, width, depth',
```

An array of field names is also acceptable:

```python
'inp1': ['length', 'width', 'depth'],
```

Only those input fields are shown in the 1st input section. The rest of the input fields are placed in a 2nd section.

### C. Include specific outputs

```python
'out1': 'volume, weight',
```

or

```python
'out1': ['volume', 'weight'],
```

Only those output fields are placed in the 1st output section. The rest (if any) move to the secondary output section.

---

## 3. Putting it together

Copy into `mycal` to quickly test layout behavior. Close any other calculator to see the 2-section layout in action:

```python
def layout_test__info():
    return {
        'title': 'Layout Test',
        'layout': 'tb',
        'inp1': ['x-y'],
        'out1': ['Sum'],
    }


def layout_test(x='7 ft', y='8 ft', z='2 in', density='2400 kg/m^3'):
    return {
        'Sum': x,
        'Density': density,
    }
```

This means:

* Overall layout: top-to-bottom (`tb`), with **2 sections** for both the input and output sections.
* Input fields: `x` and `y` are placed in **input section 1**; the remaining input fields are placed in **input section 2**.
* Output fields: `Sum` is placed in **output section 1**; `Density` is placed in **output section 2**.


---

## 4. Common mistakes

- key names `layout`, `inp1`, and `out1` are case-sensitive
- Using names in `inp1` that do not match function argument names
- Using names in `out1` that are not actual output field labels/keys

---
