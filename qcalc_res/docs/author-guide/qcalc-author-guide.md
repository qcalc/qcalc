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
  * [5. The `__info()` meta dictionary](#5-the-__info-meta-dictionary)
    * [5.2 Dynamic `__info`](#52-dynamic-__info)
  * [6. Input value precedence (important)](#6-input-value-precedence-important)
  * [7. Optional hooks](#7-optional-hooks)
  * [7.1 `__input(_kwargs)`](#71-__input_kwargs)
  * [7.2 `__modify(arg_name, arg_value, action)`](#72-__modifyarg_name-arg_value-action)
  * [7.3 `__command(fkwargs, extra)`](#73-__commandfkwargs-extra)
  * [7.4 `__help()`](#74-__help)
  * [7.5 `__schema(request, kwargs)`](#75-__schemarequest-kwargs)
  * [7.6 Hooks at a glance](#76-hooks-at-a-glance)
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

For a calculator function named, `wall_paint`, metadata and hooks must use the same prefix, 
meta function declarations may also need some parameters as mentioned below (will be explained later):

- Main calculator: `wall_paint(...)`
- Meta definition: `wall_paint__info(optional:__info)` (mandatory)
- Optional hooks:
  - `wall_paint__input(kwargs)`
  - `wall_paint__modify(arg_name, arg_value, action)`
  - `wall_paint__command(kwargs, extra)`
  - `wall_paint__schema(request, kwargs)`
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

## 5. The `__info()` meta dictionary

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

For a side-by-side comparison of all the metadata functions, see [7.6 Hooks at a glance](#76-hooks-at-a-glance).

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

## 7.4 `__help()`

Use to provide custom help HTML for the calculator.

## 7.5 `__schema(request, kwargs)`

`__info()` is evaluated once and may be cached, so it cannot produce choices that depend on what the user selected. 
Use `__schema()` for that. It is called every time the form is built, and the dictionary it returns is merged over 
the matching `schema` entries of `__info()`.

```python
def conv2__info():
    return {
        'schema': {
            'quantity': {  # changing it reloads the calculator with the new quantity
                'type': 'choice', 'choices': _base_categ_mlist(), 'initial': 'L',
                'attrs': {'hx-get': '/catalog/ulist/', 'hx-target': 'closest .calc',
                          'hx-swap': 'outerHTML'},
            },
            'from_unit': {'type': 'multiplechoice', 'choices': lmt2ulist('L')},  # fallback
        },
    }


def conv2__schema(request, kwargs):
    # posted value when submitting, url value when loading
    lmt = request.POST.get('quantity') if request.method == 'POST' else kwargs.get('quantity', 'L')
    return {'from_unit': {'choices': lmt2ulist(lmt)}}
```

- `request` is the current request. `kwargs` holds the values given in the calculator url, 
e.g. `quantity` for `/calc/add/?path=conv2/quantity/M/`. Remembered input values are not part of `kwargs`.
- Return `{field_name: {property: value}}`. Only the returned properties replace those from `__info()`, 
so return only what changes (typically `choices`).
- When a submitted form is rebuilt for validation, `request.method` is `'POST'` and the selected value is in 
`request.POST`. Read it from there, otherwise a `choice` or `multiplechoice` field rejects the posted value.
- Pair it with `__input(kwargs)` to return default values that are valid for the new choices, because the 
function defaults or `__info()` initial values may not be among them.
- The `kwargs` values may be placeholders such as `-` or `--`, so validate the value and fall back to a default.

> **Reloading is not automatic yet (backend calculators only).** `__schema()` only runs when the form is built. 
Changing a field does not rebuild the form by itself. The `hx-get` attributes in the example above, and the 
`/catalog/ulist/` route they call, are specific to the built-in `conv2` unit converter: selecting a quantity opens 
the calculator again with that quantity in the url. A backend calculator can add its own `hx-*` attributes and route 
in the same way. Frontend calculator authors cannot add routes yet, so until a general mechanism is available they 
can use `__schema()` only when the value comes from the calculator url 
(for example from a link to `/calc/add/?path=<your_calculator>/<field>/<value>/`).

> **`related` or `__schema()`?** `related` runs in the browser and updates instantly, so use it for small fixed 
cascades (see [Calculator meta functions](calculator-meta-functions.md#42-related-dependent-selections)). 
`__schema()` runs on the server, supports large or computed choices and any widget type, and keeps the field's 
validation, but it needs the form to be rebuilt.

## 7.6 Hooks at a glance

Check this section before adding custom logic. It compares what each metadata function receives, when it runs, 
and what happens to what it returns. `__info()` is included for comparison.

**When it runs and what it receives**

| Hook | When it runs | Arguments | Data available | Extra data or command sent to it |
|---|---|---|---|---|
| `__info()` | Whenever calculator metadata is read: building the form, the catalog (title, description, tags) and the API. The form-related keys (`schema`, `autofill`, `related`, `showhide`, `anyof`, `fargs`, `script`) may be cached. | none | module-level code only | nothing |
| `__input(kwargs)` | Every time the form is built (first load and after a post), before remembered values are applied | `kwargs`: values given in the calculator url | url `kwargs`. On a post, `kwargs` is empty. The request is available only to backend calculators, through `QThread.get_req()`. | url `path/key/value/...` |
| `__schema(request, kwargs)` | Every time the form is built, after `__info()` and before the fields are created | `request`, `kwargs` | the request (`request.POST`, `request.method`, ...), url `kwargs`, the `__info()` schema | url `kwargs`, posted values in `request.POST` |
| `__modify(arg_name, arg_value, action)` | Only when a `callback_button(..., '__modify', ...)` is posted, once per field named in its `args` or `kwargs` | `arg_name`, `arg_value` (the posted value of that field, converted to the field's type), `action` (the text given for that field in `kwargs`) | that one field. Other posted fields only through the request (backend calculators). | `extra = {cmd, args, kwargs}` from the button |
| `__command(fkwargs, extra)` | Only when a `callback_button(..., '__command', ...)` is posted and the form is valid | `fkwargs`: all fields, validated, as the calculator function would receive them. `extra`: the button data. | all validated fields | `extra = {cmd, args, kwargs}` from the button |
| `__help()` | When the calculator's help is displayed | none | module-level code only | nothing |

**What it returns and how the return is used**

| Hook | Returns | What happens to the return | If it raises an error | Typical use |
|---|---|---|---|---|
| `__info()` | dictionary of info keys | Overrides the defaults of the form. `qfunc_info.json` overrides it in turn. Form-related keys are merged into the calculator's info. | metadata errors are mostly ignored when building the form; other readers may report them | titles, field types, static choices, layout |
| `__input()` | `{field: value}` | Replaces the default values of those fields. Remembered values, url values and posted values can still override them. | the form fails to build | defaults computed at run time |
| `__schema()` | `{field: {property: value}}` | Merged over that field's `schema` entry of `__info()` | the form fails to build | `choices` that depend on the request |
| `__modify()` | a new value, or `qinfo`, `qwarn` or `qerror` | A value replaces that field's value in the re-rendered form. A message object is shown and the posted value is kept. The form is not validated. | the error is logged and the posted value is kept | format or load a value |
| `__command()` | any output: text, dictionary, or `qinfo`, `qwarn`, `qerror` | Shown as the calculator's output. A message object, or text starting with `Error (` or `Warning (`, is shown as a message only. | shown as `Error (POSTP): ...` | validate, save, delete, other actions |
| `__help()` | HTML text | shown in the calculator's help area | not handled | dynamic help |

**What the hooks cannot do today**

- Only `__schema()` can change a field's `choices` (or other schema properties) for a request. `__info()` is static and the other hooks only change values.
- Only `__modify()` can set a field's value after a post, and only one field per call, and only for the fields listed on the button. It cannot set or reset other fields, or their choices.
- `__command()` returns output only. It cannot change the form, and it does not run if the form is not valid.
- `__input()` and `__modify()` do not receive the request. Backend calculators can get it with `QThread.get_req()`, which is not allowed in frontend calculators.
- No hook receives "field X changed" together with all current field values and returns new values and choices for several fields at once. Today this is done by reloading the calculator, as `conv2` does.

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


def mycalfunc__input(_kwargs):
    return {"x": "10 ft", "y": "2 ft"}


def mycalfunc__modify(arg_name, arg_value, action):
    if arg_name == "x" and action == "normalize":
        return str(Qty(arg_value).to("m"))
    return arg_value


def mycalfunc__command(fkwargs, extra):
    cmd = extra.get("args", [""])[0]
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
