# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

# Demo calculators that show how the optional hooks work. The hooks are explained in
# qcalc_res/docs/author-guide/calculator-hooks.md
#
#   demo_hooks_quote     __info, __input, __help, __modify, __command
#   demo_hooks_material  __info, __input, __schema, and a 'reload' trigger that makes the form follow a field

from datetime import date, datetime

from qcore import qinfo, qwarn, qerror
from qutil import callback_button, md2html

COVERAGE_SQFT_PER_GAL = 350


# ----------------------------------------------------------------------------------------------------------
# Demo 1: demo_hooks_quote
# ----------------------------------------------------------------------------------------------------------

def demo_hooks_quote__info():
    # __info() returns static metadata: titles, help texts, buttons. It is read when the calculator is listed
    # or built and its form related keys may be cached, so nothing that depends on the request belongs here.
    return {
        'title': 'Hooks demo: paint quote',
        'desc': 'Shows __info, __input, __help, __modify and __command working together.',
        'calculate': 'Quote',
        # | without this the date and name of the previous quote would be recalled and hide what __input() computes
        'remember': False,
        'schema': {
            'prepared_by': {
                'help_inline': 'Filled by __input() with the name of the logged in user, or "guest".'},
            'quote_date': {
                'help_inline': 'Filled by __input() with today\'s date. The default in the function signature is fixed.'},
            'width': {
                'help_inline': 'Feet. Swap width and height calls __modify() for this field and for the height.'},
            'height': {
                'help_inline': 'Feet. __modify() reads the posted width with ctx.posted() and returns it here.'},
            'coats': {
                'help_inline': 'Whole number. Check coats shows a message from __modify() and keeps this value.'},
            'price_per_gal': {
                'help_inline': 'Dollars per gallon. No hook touches it, a button keeps what you typed.'},
            'discount_pct': {
                'help_inline': 'Percent. The discount buttons set it with __modify(), the action tells which button.'},
        },
        'inserts': {
            # | a button posts one command to the calculator: '__modify' calls __modify() for each field it lists
            # | in args (or in kwargs, where the text is passed to the hook as `action`), '__command' calls __command()
            'form_bottom': (
                callback_button('demo_hooks_quote', 'Swap width and height', '__modify', args=['width', 'height']) +
                callback_button('demo_hooks_quote', 'Member discount', '__modify', kwargs={'discount_pct': 'member'}) +
                callback_button('demo_hooks_quote', 'Clear discount', '__modify', kwargs={'discount_pct': 'clear'}) +
                callback_button('demo_hooks_quote', 'Check coats', '__modify', kwargs={'coats': 'check'}) +
                callback_button('demo_hooks_quote', 'Check inputs', '__command', args=['check']) +
                callback_button('demo_hooks_quote', 'What do the hooks see?', '__command', args=['trace'])
            ),
        },
    }


def demo_hooks_quote__input(ctx):
    # __input(ctx) returns starting values for fields. Use it when a value cannot be a constant of the function
    # signature, because it depends on when or by whom the form is opened. The signature defaults below are
    # evaluated only once, when qCalc starts, __input() runs every time the form is built.
    # It only provides the starting values: whatever the user has typed or posted still wins.
    return {
        'quote_date': date.today().isoformat(),
        'prepared_by': ctx.user if ctx.is_loggedin else 'guest',
    }


def demo_hooks_quote__help():
    # __help() returns HTML that is shown in the calculator card. It runs whenever the help is displayed,
    # so it can contain values that change (here the time).
    return md2html(f'''
**How the hooks work in this calculator** (this text was created at {datetime.now():%H:%M:%S})

| Hook | What it does here |
|---|---|
| `__info()` | Gives the title and the buttons below the form. |
| `__input()` | Fills today's date and the name of the user. |
| `__modify()` | **Swap width and height**, **Member discount**, **Clear discount** and **Check coats** change or check a field. |
| `__command()` | **Check inputs** validates all the fields. **What do the hooks see?** lists the data a hook receives. |
| `__help()` | Created this text. |

Change a field and press a button: the fields you typed are kept, only the fields the button modifies change.
''')


def demo_hooks_quote__modify(ctx, arg_name, arg_value, action):
    # __modify(ctx, arg_name, arg_value, action) is called once for each field that the pressed button lists.
    #   arg_value  the posted value of that field, converted to the field type (a number here)
    #   action     the text the button gave for the field in its kwargs, '' if it was listed in args
    # Return the new value of the field, or a message (qinfo, qwarn, qerror) to show a message and keep the value.
    if arg_name in ('width', 'height'):  # the swap button lists both fields
        other = 'height' if arg_name == 'width' else 'width'
        try:
            return float(ctx.posted(other))  # ctx.posted() gives any other field as it was posted (text)
        except (TypeError, ValueError):
            return arg_value
    if arg_name == 'discount_pct':
        return {'member': 10.0, 'clear': 0.0}.get(action, arg_value)
    if arg_name == 'coats' and action == 'check':
        if arg_value > 3:
            return qwarn('More than 3 coats is rarely needed, the cost will be high.')
        return qinfo('The number of coats is fine.')
    return arg_value


