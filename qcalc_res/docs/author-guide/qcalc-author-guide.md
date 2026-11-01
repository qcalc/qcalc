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
    * [5.2 Dynamic choices](#52-dynamic-choices)
  * [6. Input value precedence (important)](#6-input-value-precedence-important)
  * [7. Optional hooks](#7-optional-hooks)
  * [7.1 `__input(ctx)`](#71-__inputctx)
  * [7.2 `__modify(ctx, arg_name, arg_value, action)`](#72-__modifyctx-arg_name-arg_value-action)
  * [7.3 `__command(ctx, func_kwargs)`](#73-__commandctx-func_kwargs)
  * [7.4 `__help()`](#74-__help)
  * [7.5 `__schema(ctx)`](#75-__schemactx)
  * [7.6 Hooks at a glance](#76-hooks-at-a-glance)
  * [7.7 The hook context `ctx`](#77-the-hook-context-ctx)
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
- Meta definition: `wall_paint__info()` (mandatory)
- Optional hooks (`ctx` is the read-only request context, see [7.7](#77-the-hook-context-ctx)):
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


### 5.2 Dynamic choices

`__info()` takes no arguments and may be cached, so it is the place for static metadata only.
When choices, labels or mode-specific UI must be generated from the request, use `__schema(ctx)`
(see [7.5](#75-__schemactx)).

## 6. Input value precedence (important)

Effective input values are layered roughly as:

1. Function defaults and `__info` initial
2. `qfunc_info.json` overlays
3. `__input()` overrides
4. Recalled memory values (if enabled)
5. Saved variant, example or shared input, with the values given in the calculator url over it (`ctx.var_url()`, `ctx.var_url_kwargs`).
   A url value of `-` keeps the lower layers and `--` forces an empty value.
6. Posted form values

This is why `__input()` is best for dynamic defaulting, while posted values still win during form submission.

## 7. Optional hooks

The hooks that run for a request (`__input`, `__schema`, `__modify`, `__command`) receive a read-only context `ctx` 
as their first argument, see [7.7 The hook context `ctx`](#77-the-hook-context-ctx). 
For a side-by-side comparison of all the metadata functions, see [7.6 Hooks at a glance](#76-hooks-at-a-glance).

## 7.1 `__input(ctx)`

Use to set or override initial values before render.

```python
def beam_load__input(ctx):
    return {"density": "2500 kg/m^3"}
```

## 7.2 `__modify(ctx, arg_name, arg_value, action)`

Use to alter a specific field value when a custom `__modify` command is triggered from the UI.

```python
def beam_load__modify(ctx, arg_name, arg_value, action):
    if arg_name == "span" and action == "normalize":
        return str(Qty(arg_value).to("m"))
    return arg_value
```

`arg_value` is the posted value of that field converted to the field's type. To read another field as posted, 
use `ctx.posted("other_field")`.

After a `__modify` post the form is rebuilt. The fields named in the button's `args` or `kwargs` show the value 
returned by `__modify`. The other fields show what the user had typed (text, numbers, checkboxes, choices, 
multiple selects and select2 fields). A choice value that is no longer offered is dropped, and a `choice` or `radio` 
field whose value is no longer offered shows its first choice. Tables and file fields are 
not covered yet and show their default or remembered values.

## 7.3 `__command(ctx, func_kwargs)`

Use for command-like operations after post, without running the normal calculation path.
`func_kwargs` holds the validated field values as the calculator function would receive them.
The data of the button that sent the command is in `ctx.extra`.

```python
def beam_load__command(ctx, func_kwargs):
    if ctx.extra.get("args", [""])[0] == "syntax":
        return "OK"
    return "Unknown command"
```

## 7.4 `__help()`

Use to provide custom help HTML for the calculator.

## 7.5 `__schema(ctx)`

`__info()` is evaluated once and may be cached, so it cannot produce choices that depend on what the user selected. 
Use `__schema()` for that. It is called every time the form is built, and the dictionary it returns is merged over 
the matching `schema` entries of `__info()`.

```python
def conv2__info():
    return {
        'schema': {
            'quantity': {  # changing it rebuilds the form, the fields in reload follow the new quantity
                'type': 'choice', 'choices': _base_categ_mlist(), 'initial': 'L',
                'reload': ['from_unit', 'to_units'],
            },
            'from_unit': {'type': 'multiplechoice', 'choices': lmt2ulist('L')},  # fallback
        },
    }


def conv2__schema(ctx):
    # posted value when submitting, url value when loading
    lmt = ctx.posted('quantity') if ctx.is_post else ctx.var_url('quantity', 'L')
    return {'from_unit': {'choices': lmt2ulist(lmt)}}
```

- `ctx.var_url('quantity')` returns a value given in the calculator url, 
e.g. `quantity` for `/calc/add/?path=conv2/quantity/M/`. Remembered input values are available with `ctx.remembered()`.
- Return `{field_name: {property: value}}`. Only the returned properties replace those from `__info()`, 
so return only what changes (typically `choices`).
- When a submitted form is rebuilt for validation, `ctx.is_post` is true and the selected value is available from 
`ctx.posted()`. Read it from there, otherwise a `choice` or `multiplechoice` field rejects the posted value.
- Pair it with `__input(ctx)` to return default values that are valid for the new choices, because the 
function defaults or `__info()` initial values may not be among them.
- The `ctx.var_url()` values may be placeholders such as `-` or `--`, so validate the value and fall back to a default.

> **Rebuilding the form when a field changes.** `__schema()` runs whenever the form is built, but changing a field 
does not build it again by itself. Add `reload` to the `schema` entry of the field that decides the choices 
(see [`reload`](calculator-meta-functions.md#45-reload-rebuild-the-form-when-a-field-changes)). The form is then 
rebuilt on the server, `__input()` and `__schema()` run again, and the listed dependent fields take the new 
defaults. This needs no url or `hx-*` attribute, so it works for frontend calculators too. 
See [which hooks are needed with `reload`](calculator-meta-functions.md#which-hooks-do-i-need-with-reload).

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
| `__input(ctx)` | Every time the form is built (first load and after a post), before remembered values are applied | `ctx` | `ctx.var_url()` (empty on a post), `ctx.remembered()`, `ctx.recall`, `ctx.posted()` on a post | url `path/key/value/...` |
| `__schema(ctx)` | Every time the form is built, after `__info()` and before the fields are created | `ctx` | the same as `__input`; `ctx.posted()` holds the posted values when a form is submitted | url values, posted values |
| `__modify(ctx, arg_name, arg_value, action)` | Only when a `callback_button(..., '__modify', ...)` is posted, once per field named in its `args` or `kwargs` | `ctx`, `arg_name`, `arg_value` (the posted value of that field, converted to the field's type), `action` (the value given for that field in `kwargs`, text or dictionary) | that one field as a typed value, other fields as posted text through `ctx.posted()` | `ctx.extra = {cmd, args, kwargs}` from the button |
| `__command(ctx, func_kwargs)` | Only when a `callback_button(..., '__command', ...)` is posted and the form is valid | `ctx`, `func_kwargs`: all fields, validated, as the calculator function would receive them | all validated fields | `ctx.extra = {cmd, args, kwargs}` from the button |
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
- Hooks do not receive the request or the session. `ctx` gives a read-only view of the data they need (see [7.7](#77-the-hook-context-ctx)). Backend calculators can still reach the request with `QThread.get_req()`, which is not allowed in frontend calculators.
- A schema `reload` list makes a field rebuild the form when it changes and resets the listed fields. No hook receives "field X changed" together with all current field values and returns new values for several fields at once, but `__input()` and `__schema()` run again on every rebuild and can compute them from `ctx`.

## 7.7 The hook context `ctx`

`ctx` is the first argument of `__input`, `__schema`, `__modify` and `__command`. It is read-only and holds only 
request level data, so it is safe for frontend calculators. Data that belongs to one hook call 
(`arg_name`, `arg_value`, `action`, `func_kwargs`) is passed as separate arguments.

Field values come from three sources: the calculator url (with a saved variant, example or shared input), 
the posted form, and the user's remembered input. Each source has the same two forms: 
`name(field, default=None)` returns one value, and `name_kwargs` returns a new dictionary of all its fields 
(changing the dictionary does not change `ctx`).

| Member | What it gives |
|---|---|
| `ctx.var_url(name, default=None)`, `ctx.var_url_kwargs` | Values of a saved variant, example or shared input, with the values given in the calculator url over them. Empty on a posted form. Values are not always text (for example a table). |
| `ctx.posted(name, default=None)`, `ctx.posted_kwargs` | The posted value of a field as received (text, never converted). The last one if the field was posted several times. Empty unless a form is submitted. |
| `ctx.posted_list(name)` | All posted values of a field as text, for example a multiple select. |
| `ctx.remembered(name, default=None)`, `ctx.remembered_kwargs` | The user's previous input of this calculator, as it was stored (not always text). Empty unless memory is being recalled. |
| `ctx.recall` | True when remembered input is being recalled, false for example after the Refresh button. |
| `ctx.is_post` | True when a form is being submitted. |
| `ctx.cmd` | The command of the request, for example `__modify`, `__command` or `run`. Empty for a normal submit. |
| `ctx.extra` | The data sent by a callback button: `{cmd, args, kwargs}`. `kwargs` maps a field name to its action. |
| `ctx.user`, `ctx.is_loggedin` | The user name (a session identifier for anonymous users) and whether the user is logged in. |
| `ctx.cid`, `ctx.func_id` | The id of this calculator card and the calculator name. |

- `ctx.posted()` and `ctx.posted_kwargs` return the text exactly as posted. The converted value of the field being 
modified is the `arg_value` argument of `__modify`, and `__command` receives validated, converted values in 
`func_kwargs`.
- Posted values are available only when a form is submitted, so check `ctx.is_post` where it matters.

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
