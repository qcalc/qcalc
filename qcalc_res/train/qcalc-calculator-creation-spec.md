# qCalc Calculator Consolidated Spec


## 1) Scope and authority

This guide applies to:
- backend calculators discovered by qCalc loader,
- frontend constraints for `mycal()`-style calculators,
- AI-assisted draft/fix/review workflows.

If anything conflicts, use this precedence:
1. First determine if the calculator is to be written for frontend or backend, if in doubt ask.
2. qCalc runtime/enforced behavior
3. current qCalc documentation + source code
4. this consolidated guide

Normative terms:
- **MUST** mandatory
- **MUST NOT** prohibited
- **SHOULD** recommended
- **SHOULD NOT** generally avoid
- **MAY** optional

---

## 2) Authoritative references

- Author Guide: <https://github.com/qcalc/qcalc/blob/main/qcalc_res/docs/author-guide/qcalc-author-guide.md>
- Calculator Meta Functions: <https://github.com/qcalc/qcalc/blob/main/qcalc_res/docs/author-guide/calculator-meta-functions.md>
- Author Quick Start: <https://github.com/qcalc/qcalc/blob/main/qcalc_res/docs/author-guide/author-quick-start.md>
- Create Calculator Examples: <https://github.com/qcalc/qcalc/blob/main/qcalc_res/docs/author-guide/create-calculators-examples.md>
- Field Types: <https://github.com/qcalc/qcalc/blob/main/qcalc_res/docs/author-guide/related-topics/qcalc-field-types.md>
- Quantity Reference: <https://github.com/qcalc/qcalc/blob/main/qcalc_res/docs/author-guide/related-topics/quantity-reference.md>
- DotDict Notation: <https://github.com/qcalc/qcalc/blob/main/qcalc_res/docs/author-guide/related-topics/dot-dict-notation.md>
- Calculator source tree: <https://github.com/qcalc/qcalc/tree/main/qcalc/calculators/all>

---

## 3) Canonical calculator structure

A valid calculator normally has:
- a main function, and
- a matching `__info()` function.

```python
def slab_weight(...):
    ...

def slab_weight__info():
    ...
```

Rules:
- Base name must match across main function and hooks.
- Main function names should be snake_case.
- Main calculator name should not contain `__` (reserved for hooks).
- Recognized hooks: `__info`, `__input`, `__modify`, `__command`, `__help`.
- Invented hook names must not be used unless qCalc adds support.
- qCalc calculator discovery/registration relies on the `__info()` pair relationship.

---

## 4) Location, packaging, discovery

### 4.1 Frontend Calculators
- Frontend calculators are written using mycal() or mycal2() and stored in database or temporarily in cache (if not logged in).
- Frontend calculators use a limited safe set of functionalities as it is written within browser
- Do not import modules at module levels. Only importing inside function is allowed.
e.g. you do not ever require "from qcore import Qty" statement for frontend calculator.
- For tabular input and out put do not use `qtable` annotation, use `qtbl` instead. Within the body of the function do not use DataFrame. Instead use qdf() and related helper functions.
- Following functions and classes are globally exposed and do not require any import statement:

    Qty or q, QDateTime or qdt, DotDict or dd,
    datetime (for datetime.datetime), date (for datetime.date), time (for datetime.time),
    timedelta (for datetime.timedelta), timezone (for datetime.timezone), qx, qxi,

    is_qty, is_unit, base_units, base_dims, unit_desc, prefixes, unit2lmt,
    lmt_desc, str_type, read_unit, lmt2cat, lmt2ulist, lmt2qlist, find_unit, is_str_qty,
    minimum,
    table_columns_validator, require_columns, require_values_subset, require_unique_values,
    require_unique_pairs, require_complete_pair_grid, validate_value_columns_against_master,
    qformat_q, qformat_v, to_ucur,
    iif, joinx, css2floats, css2ints, css2values, css2strs, vals2css, css2set,
    np, qdf, qcol, qrow, qsum, qapply, qadd, qsub, qmul, qdiv, qto_values,
    qconvert, qbinary, qdf_demo_data,
    qtypes, qmodules, qsymbols, qsymstat, qsymhelp,
    QFile, qf2bio, dd_list,
    QImage, qf2img, nparray_to_bio,
    QChart, QGeo, QMap, SmartCalc,
    user_name, user_process, user_ip, local_ip,
    page_link, calurl, cal_link, command_button, addcal_button,
    today, now, spellnow,
    md2html, demo_url, is_debug, is_blank, normalize_name, to_float, pct2fraction, val2fraction,
    to_cast,
    to_bool, parameter_values, as_float, specified_args, preprocess_expression, time2float,
    variable_to_title, title_to_variable, replace_variables, replace_parameter_values,
    csv2qtbl, np2qtbl,

    QResults

