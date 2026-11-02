# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

# The simplest demos of the optional hooks: one calculator for each hook, each as short as possible.
# Every calculator has the mandatory __info(). It is kept to a title, a description and a note for each field,
# the hook that the demo is about is the only other function besides the calculator itself.
# Read them in this order. The hooks are explained in qcalc_res/docs/author-guide/calculator-hooks.md
# and dem_hooks.py has larger demos that use several hooks together.
#
#   demo_hook_info     __info     the mandatory function: title, description and a note under a field
#   demo_hook_input    __input    starting values that depend on the user and the day
#   demo_hook_schema   __schema   choices of a field that are built for each request
#   demo_hook_help     __help     help text that is created when it is shown
#   demo_hook_modify   __modify   a button that changes the value of a field
#   demo_hook_command  __command  a button that checks the form without calculating
#   demo_formula_field __input    a read-only field that shows a formula, kept up to date by 'reload'
#   demo_formula_qty   __input    the same with quantity fields (value + unit)

from datetime import date, datetime, timedelta

from qcore import Qty, qinfo, qt, qwarn
from qutil import callback_button, md2html


# ----------------------------------------------------------------------------------------------------------
# 1. __info: static information about the calculator
# ----------------------------------------------------------------------------------------------------------

def demo_hook_info__info():
    # the mandatory function: no arguments, returns a dictionary. Every calculator has it. Everything here is
    # fixed text, it does not depend on the request.
    return {
        'title': 'Hook demo 1: __info',
        'desc': '__info() gives the calculator its title, description and button caption, and notes for fields.',
        'calculate': 'Find area',
        'schema': {
            'width': {'help_inline': 'help_inline is shown under the field label.'},
            'height': {'help_inline': 'Every field can have its own note.'},
        },
    }


def demo_hook_info(width=3.0, height=2.0):
    return {'Area': width * height}


# ----------------------------------------------------------------------------------------------------------
# 2. __input: starting values that cannot be written in the function signature
# ----------------------------------------------------------------------------------------------------------

def demo_hook_input__info():
    return {
        'title': 'Hook demo 2: __input',
        'desc': '__input() fills the name and the date when the form opens.',
        'schema': {
            'who': {'help_inline': 'Filled by __input() with your user name, or "guest" when you are not logged in.'},
            'today': {'help_inline': 'Filled by __input() with today\'s date. The default in the function is fixed.'},
        },
    }


def demo_hook_input__input(ctx):
    # ctx describes the request. __input(ctx) returns {field: starting value}. It runs every time the form
    # opens, while the defaults in the function signature below are fixed when qCalc starts.
    return {
        'who': ctx.user if ctx.is_loggedin else 'guest',
        'today': date.today().isoformat(),
    }


def demo_hook_input(who: str = 'nobody', today='2000-01-01'):
    return {'Message': f'Hello {who}, today is {today}.'}


# ----------------------------------------------------------------------------------------------------------
# 3. __schema: field properties, here the choices, built for each request
# ----------------------------------------------------------------------------------------------------------

def demo_hook_schema__info():
    return {
        'title': 'Hook demo 3: __schema',
        'desc': '__schema() builds the list of days each time the form opens.',
        'schema': {
            'day': {'help_inline': 'The choices are the next three days. __schema() creates them for each request.'},
        },
    }


def demo_hook_schema__schema(ctx):
    # returns {field: {property: value}}. It is the same as the schema in __info(), but it is built every time
    # the form opens, so the choices can change: here the next three days, counted from today.
    days = [date.today() + timedelta(days=i) for i in range(1, 4)]
    return {
        'day': {'type': 'choice', 'choices': {d.isoformat(): f'{d:%A %d %B}' for d in days}},
    }


def demo_hook_schema(day: str = ''):
    return {'Chosen day': day}


# ----------------------------------------------------------------------------------------------------------
# 4. __help: help text that is created when it is shown
# ----------------------------------------------------------------------------------------------------------

def demo_hook_help__info():
    return {
        'title': 'Hook demo 4: __help',
        'desc': '__help() creates the help text. Expand the help node on top of this calculator.',
    }


def demo_hook_help__help():
    # Takes no arguments and returns HTML.
    return md2html(
        f'Use `__help()` to provide a quick explanation of this calculator. '
        f'This complements the separate calculator help file.\n\n'
        f'This function runs each time the help is displayed, so the text can '
        f'include dynamically generated values.\n\n'
        f'This help text was generated at **{datetime.now():%H:%M:%S}**. '
        f'Open the help again to see the updated time.'
    )


def demo_hook_help(a=1.0, b=2.0):
    return {'Sum': a + b}


# ----------------------------------------------------------------------------------------------------------
# 5. __modify: a button that changes the value of a field
# ----------------------------------------------------------------------------------------------------------

def demo_hook_modify__info():
    # a button can only be created in __info(), which every calculator has. callback_button(calculator, caption,
    # '__modify', args=[fields]) calls __modify() once for each field in args.
    return {
        'title': 'Hook demo 5: __modify',
        'desc': 'The button calls __modify() for the field text and puts its answer back in the field.',
        'schema': {
            'text': {'help_inline': 'Type something, then press the button.'},
            'repeat': {'help_inline': 'Whole number. No hook touches it, the button keeps what you typed.'},
        },
        'inserts': {
            'form_bottom': callback_button('demo_hook_modify', 'Make upper case', '__modify', args=['text']),
        },
    }


def demo_hook_modify__modify(ctx, arg_name, arg_value, action):
    # arg_name is the field, arg_value its posted value. The returned value becomes the new value of the field.
    # Everything else in the form stays as the user typed it.
    return arg_value.upper()


