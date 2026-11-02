# qCalc Author Guide: Creating Calculators
<!-- TOC -->
* [qCalc Author Guide: Creating Calculators](#qcalc-author-guide-creating-calculators)
  * [1. Where calculators live](#1-where-calculators-live)
    * [1.1 Backend calculators](#11-backend-calculators)
    * [1.2 Frontend calculators](#12-frontend-calculators)
  * [2. Calculator functions and naming convention](#2-calculator-functions-and-naming-convention)
    * [2.1 Calculator function](#21-calculator-function)
    * [2.2 Metadata functions](#22-metadata-functions)
  * [3. Minimal calculator example](#3-minimal-calculator-example)
  * [4. Understanding function arguments and UI generation](#4-understanding-function-arguments-and-ui-generation)
    * [4.1 Defaults define initial values](#41-defaults-define-initial-values)
    * [4.2 Type annotations influence field type](#42-type-annotations-influence-field-type)
  * [5. The `__info()` function](#5-the-__info-function)
  * [6. Input value precedence (important)](#6-input-value-precedence-important)
    * [6.1 First load and post](#61-first-load-and-post)
  * [7. Optional hooks](#7-optional-hooks)
  * [8. Working with quantities and units using `Qty()`](#8-working-with-quantities-and-units-using-qty)
  * [9. Form behavior patterns you can reuse](#9-form-behavior-patterns-you-can-reuse)
  * [10. Full template (copy/paste)](#10-full-template-copypaste)
  * [11. Common mistakes and fixes](#11-common-mistakes-and-fixes)
  * [12. Quick author checklist](#12-quick-author-checklist)
<!-- TOC -->
This guide explains how to create a calculator in qCalc using the same patterns and methods as those employed by built-in calculators. 

You can create qCalc `backend calculators` on a self-hosted qCalc Server. 
Both users and administrators can create `frontend calculators` within a running qCalc instance in a web browser. 

Developing calculators involves coding with the Python programming language. For standard calculators, you can leverage the full range of Python's flexibility and available modules for imports. In contrast, frontend calculators are developed using only a subset of Python modules, and are restricted to using specific qCalc functions for security and stability reasons.

## 1. Where calculators live

### 1.1 Backend calculators
`Backend calculators` are loaded from Python modules under:

- either `qcalc/calculators/all/...`
- or `qcalc/calculators/ext/...`
- or any other folder under `qcalc/calculators/...` if exists

The `all` folder contains the `standard` set of calculators that are included with qCalc. 
You can use the `ext` folders to extend the standard package or create any other sub-folder of `calculators` to house your calculators.

When qCalc starts up, it scans these folders recursively and registers the functions having an associated `__info()` function as calculator entries. More on `__info()` function will be discussed in the next section.

### 1.2 Frontend calculators
`Frontend calculators` are stored in the database, where the username serves as the package name. 

- **Private calculator**: User-created frontend calculators are by default `private calculators`. 
- **Public calculator**: An administrator has the ability to authorize users to create `public calculators` as well. Public calculators are accessible to anyone.
- **Shared calculator**: While only authorized users can create public calculators, any user can share their calculator with anyone. qCalc uses a security token to facilitate the sharing of calculators.

## 2. Calculator functions and naming convention

### 2.1 Calculator function
Calculator functions are written according to standard Python naming conventions. 
Depending on the source (who wrote them and where those are is kept), qCalc may adjust their names slightly during runtime.

| Type of calculator          | Author | Name user sees at the frontend        | Example             |
|-----------------------------|--------|---------------------------------------|---------------------|
| Backend Standard Calculator | qCalc  | `<Function name>`                     | `bmi`, `gold`, etc. |
| Backend User Calculator     | User   | `<Function name>-<package/folder name>` | `bmi-ext`           |
| Frontend User Calculator    | User   | `<Function name>-<username>`          | `bmi-dave`          |

### 2.2 Metadata functions

In addition to the main calculator function that performs the calculations and one mandatory metadata function named `__info()`, 
there are other optional metadata functions to assist the main function. 
All metadata function names start with the exact same name of the main function followed by a double underscored (`__`) suffix.
This also suggests that your main calculator should not have a double underscore (`__`) in its name, however single underscore (`_`) is fine.

- **__info()**: The `__info()` function is the calculator metadata hook. It is used by qCalc to identify a function as a calculator, 
define the calculator’s UI schema, and provide descriptive metadata such as the 
title, description, input fields, labels, choices, validation rules, help text, layout hints, 
and other form-related settings. In other words, this function tells qCalc how the calculator should appear and behave in the interface. 
It is essential for distinguishing calculator functions from ordinary Python functions and for building the interactive form that users see.

>For further details about the `__info()` metadata function, please see 
[Calculator meta functions](calculator-meta-functions.md)

- **__input()**: The `__input()` function is used to provide runtime default values for calculator inputs when 
the values are not simple static constants. While basic defaults can be supplied directly as function arguments 
or declared in the `__info()` metadata schema, `__input()` is useful when defaults must be computed dynamically 
based on context. In short, `__input()` acts as a dynamic initialization hook for user-facing form inputs when 
default values require logic rather than a fixed literal.

- **__modify()**: The `__modify()` function handles dynamic changes to the calculator form or input values 
_after_ the form has been created. This is distinct from `__input()`, which modifies the form _before_ it is created.
It is employed for updating a field in response to a request, such as reloading data, formatting values, 
or altering the form based on user actions or commands. In effect, it manages interactive UI behavior 
and allows the calculator to react to changes without reloading the whole page.

- **__command()**: The `__command()` function is used for custom command actions triggered by the interface, 
usually through buttons or special controls. These commands may perform operations such as validation, 
syntax checking, saving data, deleting entries, or executing auxiliary actions that are not the main calculation 
itself. It provides a clean way to support workflow actions around the calculator while keeping the actual 
computation logic separate.

- **__schema()**: The `__schema()` function overrides properties of the `schema` entries of `__info()`, 
typically the `choices` of a field, every time the form is built. Because `__info()` is evaluated once and may be cached, 
`__schema()` is the place for choices that depend on the request, e.g. units that depend on a selected quantity.

- **__help()**: The `__help()` function supplies help content or contextual guidance for the calculator.
This allows dynamic help content possible. This is different from static help file that can be associated with a calculator.

For a calculator function named, `wall_paint`, metadata and hooks must use the same prefix. 
The optional hooks are explained in the [Calculator hooks guide](calculator-hooks.md):

- Main calculator: `wall_paint(...)`
- Meta definition: `wall_paint__info()` (mandatory)
- Optional hooks (`ctx` is the read-only request context, see [the hooks guide](calculator-hooks.md#7-the-hook-context-ctx)):
  - `wall_paint__input(ctx)`
  - `wall_paint__schema(ctx)`
  - `wall_paint__modify(ctx, arg_name, arg_value, action)`
  - `wall_paint__command(ctx, func_kwargs)`
  - `wall_paint__help()`

## 3. Minimal calculator example

For a frontend calculator you can simply cut and paste the code into `mycal` to create it.

For a backend calculator, provided you are hosting your onw qCalc server, create a file under a suitable folder, for example:
- `qcalc/calculators/ext/estimation/slab_weight.py`
- add following import to the top: `from qcore import Qty`

```python
def slab_weight__info():
    return {
        "title": "Concrete Slab Weight",
        "desc": "Estimate slab self-weight from dimensions and density",
        "calculate": "Calculate",
    }

def slab_weight(length="10 ft", width="12 ft", thickness="5 in", density="2400 kg/m^3"):
    ql = Qty(length)
    qw = Qty(width)
    qt = Qty(thickness)
    qd = Qty(density)

    volume = ql * qw * qt
    weight = volume * qd

    # Convert outputs to readable units.
    return {
        "Volume": volume.to("m^3"),
        "Weight": weight.to("kg"),
    }
```

## 4. Understanding function arguments and UI generation

qCalc builds input fields from your function signature plus `__info()` metadata.

### 4.1 Defaults define initial values

Default argument values in `beam_load(...)` are the first source of initial input values.

### 4.2 Type annotations influence field type

You can use built-in Python types and qCalc annotations.

Common examples:
- `float`, `int`, `bool`
- `qtext`, `qtexta`, `qdate`, `qdatetime`, `qemail`
- `quom`, `quomx`, `quom2`
- `qtable`, `qlist[...]`, `qfunc`, `qhide`

Example:

```python
from qcore.mod_anno import qtexta, qtable, quomx
import pandas as pd


def sample_calc(value: qtexta = "42/7", unit: quomx = "ft", rows: qtable = pd.DataFrame()):
    ...
```

## 5. The `__info()` function

`__info()` returns a dictionary used to build form behavior and rendering.

Important keys include:
- `title`, `desc`, `calculate`
- `schema`: per-field properties (type, choices, attrs, validators, help_text, etc.)
- `autofill`, `related`, `showhide`, `anyof`
- Layout keys: `layout`, `inp1`, `out1`, `input_columns`, `output_columns`, `input_blocks`, `output_blocks`
- Frontend keys: `script`, `onsubmit`, `inserts`
- Flow keys: `step2`, `xpr`, `url`, `loop`, `cost`

For layout details, see:
- `related-topics/info-dynamic-layout.md` for preferred dynamic block/tab layout.
- `related-topics/info-specify-layout.md` for simple split layout (`inp1`/`out1`).

`__info()` takes no arguments and may be cached, so it is the place for static metadata only.
When choices, labels or mode-specific UI must be generated from the request, use `__schema(ctx)`
(see [`__schema(ctx)`](calculator-hooks.md#5-__schemactx)).

## 6. Input value precedence (important)

Effective input values are layered as follows:

1. Function defaults and `__info` initial
2. Internal: `qfunc_info.json` overlays
3. `__input()` overrides
4. Recalled/remembered values (if memory is enabled)
5. Saved variant, example or shared input, with the values given in the calculator url over it. A url value of `-` keeps the lower layers and `--` forces an empty value.
6. Posted form values

This is why `__input()` is best for dynamic defaulting, while posted values still win during form submission. 
Layers 1 to 5 only decide the values the form starts with. Layer 6 is applied last: a submitted form is bound to the 
posted values, so they replace whatever the lower layers produced. After a button post, only the fields the button 
modifies show the value returned by `__modify()`; the other fields keep their posted values.

Hooks can read the two kinds of values through the hook context (see [the hooks guide](calculator-hooks.md#7-the-hook-context-ctx)): 
`ctx.posted()` is layer 6 and `ctx.resolved()` is layers 1 to 5 merged, i.e. what the form starts with in this request.

### 6.1 First load and post

Not every request has every layer:

| Request | Remembered values (4) | Variant or url values (5) | Posted values (6) |
|---|---|---|---|
| First load from a catalog or `/calc/<name>/`, or add by name | yes | no | no |
| Add with values in the url (`path=name/field/value/`) | no | yes | no |
| Open from a variant, example or shared link | no | yes | no |
| Calculate, or a button post | yes | no | yes, the form is bound to them |
| Open a saved input file | no | yes, the values of the file | no |

* Memory is used when the calculator is opened by its name and not when it is opened with values in the url.
* On a post the url layer is empty (a post carries its values in the form), so `ctx.resolved()` of a post holds 
layers 1 to 4. The exception is opening a saved input file, which provides the values of the file as layer 5.
* A field that is not posted, such as a disabled field, takes its value from layers 1 to 4 on a post, not from the url 
value it showed on the first load.

## 7. Optional hooks

The optional hooks are described in the separate [Calculator hooks guide](calculator-hooks.md):

- [`__input(ctx)`](calculator-hooks.md#1-__inputctx): starting values of the fields, computed at run time
- [`__modify(ctx, arg_name, arg_value, action)`](calculator-hooks.md#2-__modifyctx-arg_name-arg_value-action): change a field value when a button asks for it
- [`__command(ctx, func_kwargs)`](calculator-hooks.md#3-__commandctx-func_kwargs): command like actions without the normal calculation
- [`__help()`](calculator-hooks.md#4-__help): help displayed in the calculator card
- [`__schema(ctx)`](calculator-hooks.md#5-__schemactx): choices and other field properties that depend on the request
- [Hooks at a glance](calculator-hooks.md#6-hooks-at-a-glance): when each hook runs, what it receives and what it returns
- [The hook context `ctx`](calculator-hooks.md#7-the-hook-context-ctx): the read-only request data passed to the hooks

## 8. Working with quantities and units using `Qty()`

qCalc calculators commonly accept quantity strings (for example `"5 ft"`, `"20 MPa"`, `"5 ft, 6 in"`).

Recommended pattern:

1. Normalize each input with `Qty(...)`
2. Compute using quantity arithmetic
3. Convert outputs with `.to(...)` before returning

```python
from qcore import Qty


def pressure_drop(length="20 m", gradient="150 Pa/m"):
    ql = Qty(length)
    qg = Qty(gradient)
    drop = ql * qg
    return {"Pressure Drop": drop.to("kPa")}
```

This keeps dimensional consistency and avoids unit mismatch errors.

## 9. Form behavior patterns you can reuse

Use demo calculators as references under `../../../qcalc/calculators/all/demo`:

- `dem_input.py`: field types and schema customization
- `dem_validate.py`: validators, required/readonly/disabled, autofill
- `dem_showhide.py`: conditional visibility via `showhide` and `script`
- `dem_related.py`: dependent fields via `related`, `autofill`, and `anyof`
- `dem_layout.py`: dynamic block and tab layout behavior
- `dem_test_layout.py`: legacy row/column layout behavior
- `calculator-field-naming.md`: field naming limits, token contracts, and safe naming rules

Also inspect production calculators for real Qty patterns, for example:
- `all/science/physics/cal_gas_law.py`
- `all/general/cal_conv.py`

## 10. Full template (copy/paste)

```python
from qcore import Qty
from qcore.mod_anno import qtexta


def mycalfunc__info(__info=None):
    return {
        "title": "My Calculator",
        "desc": "Describe what it computes",
        "calculate": "Calculate",
        "layout": "tb",
        "schema": {
            "x": {"help_text": "Input quantity"},
            "mode": {"type": "choice", "choices": ["A", "B"]},
        },
        "input_columns": 1,
        "input_blocks": [
            {
                "column": 1,
                "tabs": [
                    {"title": "Main", "fields": ["x", "mode", "y"]},
                    {"title": "Notes", "fields": ["notes"]},
                ],
            }
        ],
        "showhide": {
            "mode": {"fields": ["y"], "callback": "toggle_y"}
        },
        "script": """
        function toggle_y(v){
          return [v == 'A']
        }
        """,
    }


def mycalfunc__input(ctx):
    return {"x": "10 ft", "y": "2 ft"}


def mycalfunc__modify(ctx, arg_name, arg_value, action):
    if arg_name == "x" and action == "normalize":
        return str(Qty(arg_value).to("m"))
    return arg_value


def mycalfunc__command(ctx, func_kwargs):
    cmd = ctx.extra.get("args", [""])[0]
    if cmd == "check":
        return "Input looks valid"
    return "No action"


def mycalfunc(x="10 ft", y="2 ft", mode="A", notes: qtexta = ""):
    qx = Qty(x)
    qy = Qty(y)

    if mode == "A":
        result = qx + qy
    else:
        result = qx - qy

    return {
        "Result": result.to("ft"),
        "Notes": notes,
    }
```

## 11. Common mistakes and fixes

- Mistake: Prefix mismatch between `mycalfunc` and `mycalfunc__info`.
  - Fix: Keep exactly the same base name before `__...`.

- Mistake: Unknown meta suffix such as `mycalfunc__metadata`.
  - Fix: Only use known suffixes (`__info`, `__input`, `__modify`, `__command`, `__help`, `__schema`).

- Mistake: Returning unitless strings where a quantity is expected.
  - Fix: Normalize with `Qty(...)`, and return converted `Qty` values.

- Mistake: Show/hide callback returns wrong number of booleans.
  - Fix: Return one boolean per listed field in `showhide[field].fields`.

- Mistake: Expecting non-combined meta keys from introspection merge.
  - Fix: Put mergeable field-level behavior under keys in `COMBINE_FINF`.

## 12. Quick author checklist

- Create calculator file under the correct category package.
- Implement `mycalfunc(...)` with clear defaults.
- Add `mycalfunc__info()` with at least title and schema/layout as needed.
- Use `Qty()` at input normalization points and output conversion points.
- Add optional callbacks only when needed (`__input`, `__modify`, `__command`, `__schema`, `__help`).
- Verify calculator appears in catalog and renders expected form behavior.
- Run sample calculations with mixed units and edge cases.