### 4.2 Backend Calculators
- Backend calculators are typically under `qcalc/calculators/all/`.
- Backend Extendended set of calculators may be under `qcalc/calculators/ext/` or supported subtrees.
- Python module extension should be `.py`.
- Calculator must remain discoverable by qCalc recursive loader.
---

## 5) `__info()` metadata requirements

### 5.1 Core
- `__info()` must return qCalc-compatible metadata.
- `title` is strongly recommended.
- `desc` is recommended as it is the minimum info that helps user.
- Metadata must correspond to real calculator parameters/behavior.

### 5.2 Current top-level metadata keys

```text
title, desc, calculate, schema, autofill, related, showhide, anyof, images,
step2, kins, tags, script, onsubmit, inserts, template,
layout, input_columns, output_columns, input_blocks, output_blocks, inp1, out1, interactive, proper
```

`__info()` validation schema:

Use the following structural contract when generating `__info()` metadata:

```json
{
    "FIELD_SELECTOR_SCHEMA": {
        "anyOf": [
            {"type": "string"},
            {
                "type": "array",
                "items": {"type": "string"}
            }
        ]
    },
    "ANYOF_SCHEMA": {
        "type": "object",
        "additionalProperties": {
            "type": "object",
            "properties": {
                "fields": {"$ref": "#/$defs/FIELD_SELECTOR_SCHEMA"}
            },
            "required": ["fields"],
            "additionalProperties": true
        }
    },
    "AUTOFILL_SCHEMA": {
        "type": "object",
        "additionalProperties": {
            "type": "object",
            "properties": {
                "fields": {"$ref": "#/$defs/FIELD_SELECTOR_SCHEMA"},
                "autofill": {"type": "object", "additionalProperties": true}
            },
            "required": ["fields"],
            "additionalProperties": true
        }
    },
    "RELATED_SCHEMA": {
        "type": "object",
        "additionalProperties": {
            "type": "object",
            "properties": {
                "fields": {"type": "object", "additionalProperties": true},
                "relation": {"type": "object", "additionalProperties": true}
            },
            "required": ["fields"],
            "additionalProperties": true
        }
    },
    "SHOWHIDE_SCHEMA": {
        "type": "object",
        "additionalProperties": {
            "type": "object",
            "properties": {
                "fields": {"$ref": "#/$defs/FIELD_SELECTOR_SCHEMA"},
                "callback": {"type": "string"}
            },
            "required": ["fields"],
            "additionalProperties": true
        }
    },
    "TAB_SCHEMA": {
        "type": "object",
        "additionalProperties": false,
        "properties": {
            "title": {"type": "string"},
            "fields": {"$ref": "#/$defs/FIELD_SELECTOR_SCHEMA"}
        },
        "required": ["fields"]
    },
    "BLOCK_SCHEMA": {
        "type": "object",
        "additionalProperties": false,
        "properties": {
            "kind": {"type": "string", "enum": ["fields", "tabs"]},
            "column": {"type": "integer", "enum": [1, 2]},
            "fields": {"$ref": "#/$defs/FIELD_SELECTOR_SCHEMA"},
            "tabs": {"type": "array", "items": {"$ref": "#/$defs/TAB_SCHEMA"}}
        }
    },
    "INFO_SCHEMA": {
        "type": "object",
        "additionalProperties": false,
        "properties": {
            "title": {"type": "string"},
            "desc": {"type": "string"},
            "calculate": {"type": "string"},
            "schema": {
                "type": "object",
                "additionalProperties": {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string"}
                    },
                    "additionalProperties": true
                }
            },
            "interactive": {"type": "boolean"},
            "anyof": {"$ref": "#/$defs/ANYOF_SCHEMA"},
            "autofill": {"$ref": "#/$defs/AUTOFILL_SCHEMA"},
            "related": {"$ref": "#/$defs/RELATED_SCHEMA"},
            "showhide": {"$ref": "#/$defs/SHOWHIDE_SCHEMA"},
            "images": {"type": "object"},
            "layout": {"type": "string", "enum": ["lr", "tb"]},
            "inp1": {},
            "out1": {},
            "input_columns": {"type": "integer", "enum": [1, 2]},
            "output_columns": {"type": "integer", "enum": [1, 2]},
            "input_blocks": {"type": "array", "items": {"$ref": "#/$defs/BLOCK_SCHEMA"}},
            "output_blocks": {"type": "array", "items": {"$ref": "#/$defs/BLOCK_SCHEMA"}},
            "onsubmit": {"type": "string"},
            "script": {"type": "string"},
            "kins": {"type": "string"},
            "tags": {"type": "string"},
            "proper": {"type": "string"},
            "inserts": {"type": "object"}
        }
    }
}
```