def demo_hook_modify(text: str = 'hello world', repeat: int = 2):
    return {'Result': ' '.join([text] * repeat)}


# ----------------------------------------------------------------------------------------------------------
# 6. __command: a button that runs an action instead of calculating
# ----------------------------------------------------------------------------------------------------------

def demo_hook_command__info():
    # the button is created here, in the mandatory __info()
    return {
        'title': 'Hook demo 6: __command',
        'desc': 'The button calls __command() with the checked values and shows a message, nothing is calculated.',
        'schema': {
            'width': {'help_inline': 'Feet.'},
            'height': {'help_inline': 'Feet. Make the area more than 100 sq ft and press the button to see a warning.'},
        },
        'inserts': {
            'form_bottom': callback_button('demo_hook_command', 'Check size', '__command'),
        },
    }


def demo_hook_command__command(ctx, func_kwargs):
    # func_kwargs holds all the fields, already converted and validated, as the function would receive them.
    # The return value is shown as the result.
    area = func_kwargs['width'] * func_kwargs['height']
    if area > 100:
        return qwarn(f'The area is {area:g} sq ft, that is a big wall.')
    return qinfo(f'The area is {area:g} sq ft, that is fine.')


def demo_hook_command(width=12.0, height=8.0):
    return {'Area': width * height}


# ----------------------------------------------------------------------------------------------------------
# 7. A read-only formula field: 'reload' + __input, no javascript
# ----------------------------------------------------------------------------------------------------------

def demo_formula_field__info():
    # 'reload' on width and height rebuilds the form on the server when either one changes (after the field loses
    # focus). The listed field, area, is reset to its default each time, which is where __input() puts the formula.
    # 'disabled' makes area read-only for the user, and the form takes its value from __input() also when it is
    # calculated, never from what the browser posts.
    return {
        'title': 'Formula field demo: reload + __input',
        'desc': 'The read-only Area is width x height. It is recalculated on the server when width or height changes.',
        'schema': {
            'width': {'reload': ['area'], 'help_inline': 'Change it, then click outside the field.'},
            'height': {'reload': ['area'], 'help_inline': 'Area follows after the field loses focus.'},
            'area': {'disabled': True, 'help_inline': 'Read-only, computed by __input().'},
        },
    }


def demo_formula_field__input(ctx):
    # ctx.value(name, float, default) is the number in the field in this request: the posted one, or the starting
    # value on the first open when nothing is posted. The default is used when neither is a number.
    return {'area': ctx.value('width', float, 0.0) * ctx.value('height', float, 0.0)}


def demo_formula_field(width=3.0, height=2.0, area=6.0):
    return {'Width': width, 'Height': height, 'Area': area}


def demo_formula_field__help():
    return md2html(
        '**How it works**\n\n'
        '* `reload` on `width` and `height` rebuilds the input section on the server when either changes. '
        '`__input(ctx)` runs again and returns the new `area`.\n'
        '* `area` is in the `reload` list, so it is reset to its default each time. Without that it would keep '
        'its old value.\n'
        '* `area` is `disabled`: the user cannot edit it, and the form takes its value from `__input()` '
        'also when you press Calculate, never from the browser. A plain `readonly` input is still posted, '
        'so it can be changed with the browser tools.\n\n'
        '**Things to watch**\n\n'
        '* Every field the formula reads needs a `reload` list that includes the formula field.\n'
        '* `ctx.posted()` returns text. `ctx.value(name, float, default)` gives the number in the field in this '
        'request: the posted one, or the starting value on the first open, when nothing is posted. '
        'The default is used when neither is a number.\n'
        '* The form is rebuilt on `change`, that is after the field loses focus, not on each key press. '
        'It needs a round trip to the server. For an instant update use JavaScript.\n'
        '* Use `reload` on plain fields. A select2 field does not reliably report a change.\n'
        '* The function still receives `area` as an argument, so it needs a default in the signature.'
    )


# ----------------------------------------------------------------------------------------------------------
# 8. A read-only formula field with quantities: two masses added in the unit of the first one
# ----------------------------------------------------------------------------------------------------------

def demo_formula_qty__info():
    # A quantity field is posted as two inputs: the value (mass1) and the unit (mass1_uom). 'reload' on mass1 is
    # put on both of them, but the unit of total is a field of its own, so total_uom must be reset with it.
    # 'disabled' does not reach the inputs of a quantity, use attrs readonly, which qCalc passes on to both the
    # value and the unit. A readonly input is still posted, so the user could edit it with the browser tools.
    return {
        'title': 'Formula field demo: quantities',
        'desc': 'The read-only Total is mass 1 + mass 2, shown in the unit of mass 1.',
        'schema': {
            'mass1': {'reload': ['total', 'total_uom'], 'help_inline': 'Change the value or the unit.'},
            'mass2': {'reload': ['total', 'total_uom'], 'help_inline': 'Any mass unit, for example g or lb.'},
            'total': {'attrs': {'readonly': True}, 'help_inline': 'Read-only, computed by __input().'},
        },
    }


def demo_formula_qty__input(ctx):
    # ctx.value(name, qt) is the quantity in the field in this request: the posted value and unit joined into
    # one quantity, or the starting quantity on the first open when nothing is posted.
    # The sum has the unit of the first quantity.
    return {'total': str(ctx.value('mass1', qt) + ctx.value('mass2', qt))}


def demo_formula_qty(mass1: qt = '2 kg', mass2: qt = '500 g', total: qt = '2.5 kg'):
    return {'Mass 1': Qty(mass1), 'Mass 2': Qty(mass2), 'Total': Qty(total)}