def demo_hooks_quote__command(ctx, func_kwargs):
    # __command(ctx, func_kwargs) runs an action that is not the calculation. It is called only when the form
    # is valid. func_kwargs holds the validated values the calculator would receive, ctx.extra the button data.
    # What it returns is shown as the result: a message or the usual labelled values.
    action = ctx.extra['args'][0]
    if action == 'check':
        problems = []
        if func_kwargs['width'] <= 0 or func_kwargs['height'] <= 0:
            problems.append('width and height must be positive')
        if not 0 <= func_kwargs['discount_pct'] <= 100:
            problems.append('discount must be between 0 and 100')
        if problems:
            return qerror('Please fix: ' + '; '.join(problems) + '.')
        return qinfo('All inputs are valid, press Quote to calculate.')
    if action == 'trace':
        # | a table, so that the name of each member is shown as it is written in code
        return {
            'columns': ['Member', 'Value'],
            'data': [
                ['ctx.cmd', ctx.cmd],
                ['ctx.extra', str(ctx.extra)],
                ['ctx.posted_kwargs', ', '.join(f'{k}={v}' for k, v in ctx.posted_kwargs.items())],
                ['ctx.resolved_kwargs', ', '.join(f'{k}={v}' for k, v in ctx.resolved_kwargs.items())],
                ['func_kwargs', ', '.join(f'{k}={v}' for k, v in func_kwargs.items())],
                ['ctx.is_loggedin', str(ctx.is_loggedin)],
            ],
        }
    return qwarn(f'Unknown command: {action}')


def demo_hooks_quote(prepared_by: str = 'nobody', quote_date='2000-01-01', width=12.0, height=8.0, coats: int = 2,
                     price_per_gal=40.0, discount_pct=0.0):
    area = width * height
    gallons = area * coats / COVERAGE_SQFT_PER_GAL
    cost = gallons * price_per_gal * (1 - discount_pct / 100)
    return {
        'Prepared by': prepared_by,
        'Quote date': str(quote_date),
        'Area (sq ft)': round(area, 2),
        'Paint needed (gal)': round(gallons, 2),
        'Cost': round(cost, 2),
    }


# ----------------------------------------------------------------------------------------------------------
# Demo 2: demo_hooks_material
# The choices of 'material' depend on 'material_type'. Three pieces work together:
#   'reload' (in __info)  rebuilds the form when material_type changes and resets the fields it lists
#   __schema(ctx)         gives the choices of material for the selected type
#   __input(ctx)          gives a default material that belongs to the selected type
# ----------------------------------------------------------------------------------------------------------

MATERIALS = {  # density in kg/m3
    'metal': {'steel': 7850, 'aluminium': 2700, 'copper': 8960},
    'wood': {'oak': 750, 'pine': 500, 'balsa': 160},
    'plastic': {'pvc': 1380, 'abs': 1050, 'nylon': 1150},
}


def _material_choices(material_type):
    return {name: f'{name.title()} ({density} kg/m3)' for name, density in MATERIALS[material_type].items()}


def _material_type(ctx):
    # the selection of the user when the form is submitted or rebuilt by 'reload', else the value the form
    # starts with (function default, remembered value or value in the calculator url)
    for value in (ctx.posted('material_type'), ctx.resolved('material_type')):
        if value in MATERIALS:
            return value
    return 'metal'


def demo_hooks_material__info():
    return {
        'title': 'Hooks demo: choices that depend on another field',
        'desc': 'Shows __info with reload, __schema and __input: the materials follow the selected type.',
        'schema': {
            'material_type': {
                'type': 'choice', 'choices': {name: name.title() for name in MATERIALS},
                'reload': ['material'],  # changing the type rebuilds the form and resets the material
                'help_inline': 'Changing it reloads the form (reload in __info) and resets the material.',
            },
            # | static choices are only the fallback, __schema() replaces them every time the form is built
            'material': {
                'type': 'choice', 'choices': _material_choices('metal'),
                'help_inline': 'Choices come from __schema(), the default from __input(), for the selected type.',
            },
            'volume_l': {
                'help_inline': 'Litres. It is not in the reload list, so it keeps your value when the type changes.'},
        },
    }


def demo_hooks_material__schema(ctx):
    # __schema(ctx) returns {field: {property: value}} that is merged over the schema of __info(). Unlike
    # __info() it runs every time the form is built, so choices can depend on the request.
    return {'material': {'choices': _material_choices(_material_type(ctx))}}


def demo_hooks_material__input(ctx):
    # the function default 'steel' is only right for metals, the material of the selected type is the default
    return {'material': next(iter(MATERIALS[_material_type(ctx)]))}


def demo_hooks_material(material_type='metal', material='steel', volume_l=10.0):
    if material not in MATERIALS.get(material_type, {}):
        raise ValueError(f'{material} is not a {material_type}')
    density = MATERIALS[material_type][material]
    return {
        'Density (kg/m3)': density,
        'Mass (kg)': round(density * volume_l / 1000, 3),
    }