Notes:
- `fields` in `anyof`, `autofill`, `showhide`, tab entries, and blocks uses the selector schema and can be a comma-separated string or an array of strings.
- `related.fields` is a mapping object, not a selector list.
- `input_columns` and `output_columns` are limited to `1` or `2`.


### 5.3 Field mapping and labels
- Schema field names should match function parameter names.
- qCalc can derive fields from signature/defaults/annotations.
- Do not add schema labels only to prettify snake_case names; add `label` only when wording must intentionally differ.

### 5.4 Dynamic metadata
- `__info(__info=None)` may be used for dynamic metadata generation in rare cases.

### 5.5 Structural validation constraints
- `fields` selectors in `anyof/autofill/showhide/tabs/blocks` may be comma-separated string or string array.
- `related.fields` is a mapping object (not selector list).
- `input_columns` and `output_columns`: `1` or `2`.
- `layout`: `lr` or `tb`.

---

## 6) Arguments, defaults, and types

- Inputs should be function parameters unless deliberately handled by supported hooks.
- Defaults should be sensible and runnable.
- Defaults must remain type-compatible with qCalc processing.

Representative supported types:

`qchar, qcode, qdate, qdatetime, qemail, qfile, qfl, qfunc, qhide, qhidex, qhtml, qimage, qin, qpage, qread, qsel2, qt, qt2, qtbl, qtc, qtc2, qtext, qtexta, qtime, qtx, qurl, float, int, bool, str, qtable (backend), qlist[...]`

Do not invent unsupported annotation types.

Common default-to-type inference examples:

| default | derived type |
|---|---|
| `10` | `int` |
| `10.5` | `float` |
| `True` | `bool` |
| `'30 ft'` | `qt2` |
| `'hello'` | `str` |
| `'2026-09-05'` | `qdate` |
| `'2026-09-05 14:30:00'` | `qdatetime` |
| `'09:30:00'` | `qtime` |
| `{'columns': [...], 'data': [...]}` | `qtbl` |
| `pd.DataFrame()` | `qtable` (backend) |

---

## 7) Quantities, currency, datetime

### 7.1 Qty as input

- Normalize quantity-like inputs with `Qty(...)`. Example: Qty(length, 'm'), explicit normalization to a specified unit is better, i.e. `Qty(length, 'm')` is better than `Qty(length)`
- Prefer quantity-aware arithmetic over stripping units.
- Preserve dimensional correctness.
- Convert result units explicitly when presentation unit is intended. Example: `area.to('sft')` or `Qty(area, 'sft')`
- Avoid hard-coded conversion factors when `Qty` can convert.

