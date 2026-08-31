# Create Calculators - Learn by Examples
<!-- TOC -->
* [Create Calculators - Learn by Examples](#create-calculators---learn-by-examples)
  * [Example 1: Dealing with quantities with `Qty()` or `q()`](#example-1-dealing-with-quantities-with-qty-or-q)
  * [Example 2: Normalize, calculate, and return quantities](#example-2-normalize-calculate-and-return-quantities)
  * [Example 3: Input and output table, `qtbl` and `qdf()`](#example-3-input-and-output-table-qtbl-and-qdf)
  * [Example 4: Nested calculator, `qfunc`](#example-4-nested-calculator-qfunc)
  * [Example 5: Dynamic metadata with `__info`](#example-5-dynamic-metadata-with-__info)
  * [Example 6: Autofill fields from a `choice` selection](#example-6-autofill-fields-from-a-choice-selection)
  * [Final tips](#final-tips)
<!-- TOC -->
This companion document provides worked examples you can adapt directly to create qCalc calculators 
from within the front end using `mycal`.

Learning by example is often the quickest way to get started. You can study a working calculator, 
understand how its parts fit together, and then modify or combine the examples to create your own calculators.

## Example 1: Dealing with quantities with `Qty()` or `q()`

```python
def wall_area__info():
    return {
        'title': 'Wall area',
    }


def wall_area(width='12 ft', height='8 ft'):
    area_q = q(width) * q(height)
    return {'Area': area_q.to('ft^2')}
```
* You can use either `q()` or `Qty()` to convert a string into a quantity.
* `'Area': area_q.to('ft^2')` — The result is assigned the label `'Area'`.
* You can also simply return the value without a label: `area_q.to('ft^2')`. It will then be assigned the default label `'Result'`.


## Example 2: Normalize, calculate, and return quantities

```python
def rebar_weight__info():
    return {
        "title": "Rebar Weight",
        "calculate": "Estimate",
    }


def rebar_weight(diameter="12 mm", length="6 m", count=10,
                 steel_density="7850 kg/m^3"):
    
    diameter_q = q(diameter, "m")
    length_q = q(length, "m")
    density_q = q(steel_density, "kg/m^3")

    bar_area_q = pi / 4.0 * diameter_q * diameter_q  # m^2
    bar_weight_q = bar_area_q * length_q * density_q  # kg

    total_weight_q = bar_weight_q * count

    return {
        "Single Bar Weight": bar_weight_q.to("kg"),
        "Total Weight": total_weight_q.to("kg"),
    }
```
* Normalize all input quantities to known units.
* Base your calculations on normalized quantities.
* Return the results in the expected units.
* Change the **Calculate** button caption to **"Estimate"** using `"calculate": "Estimate"`.
* `count=10` (a number without a decimal point) makes the field an integer field. Try entering a fractional value—it will not be accepted.

## Example 3: Input and output table, `qtbl` and `qdf()`

```python
def item_costs__info():
    return {
        "title": "Item Cost Rollup",
    }


def item_costs(items: qtbl = {
    "columns": ["Item", "Quantity", "Unit Cost"],
    "data": [
        ["Brick", "3650 nos", "0.01 USD/nos"],
        ["Sand", "100 cft", "3.5 USD/cft"],
        ["Cement", "20 bag", "7.2 USD/bag"],
    ]
}):
    df = qdf(items)
    df["cost"] = qmul(df["Quantity"], df["Unit Cost"])
    total_cost = qsum(df["cost"])

    return {
        "Item Costs": df.to_dict(),
        "Total Cost": total_cost,
    }
```

* Use a dict with `"columns"` and `"data"` to represent an input data table using the `qtbl` annotation.
* `qdf()` provides safe and lightweight DataFrame-like functionality in Python.
* `.to_dict()` displays a table in the output.
* `qmul()` is a unit-aware function that multiplies two columns of quantities.
* `qsum()` is a unit-aware function that totals a column of quantities.


## Example 4: Nested calculator, `qfunc`

Reuse one calculator inside another.

```python
def total_load__info():
    return {"title": "Total Load on a circular area"}


def total_load(area_calc: qfunc = circle, pressure="5 kN/m^2"):
    area_q = area_calc["Area"]
    pr_q = q(pressure)
    force_q = area_q * pr_q
    return {"Total Load": force_q.to("kN")}
```
* qCalc has a powerful feature that allows you to reuse the interface and calculations of another calculator.
* `area_calc` is a `qfunc` that allows you to assign another calculator, `circle`, to it. The `circle` calculator returns a result titled `"Area"`, and this quantity is assigned to `area` by the statement `area = area_calc["Area"]`.
* Run the calculator to see how the `circle` calculator's interface and the variables from this calculator are presented together on the screen.
* The circle's area will be calculated based on the input provided by the user on this screen.

## Example 5: Dynamic metadata with `__info`

```python
def unit_converter__info(__info=None):
    category = (__info or 'length').lower()
    defa_from = {'length': 'm', 'weight': 'kg'}[category]
    defa_to = {'length': 'ft', 'weight': 'lb'}[category]
    return {
        'title': f'{category.title()} Unit Converter',
        'schema': {
            'value': {'initial': 10},
            'from_unit': {'initial': defa_from},
            'to_unit': {'initial': defa_to},
        },
    }


def unit_converter(value, from_unit, to_unit, __info: qhide = 'weight'):
    result_q = q(f"{value} {from_unit}")
    return {'Result': result_q.to(to_unit)}
```
* `__info__()` and the calculator itself can both accept an optional `__info` parameter—qCalc passes the currently selected mode into it.
* Here `category` drives `initial` value of `from_unit` and `to_unit`, so the same calculator serves length conversion and weight conversion depending on the mode qCalc is opened with.
* The calculator function can use the same `__info` value if it needs the mode during calculation.
* This pattern is handy whenever a single calculator should adapt its title, choices, or labels to a runtime-selected mode.

## Example 6: Autofill fields from a `choice` selection

```python
def wall_paint2__info():
    return {
        'title': 'Paint Required for a Wall v2',
        'calculate': 'Estimate',
        'schema': {
            'brand': {
                'type': 'choice',
                'choices': ['standard', 'premium'],
                'initial': 'standard',
            },
            'coverage': {'attrs': {'readonly': True}},
            'tin_size': {'attrs': {'readonly': True}},
            'coats': {
                'type': 'choice',
                'choices': [1, 2],
                'initial': 2,
            },
        },
        'autofill': {
            'brand': {
                'fields': ['coverage', 'tin_size'],
                'values': {
                    'standard': ['350', '1.0'],
                    'premium': ['600', '1.5'],
                },
            },
        },
        'tags': 'home, painting, estimation',
    }


def wall_paint2(
    width='12 ft',
    height='8 ft',
    brand='standard',
    coverage='350 sqft/gal',
    tin_size='1 gal',
    coats=2
):

    width_q = Qty(width, 'ft')
    height_q = Qty(height, 'ft')
    coverage_q = Qty(coverage, 'sqft/gal')
    tin_size_q = Qty(tin_size)

    area = width_q * height_q * int(coats)
    paint = area / coverage_q
    tins = paint / tin_size_q

    return {
        'Paint needed': Qty(paint, 'gal'),
        'Tins to buy': tins
    }
```
* `'autofill'` links the `brand` choice field to other fields (`coverage`, `tin_size`), filling them in automatically whenever the user picks a different brand.
* The `autofill` mapping under `brand` lists the target `fields` in order, then supplies one value list per `choices` key (`standard`, `premium`) matching that order.
* The user can not edit `coverage` or `tin_size`, it locks the field as `{'attrs': {'readonly': True}`.
* Use this pattern whenever picking one option (a brand, a material, a preset) should reasonably populate several related numeric or unit fields at once.

## Final tips

- Keep your core function pure: normalize, calculate, return.
- Keep UI behavior in `__info` and other optional hooks.
- Prefer explicit output unit conversion.
