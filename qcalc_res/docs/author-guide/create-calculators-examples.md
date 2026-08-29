# Create Calculators - Learn by Examples

This companion document provides worked examples you can adapt directly to create qCalc calculators 
from within the front end using `mycal`.

Learning by example is often the quickest way to get started. You can study a working calculator, 
understand how its parts fit together, and then modify or combine the examples to create your own calculators.

## 1. Example 1: Dealing with quantities with `Qty()` or `q()`

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


## 2. Example 2: Normalize, calculate, and return quantities

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
    area = area_calc["Area"]
    p = Qty(pressure)
    force = area * p
    return {"Total Load": force.to("kN")}
```
* qCalc has a powerful feature that allows you to reuse the interface and calculations of another calculator.
* `area_calc` is a `qfunc` that allows you to assign another calculator, `circle`, to it. The `circle` calculator returns a result titled `"Area"`, and this quantity is assigned to `area` by the statement `area = area_calc["Area"]`.
* Run the calculator to see how the `circle` calculator's interface and the variables from this calculator are presented together on the screen.
* The circle's area will be calculated based on the input provided by the user on this screen.

## Final tips

- Keep your core function pure: normalize, calculate, return.
- Keep UI behavior in `__info` and other optional hooks.
- Prefer explicit output unit conversion.