### 7.2 Qty as output

- When the calculator is intended to return a result in the same unit system or unit family as an input, the implementation MAY derive the output unit from the input quantity.

Example:

```python
volume.to(qcyl_size.uom)

to_cur = q_sales.uom[:3]
q_cogs = Qty(annual_cogs).to(f'{to_cur}/yr')
```
- Use `pct` (not `%`) for percentage units, e.g. `Qty(8, 'pct/yr')`.


### 7.3 Currency as input

Currency-bound `Qty` fields automatically receive qCalc's appropriate currency/multi-currency behavior. 
It is therefore fine to use any input unit e.g. `USD` in defaults 

### 7.4 Currency as output

Returned currency SHOULD be the one that user specified in first currency input.

Example:

```python
purchase_price='10000 USD'
unit_cost='50 USD/unit'
```

for first currency value if user change it to 'EUR'
We should preserve that currency in returned values.

```python
q_purchase_price = Qty(purchase_price)
to_cur = q_purchase_price.uom # preserve input currency
```

Then return values and intermediate conversions can use the `to_cur`, like below:

```python
Qty(starting_balance, to_cur)
Qty(investment_gain, to_cur)
Qty(investment_tax_amount, to_cur)
Qty(withdrawal_amount, f'{to_cur}/yr')
Qty(ending_balance, to_cur)
```

### 7.5 Date/Time as input
- Normalize date/time/datetime inputs with `QDateTime(...)`.

Example: 
```python
def cal_func(on_date='2026-09-05')
    q_on_date = QDateTime(on_date) # !important, normalize date input (like we normalize Qty)
    ...

def cal_func(on_date=datetime.date.today())
    q_on_date = QDateTime(on_date) # !important, normalize date input (like we normalize Qty)
    ...
```

### 7.6 Representative unit subset

For calculator drafting, prefer units from this compact representative subset when they fit the requirement. This subset is sourced from `qcore/qc_units_subset.py` and organized by qCalc LMT/dimension key:

```python
units_subset = {
    "0": ["unit", "ea", "pair", "dozen", "pct", "ppm"],  # unitless
    "T": ["s", "sec", "min", "h", "hr", "d", "wk", "mo", "yr", "manhr", "manday", "manmo", "manyr"],  # time and labour
    "L": ["mm", "cm", "m", "km", "inch", "ft", "yd", "mi", "nmi"],  # length
    "L2": ["m2", "sqft", "sqyd", "ha", "acre", "km2"],  # area
    "L3": ["ml", "L", "m3", "floz", "cup", "qt", "us_gal", "gal"],  # volume
    "M": ["kg", "g", "tonne", "lb", "oz", "us_ton", "uk_ton"],  # mass
    "LT-2": ["mps2", "fps2", "g0"],  # acceleration
    "LMT-2": ["N", "kN", "lbf", "kgf"],  # force
    "L2MT-2": ["J", "kJ", "cal", "kcal", "Btu", "Wh", "kWh"],  # energy
    "L2MT-3": ["W", "kW", "MW", "hp"],  # power
    "L-1MT-2": ["Pa", "kPa", "MPa", "bar", "atm", "psi", "torr", "mmHg"],  # pressure
    "P": ["rad", "deg", "rev"],  # angle
    "Θ": ["K", "degC", "degF", "degR"],  # temperature
    "C": ["USD", "EUR", "GBP", "INR", "CNY", "CAD", "AUD", "JPY"],  # currency
    "N": ["mol"],  # amount of substance
    "J": ["cd"],  # luminous intensity
    "S": ["sr"],  # solid angle
    "I": ["A"],  # electric current
    "TI": ["Clm"],  # electric charge
    "L2MT-3I-1": ["V"],  # electric potential
    "L2MT-3I-2": ["ohm"],  # resistance
    "L-2M-1T4I2": ["F"],  # capacitance
    "L2MT-2I-2": ["Hn"],  # inductance
    "L2MT-2I-1": ["Wb"],  # magnetic flux
    "MT-2I-1": ["Ts"],  # magnetic flux density
    "L-2M-1T3I2": ["Si"],  # conductance
}
```

