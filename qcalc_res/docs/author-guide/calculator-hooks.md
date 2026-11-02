# Calculator Hooks Guide

<!-- TOC -->
* [Calculator Hooks Guide](#calculator-hooks-guide)
  * [1. `__input(ctx)`](#1-__inputctx)
  * [2. `__modify(ctx, arg_name, arg_value, action)`](#2-__modifyctx-arg_name-arg_value-action)
  * [3. `__command(ctx, func_kwargs)`](#3-__commandctx-func_kwargs)
  * [4. `__help()`](#4-__help)
  * [5. `__schema(ctx)`](#5-__schemactx)
  * [6. Hooks at a glance](#6-hooks-at-a-glance)
  * [7. The hook context `ctx`](#7-the-hook-context-ctx)
<!-- TOC -->

A calculator can have optional hook functions beside its main function and its mandatory `__info()` metadata function. 
The name of a hook is the name of the main function followed by a double underscore suffix, for example 
`wall_paint__input()` for the calculator `wall_paint()`. qCalc calls a hook at a fixed moment while it builds or 
posts the calculator form. Use a hook only when the calculator needs logic that a static `__info()` cannot express.

| Hook function | Signature | Purpose |
|---|---|---|
| [`__input()`](#1-__inputctx) | `__input(ctx)` | Starting values of the fields, computed at run time |
| [`__modify()`](#2-__modifyctx-arg_name-arg_value-action) | `__modify(ctx, arg_name, arg_value, action)` | Change the value of a field when a button asks for it |
| [`__command()`](#3-__commandctx-func_kwargs) | `__command(ctx, func_kwargs)` | Command like actions (validate, save, delete) without the normal calculation |
| [`__help()`](#4-__help) | `__help()` | Help displayed in the calculator card |
| [`__schema()`](#5-__schemactx) | `__schema(ctx)` | Field properties, typically choices, that depend on the request |

The hooks that run for a request (`__input`, `__schema`, `__modify`, `__command`) receive a read-only context `ctx` 
as their first argument, see [7. The hook context `ctx`](#7-the-hook-context-ctx). 
For a side-by-side comparison of all the metadata functions, see [6. Hooks at a glance](#6-hooks-at-a-glance).
How the starting values of a field are layered is explained in 
[Input value precedence](qcalc-author-guide.md#6-input-value-precedence-important). 
For the `__info()` function, see [Calculator meta functions](calculator-meta-functions.md).

## 1. `__input(ctx)`

Use to set or override initial values before render.

```python
def beam_load__input(ctx):
    return {"density": "2500 kg/m^3"}
```

`__input()` runs every time the form is built, which includes the form rebuilt for a post, but it only provides 
the values the form starts with. When the user submits the form (Calculate), the posted value of each field 
is what the calculator receives, so `__input()` has no effect on it. The same holds for a button post (`__modify`): 
the fields the user typed keep their posted values (see [2](#2-__modifyctx-arg_name-arg_value-action)).

A post differs from a first load in two ways:
- The values `__input()` returns are used only for fields that were not posted. A disabled field is not posted by the 
browser, so it takes the value `__input()` returns on that post. If the value is computed (random, current date, a 
lookup), the calculator receives the newly computed value, which may differ from the one the user saw.
- `ctx.is_post` is true and `ctx.posted()` holds the posted values, so `__input()` can base its result on them 
(for example with `reload`, where the dependent fields are reset to values that fit the new selection).

## 2. `__modify(ctx, arg_name, arg_value, action)`

Use to alter a specific field value when a custom `__modify` command is triggered from the UI.

```python
def beam_load__modify(ctx, arg_name, arg_value, action):
    if arg_name == "span" and action == "normalize":
        return str(Qty(arg_value).to("m"))
    return arg_value
```

`arg_value` is the posted value of that field converted to the field's type. To read another field as posted, 
use `ctx.posted("other_field")`.

After a `__modify` post, the form is rebuilt. The fields named in the button's `args` or `kwargs` show the value 
returned by `__modify`. The other fields show what the user had typed (text, numbers, checkboxes, choices, 
multiple selects and select2 fields). 

Note: A choice value that is no longer offered is dropped, and a `choice` or `radio` field whose value is no longer offered shows its first choice. Tables and file fields are not covered yet and show their default or remembered values.

## 3. `__command(ctx, func_kwargs)`

Use for command-like operations after post, without running the normal calculation path.
`func_kwargs` holds the validated field values as the calculator function would receive them.
The data of the button that sent the command is in `ctx.extra`.

```python
def beam_load__command(ctx, func_kwargs):
    if ctx.extra.get("args", [""])[0] == "syntax":
        return "OK"
    return "Unknown command"
```

## 4. `__help()`

Use it to provide custom HTML help for the calculator, displayed in the same card above the calculator. This differs from the backend calculator help, which is displayed in a separate card and provided through a Markdown or HTML file.

## 5. `__schema(ctx)`

`__info()` is evaluated once and may be cached, so it cannot produce dynamic choices that depend on what the user selected. 
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
    # the posted value when the form is submitted, else the value the form starts with
    lmt = ctx.posted('quantity') or ctx.resolved('quantity', 'L')
    return {'from_unit': {'choices': lmt2ulist(lmt)}}
```

- `ctx.resolved('quantity')` is the value the form starts with: the function default, the remembered value or the 
value given in the calculator url (e.g. `quantity` for `/calc/add/?path=conv2/quantity/M/`), merged in the order of 
[input value precedence](qcalc-author-guide.md#6-input-value-precedence-important). 
- Return `{field_name: {property: value}}`. Only the returned properties replace those from `__info()`, 
so return only what changes (typically `choices`).
- When a submitted form is rebuilt for validation, the selected value is available from `ctx.posted()`. 
Read it from there first, otherwise a `choice` or `multiplechoice` field rejects the posted value.
- Pair it with `__input(ctx)` to return default values that are valid for the new choices, because the 
function defaults or `__info()` initial values may not be among them.
- Validate the value and fall back to a default, the field may hold a value that is not offered.

> **Rebuilding the form when a field changes.** `__schema()` runs whenever the form is built, but changing a field 
does not build it again by itself. Add `reload` to the field that decides the choices 
(see [`reload`](calculator-meta-functions.md#45-reload-rebuild-the-form-when-a-field-changes)). The form is then 
rebuilt on the server, `__input()` and `__schema()` run again, and the listed dependent fields take the new 
defaults. See [which hooks are needed with `reload`](calculator-meta-functions.md#which-hooks-do-i-need-with-reload).

> **`related` or `__schema()`?** `related` runs in the browser and updates instantly, so use it for small fixed 
cascades (see [Calculator meta functions](calculator-meta-functions.md#42-related-dependent-selections)). 
`__schema()` runs on the server, supports large or computed choices and any widget type, and keeps the field's 
validation, but it needs the form to be rebuilt.

## 6. Hooks at a glance

Check this section before adding custom logic. It compares what each metadata function receives, when it runs, 
and what it returns. `__info()` is included for comparison.

**When it runs and what it receives**

| Hook function with arguments | When it runs | Arguments | Data available | Extra data or command sent to it |
|---|---|---|---|---|
| `__info()` | Whenever calculator metadata is read: building the form, the catalog (title, description, tags) and the API. The form-related keys (`schema`, `autofill`, `related`, `showhide`, `anyof`, `fargs`, `script`) may be cached. | none | module-level code only | nothing |
| `__input(ctx)` | Every time the form is built: on a first load or refresh, and again when a form is posted. It provides the starting values. Remembered, url and posted values are layered over them, in the order of [input value precedence](qcalc-author-guide.md#6-input-value-precedence-important), so posted values win. | `ctx` | `ctx.resolved()` (the starting values without the ones `__input()` returns), `ctx.var_url()` (empty on a post, except when a saved input file is opened), `ctx.recall`, `ctx.posted()` on a post | url `path/key/value/...` |
| `__schema(ctx)` | Every time the form is built, after `__info()` and before the fields are created | `ctx` | the same as `__input`; `ctx.posted()` holds the posted values when a form is submitted | url values, posted values |
| `__modify(ctx, arg_name, arg_value, action)` | Only when a `callback_button(..., '__modify', ...)` is posted, once per field named in its `args` or `kwargs` | `ctx`, `arg_name`, `arg_value` (the posted value of that field, converted to the field's type), `action` (the value given for that field in `kwargs`, text or dictionary) | that one field as a typed value, other fields as posted text through `ctx.posted()` | `ctx.extra = {cmd, args, kwargs}` from the button |
| `__command(ctx, func_kwargs)` | Only when a `callback_button(..., '__command', ...)` is posted and the form is valid | `ctx`, `func_kwargs`: all fields, validated, as the calculator function would receive them | all validated fields | `ctx.extra = {cmd, args, kwargs}` from the button |
| `__help()` | When the calculator's help is displayed | none | module-level code only | nothing |

**What it returns and how the return is used**

| <div style="width: 100px;">Hook function</div> | Returns | What happens to the return | If it raises an error | Typical use |
|---|---|---|---|---|
| `__info()` | dictionary of info keys | Overrides the defaults of the form. `qfunc_info.json` overrides it in turn. Form-related keys are merged into the calculator's info. | metadata errors are mostly ignored when building the form; other readers may report them | titles, field types, static choices, layout |
| `__input()` | `{field: value}` | Provides the starting values of those fields. Remembered values, url values and posted values override them, so on a post the calculator receives the posted values. Only a field that is not posted (a disabled field) takes the value returned on that post. | the form fails to build | defaults computed at run time |
| `__schema()` | `{field: {property: value}}` | Merged over that field's `schema` entry of `__info()` | the form fails to build | `choices` that depend on the request |
| `__modify()` | a new value, or `qinfo`, `qwarn` or `qerror` | A value replaces that field's value in the re-rendered form. A message object is shown and the posted value is kept. The form is not validated. | the error is logged and the posted value is kept | format or load a value |
| `__command()` | any output: text, dictionary, or `qinfo`, `qwarn`, `qerror` | Shown as the calculator's output. A message object, or text starting with `Error (` or `Warning (`, is shown as a message only. | shown as `Error (POSTP): ...` | validate, save, delete, other actions |
| `__help()` | HTML text | shown in the calculator's help area | not handled | dynamic help |

**What the hooks cannot do today**

- Only `__schema()` can change a field's `choices` (or other schema properties) for a request. `__info()` is static and the other hooks only change values.
- Only `__modify()` can set a field's value after a post, and only one field per call, and only for the fields listed on the button. It cannot set or reset other fields, or their choices.
- `__command()` returns output only. It cannot change the form, and it does not run if the form is not valid.
- Hooks do not receive the request or the session. `ctx` gives a read-only view of the data they need (see [7](#7-the-hook-context-ctx)). Backend calculators can still reach the request with `QThread.get_req()`, which is not allowed in frontend calculators.
- A schema `reload` list makes a field rebuild the form when it changes and resets the listed fields. No hook receives "field X changed" together with all current field values and returns new values for several fields at once, but `__input()` and `__schema()` run again on every rebuild and can compute them from `ctx`.

## 7. The hook context `ctx`

`ctx` is the first argument of `__input`, `__schema`, `__modify` and `__command`. It is read-only and holds only 
request level data, so it is safe for frontend calculators. Data that belongs to one hook call 
(`arg_name`, `arg_value`, `action`, `func_kwargs`) is passed as separate arguments.

Field values come from three sources: the posted form, the values the form starts with (`resolved`, layers 1 to 5 of 
[input value precedence](qcalc-author-guide.md#6-input-value-precedence-important) merged), and the saved variant or url values on their own (`var_url`, 
which is layer 5 only). Each source has the same two forms: 
`name(field, default=None)` returns one value, and `name_kwargs` returns a new dictionary of all its fields 
(changing the dictionary does not change `ctx`).

| Member | What it gives |
|---|---|
| `ctx.posted(name, default=None)`, `ctx.posted_kwargs` | The posted value of a field as received (text, never converted). The last one if the field was posted several times. Empty unless a form is submitted. |
| `ctx.posted_list(name)` | All posted values of a field as text, for example a multiple select. |
| `ctx.posted_as(name, type, default=None)` | The posted value converted to a type of the calculator function (`float`, `int`, `str`, `bool`, `qt` ...). The default is returned when the field was not posted (the first open of the form) or the value cannot be converted, for example an empty or invalid number. A quantity (`qt`, `qt2`, `qtx`) is joined from its value and unit inputs. |
| `ctx.value(name, type, default=None)` | The value the field has in this request, converted to `type`: the posted value when it converts, else the resolved value, else the default. A resolved value that is not text (a number, a quantity, a table) is returned as it is. Use it for formula fields, as the `demo_formula_field` and `demo_formula_qty` demos do. |
| `ctx.resolved(name, default=None)`, `ctx.resolved_kwargs` | The value each field starts with in this request: function defaults, `__info()` values, `__input()` values, remembered input and the variant or url values, merged in that order (a url `-` keeps the lower layers, `--` empties the field). Keyed by the argument names of the calculator function. Values keep their own type (a list, a table, `"5 ft"`), they are not always text. In `__input()` it does not yet contain the values `__input()` returns. A post has no url layer, see [first load and post](qcalc-author-guide.md#61-first-load-and-post). The default is used only when the calculator has no such field. |
| `ctx.var_url(name, default=None)`, `ctx.var_url_kwargs` | Only the values of a saved variant, example or shared input, with the values given in the calculator url over them. Empty on a post, except when a saved input file is opened. Use it to know that a value was asked for by the link, not remembered or defaulted. Values are not always text (for example a table). |
| `ctx.recall` | True when remembered input is being recalled, false for example after the Refresh button. |
| `ctx.is_post` | True when a form is being submitted. |
| `ctx.cmd` | The command of the request, for example `__modify`, `__command` or `run`. Empty for a normal submit. |
| `ctx.extra` | The data sent by a callback button: `{cmd, args, kwargs}`. `kwargs` maps a field name to its action. |
| `ctx.user`, `ctx.is_loggedin` | The user name (a session identifier for anonymous users) and whether the user is logged in. |
| `ctx.cid`, `ctx.func_id` | The id of this calculator card and the calculator name. |

- `ctx.posted()` and `ctx.posted_kwargs` return the text exactly as posted. Use `ctx.posted_as(name, type, default)` 
when you need a number or a quantity: an empty or invalid value gives the default instead of an error. The converted 
value of the field being modified is the `arg_value` argument of `__modify`, and `__command` receives validated, 
converted values in `func_kwargs`.
- Posted values are available only when a form is submitted, so check `ctx.is_post` where it matters.
- To get the value a field has in this request, use `ctx.value(name, type, default)`: it is the posted value when 
there is one, else the resolved value, converted to the type and checked, for example `ctx.value('width', float, 0.0)` 
or `ctx.value('mass1', qt)`. The same by hand: `ctx.posted('quantity') or ctx.resolved('quantity')`, which is what 
the `conv2` calculator does for a text field.
