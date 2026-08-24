# qCalc Author Guide: Creating Calculators

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

When qCalc starts up, it scans these folders recursively and registers the functions having an associated `__info()` function as calculator entries.
More on `__info()` function will be discussed in the next section.

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

- **__help()**: The `__help()` function supplies help content or contextual guidance for the calculator.
This allows dynamic help content possible. This is different from static help file that can be associated with a calculator.

For a calculator function named, `wall_paint`, metadata and hooks must use the same prefix, 
meta function declarations may also need some parameters as mentioned below (will be explained later):

- Main calculator: `wall_paint(...)`
- Meta definition: `wall_paint__info(optional:__info)` (mandatory)
- Optional hooks:
  - `wall_paint__input(kwargs)`
  - `wall_paint__modify(arg_name, arg_value, action)`
  - `wall_paint__command(kwargs, extra)`
  - `wall_paint__help(optional:__info)`

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

## 5. The `__info()` meta dictionary

`__info()` returns a dictionary used to build form behavior and rendering.

Important keys include:
- `title`, `desc`, `calculate`
- `schema`: per-field properties (type, choices, attrs, validators, help_text, etc.)
- `autofill`, `related`, `showhide`, `anyof`
- Layout keys: `row`, `col`, `newcol`, `endcol`, `newrow`, `inrowb`, `inrowe`, `endrow`, `outcol`
- Frontend keys: `script`, `onsubmit`, `inserts`
- Flow keys: `step2`, `xpr`, `url`, `loop`, `cost`, `table_in`, `table_out`


### 5.2 Dynamic `__info`

If you declare:

```python
def conv_like__info(__info=None):
    ...
```

qCalc can pass runtime context (`__info`) so your choices, labels, or mode-specific UI can be generated dynamically.

## 6. Input value precedence (important)

Effective input values are layered roughly as:

1. Function defaults and `__info` initial
2. `qfunc_info.json` overlays
3. `__input()` overrides
4. Recalled memory values (if enabled)
5. URL/kwargs overrides
6. Posted form values

This is why `__input()` is best for dynamic defaulting, while posted values still win during form submission.

## 7. Optional hooks

## 7.1 `__input(_kwargs)`

Use to set or override initial values before render.

```python
def beam_load__input(_kwargs):
    return {"density": "2500 kg/m^3"}
```

## 7.2 `__modify(arg_name, arg_value, action)`

Use to alter a specific field value when a custom `__modify` command is triggered from the UI.

```python
def beam_load__modify(arg_name, arg_value, action):
    if arg_name == "span" and action == "normalize":
        return str(Qty(arg_value).to("m"))
    return arg_value
```

## 7.3 `__command(fkwargs, extra)`

Use for command-like operations after post, without running the normal calculation path.

```python
def beam_load__command(fkwargs, extra):
    if extra.get("args", [""])[0] == "syntax":
        return "OK"
    return "Unknown command"
```

## 7.4 `__help(__info=None)`

Use to provide custom help HTML for the calculator.

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
- `dem_test_layout.py`: row/column layout behavior

Also inspect production calculators for real Qty patterns, for example:
- `all/science/physics/cal_gas_law.py`
- `all/general/cal_conv.py`

## 10. Full template (copy/paste)

```python
from qcore import Qty
from qcore.mod_anno import qtexta


def mycalc__info(__info=None):
    return {
        "title": "My Calculator",
        "desc": "Describe what it computes",
        "calculate": "Calculate",
        "schema": {
            "x": {"help_text": "Input quantity"},
            "mode": {"type": "choice", "choices": ["A", "B"]},
        },
        "showhide": {
            "mode": {"fields": ["y"], "callback": "toggle_y"}
        },
        "script": """
        function toggle_y(v){
          return [v == 'A']
        }
        """,
        "row": ["x-mode", "y"],
        "outcol": ["result"],
    }


def mycalc__input(_kwargs):
    return {"x": "10 ft", "y": "2 ft"}


def mycalc__modify(arg_name, arg_value, action):
    if arg_name == "x" and action == "normalize":
        return str(Qty(arg_value).to("m"))
    return arg_value


def mycalc__command(fkwargs, extra):
    cmd = extra.get("args", [""])[0]
    if cmd == "check":
        return "Input looks valid"
    return "No action"


def mycalc(x="10 ft", y="2 ft", mode="A", notes: qtexta = ""):
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

- Mistake: Prefix mismatch between `mycalc` and `mycalc__info`.
  - Fix: Keep exactly the same base name before `__...`.

- Mistake: Unknown meta suffix such as `mycalc__metadata`.
  - Fix: Only use known suffixes (`__info`, `__input`, `__modify`, `__command`, `__help`).

- Mistake: Returning unitless strings where a quantity is expected.
  - Fix: Normalize with `Qty(...)`, and return converted `Qty` values.

- Mistake: Show/hide callback returns wrong number of booleans.
  - Fix: Return one boolean per listed field in `showhide[field].fields`.

- Mistake: Expecting non-combined meta keys from introspection merge.
  - Fix: Put mergeable field-level behavior under keys in `COMBINE_FINF`.

## 12. Quick author checklist

- Create calculator file under the correct category package.
- Implement `mycalc(...)` with clear defaults.
- Add `mycalc__info()` with at least title and schema/layout as needed.
- Use `Qty()` at input normalization points and output conversion points.
- Add optional callbacks only when needed (`__input`, `__modify`, `__command`, `__help`).
- Verify calculator appears in catalog and renders expected form behavior.
- Run sample calculations with mixed units and edge cases.