Important:
- This is a preferred compact vocabulary, not the complete set of valid qCalc units.
- Use another unit from `qcore/qc_units.py` when the calculator requirement calls for it.
- Preserving exact unit spelling and case (`L`, `K`, `A`, `Pa`, `USD`, and so on) is recommended.
- Compound units may be formed from compatible units, for example `USD/yr`, `USD/unit`, `pct/yr`, `kg/m3`, and `m/s`.
- Do not invent a unit merely because it appears plausible; verify units outside this subset against the current qCalc unit catalog.

---


## 8 Calculation

### 8.1 Calculation style

- Main calculator function should own calculation + return.
- Reuse existing qCalc facilities where possible.
- Avoid unnecessary complexity.
- MAYY use pandas/DataFrames if you are creating backend calculator and when materially useful, otherwise it is recommended to use qdf() to convert frontend-safe table shape: `{'data': [...], 'columns': [...]}` (`qtbl` style) and then use related helper functions
- Before implementing potentially existing functionality, inspect similar calculators and qCalc APIs first.

Recommended flow:
1. receive inputs
2. normalize (`Qty` / `QDateTime`)
3. convert to numeric forms as needed
4. compute
5. assemble user-facing outputs
6. return with proper dimensions/units


### 8.2 Variable Name

Variable names describe the concept or quantity; units describe its dimensional and temporal basis.

For example use:

```text
rent='1000 USD/mo'
ownership_cost='1500 USD/yr'
withdrawal='30000 USD/yr'
income='5000 USD/mo'
interest='8 pct/yr'
```
rather than:

```text
monthly_rent
annual_ownership_cost
annual_withdrawal
monthly_income
annual_interest
```

This is particularly important in qCalc because units are user-selectable, 
so the variable name must remain valid regardless of which compatible unit the user chooses.

when a scalar value needs to be used you can use unit in variable name:

```
rent=Qty(rent, '1000 USD/mo')
monthly_rent = rent.val

weight_kg = weight.to('kg')

```
---

## 9 Returning results

When a calculator produces multiple named outputs, it SHOULD return a dictionary.

Example:

```python
return {
    "Volume": volume.to("m^3"),
    "Weight": weight.to("kg"),
}
```
- Return value must be qCalc-compatible.
- Prefer human-readable result keys.
- Keep physical outputs as `Qty` where semantics apply.
- Return tabular output using frontend-safe table shape: `{'data': [...], 'columns': [...]}` (`qtbl` style). This shape is compatible for both backend and frontend calculator.
A frontend-safe table can be returned as:

```python
{
    'data': [
        [2024, 100],
        [2025, 125],
    ],
    'columns': [
        'Year',
        'Value',
    ],
}
```
---

## 10 Dynamic behavior hooks

The following metadata hooks are recognized by qCalc. 

### `__info`

`<calculator>__info()` is mandatory.

It defines calculator metadata and, where applicable, the calculator UI schema and behavior.

### `__input`

`<calculator>__input(_kwargs)` MAY be implemented when calculator inputs require dynamic initialization or modification before form rendering.

### `__modify`

`<calculator>__modify(arg_name, arg_value, action)` MAY be implemented for dynamic modification of calculator inputs in response to UI actions.

### `__command`

`<calculator>__command(fkwargs, extra)` MAY be implemented for command-like operations associated with the calculator.

### `__help`

`<calculator>__help()` MAY be implemented to provide dynamic calculator help content.

A calculator MUST NOT invent metadata hook names.

---

## 11 Imports and runtime constraints

- BACKEND calculators may import modules available in backend environment.
- BACKEND calculators must use documented qCalc APIs for qCalc-specific behavior.
- FRONTEND calculator restrictions:
  - SHOULD NOT have module-level imports,
  - MAY have imports inside function body only (where supported),
  - CAN import only modules that are exposed ( `qmodules()` can list them).
- FRONTEND pre-exposed symbols/utility functions can be inspected via `qsymbols()` / `qsymbols('all')`.
- Do not import/call undocumented qCalc APIs.

---

## 12 Error handling and code quality

- Detect invalid or ambiguous mathematical conditions.
- Do not silently return invalid mathematical outputs.
- Error text should be clear.
- Preferred message format:
  - `Error (<3-char-id>): <message>` (e.g., `Error (COS): ...`)
  - or standardized qCalc helpers where project style requires.

Quality rules:
- Keep implementation readable and maintainable.
- Use simplest correct implementation.
- Comments should explain non-obvious math/qCalc-specific decisions.
- Prefer established conventions from similar calculators.

---

## 13 Validation and testing checklist

A robust calculator should pass:
1. syntax validation
2. import/module validation
3. discovery validation
4. `__info()` validation
5. metadata consistency checks
6. qCalc API checks
7. input validation
8. quantity/dimension checks
9. execution tests
10. expected-result tests
11. edge-case tests

Important edge cases (as applicable):
- division by zero
- zero quantity
- negative/nonsensical quantities

---

## 14 Business-calculator guidance

- Solve a real user decision/problem, not only a formula.
- Prefer meaningful outputs

---

## 15 DotDict (`dd`) usage

- `dd()` may be used for concise nested metadata:
- dot notation for structure,
- `dd()` for grouped values.
- `dd()` / DotDict allows nested metadata to be written using dot notation.

Example:

```python
def example__info():
    d = dd()
    d.title = 'Example Calculator'
    d.calculate = 'Calculate'
    d.schema.option = dd(
        type='choice',
        choices=['A', 'B'],
        initial='A',
    )
    d.tags = 'example, demo'
    return d
```

Schema values may also be generated by functions if they ultimately return valid qCalc metadata structures. Ensure final returned metadata remains valid qCalc metadata.

---

## 16 Layout guidance

layout/grouping metadata:
- `layout`
- `input_columns`, `output_columns`
- `input_blocks`, `output_blocks`
- `inp1`, `out1` 

---


## 17 AI generation requirements

AI generation should:
1. follow qCalc-specific rules (not just generic Python),
2. include mandatory `__info`,
3. preserve exact naming correspondence across hooks,
4. use documented APIs only,
5. use proper `Qty`/dimension handling,
6. preserve result-key conventions,
7. use existing calculators as references when helpful,
8. validate with validator + runtime tests.

Do not treat syntactically valid generic Python as automatically valid qCalc calculator code.

---

## 18 Minimal unit-aware pattern


```python
from qcore import Qty

def slab_weight__info():
    return {
        "title": "Concrete Slab Weight",
        "desc": "Estimate slab self-weight from dimensions and density",
        "calculate": "Calculate",
    }

def slab_weight(
    length="10 ft",
    width="12 ft",
    thickness="5 in",
    density="2400 kg/m^3",
):
    ql = Qty(length)
    qw = Qty(width)
    qt = Qty(thickness)
    qd = Qty(density)
    volume = ql * qw * qt
    weight = volume * qd
    return {
        "Volume": volume.to("m^3"),
        "Weight": weight.to("kg"),
    }
```

However a calculator can also be unit unaware (using numbers only) when makes sense.

---

## 19 Living-document and handoff rule

When qCalc evolves:
1. update this file,
2. mark obsolete conventions explicitly,
3. keep links current,
4. avoid duplicating full upstream documentation.

Suggested new-thread handoff:

> Read this consolidated qCalc calculator spec first. If any detail is ambiguous or seems stale, verify against current qCalc source and current author-guide docs before implementation.

---

## 20 Exceptions and anti-overfitting rules

- Unusual implementations are not automatically invalid only because they differ from common calculator patterns.
- Conversely, one unusual/legacy calculator pattern should not be generalized into a global rule.
- Canonical examples are illustrative; they do not force every calculator to share identical structure.
- Individual examples must not override general specification rules unless documented as explicit exceptions.
