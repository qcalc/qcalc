# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import re

from qcore.mod_anno import *
from calc import UCals
from calc.mod_openai import ask_gpt
from qutil import command_button, page_link, format_py_code, ensure_info_function, extract_common_prefix, \
    get_functions, addcal_button, md2html

from .cal_mycal import validate_calculator_defaults, validate_calculator_info, mycal__modify


_CODE_BLOCK_RE = re.compile(r"```(?:python)?\s*(.*?)```", re.IGNORECASE | re.DOTALL)


def _extract_python_code(text):
    if not isinstance(text, str):
        raise ValueError('AI response is not text')

    stripped = text.strip()
    match = _CODE_BLOCK_RE.search(stripped)
    if match:
        stripped = match.group(1).strip()

    if stripped == '':
        raise ValueError('AI response did not contain Python code')
    return stripped


def _build_prompt(user_prompt, current_code, validation_error=''):
    return f"""
You are generating Python calculator code for qCalc mycal editor.

Output rules:
- Return ONLY Python code. No markdown and no explanation text.
- Define one main calculator function and matching __info function.
- Allowed meta functions: __info, __input, __modify, __command, __help.
- Keep function defaults runnable without required arguments.
- __info must return a dict and include at least 'title'.

User request:
{user_prompt}

Current code:
{current_code}

Validation error:
{validation_error}
""".strip()


def _validate_code(code):
    validate_calculator_info(code)
    validate_calculator_defaults(code)


def _ai_generate_code(user_prompt, current_code, cal_name_hint='', max_attempts=3):
    prompt = user_prompt.strip()
    if prompt == '':
        raise ValueError('Please provide AI prompt')

    draft = current_code
    last_error = ''
    for _ in range(max_attempts):
        ai_prompt = _build_prompt(prompt, draft, last_error)
        generated = ask_gpt(ai_prompt, temperature=0.2)
        draft = _extract_python_code(generated)
        draft, _functions = ensure_info_function(draft, cal_name_hint)
        draft = format_py_code(draft)

        try:
            _validate_code(draft)
            return draft
        except Exception as e:
            last_error = str(e)

    raise ValueError(f'AI could not produce valid code after {max_attempts} attempts: {last_error}')


def _render_code_markdown(code, title='AI Generated Code'):
    md_text = f"### {title}\n```python\n{code}\n```"
    return qhtml(md2html(md_text, wrap=True))


def mycal2__command(fkwargs, extra):
    result = ''
    action = extra['args'][0]
    user_code = fkwargs.get('code', '')

    if action == 'syntax':
        try:
            result = validate_calculator_info(user_code)
        except Exception as e:
            result = str(e)
    elif action == 'validate':
        try:
            result = validate_calculator_defaults(user_code)
        except Exception as e:
            result = str(e)
    elif action == 'ai_draft':
        try:
            prompt = fkwargs.get('ai_prompt', '')
            cal_name = fkwargs.get('cal_name', '')
            code = _ai_generate_code(prompt, user_code, cal_name_hint=cal_name, max_attempts=3)
            result = _render_code_markdown(code, 'AI Draft (Copy and paste into Code if needed)')
        except Exception as e:
            result = f'AI draft failed: {e}'
    elif action == 'ai_fix':
        try:
            cal_name = fkwargs.get('cal_name', '')
            prompt = fkwargs.get('ai_prompt', '').strip()
            if prompt == '':
                try:
                    _validate_code(user_code)
                    return 'Code is already valid'
                except Exception as e:
                    prompt = f'Fix this qCalc calculator code without changing the intended behavior. Current validation error: {e}'
            code = _ai_generate_code(prompt, user_code, cal_name_hint=cal_name, max_attempts=3)
            result = _render_code_markdown(code, 'AI Fix (Copy and paste into Code if needed)')
        except Exception as e:
            result = f'AI fix failed: {e}'
    return result


def mycal2__modify(arg_name, arg_value, action):
    return mycal__modify(arg_name, arg_value, action)


def mycal2__input(kwargs):
    uc = UCals()
    user_code = uc.get_code(kwargs.get('cal_name', ''))
    if user_code:
        return {
            'code': user_code
        }
    else:
        return {'cal_name': ''}


def mycal2__info():
    return {
        'title': 'Create My Calculator (AI Assisted)',
        'desc': 'Generate and validate calculator code with AI assistance before saving.',
        'schema': {
            'ai_prompt': {
                'type': 'qtexta',
                'help_text': 'Describe the calculator behavior or provide fix instructions for existing code.',
            },
        },
        'inserts': {
            'form_top':
                command_button('mycal2', 'Load Code', '__modify', kwargs={'code': 'load'}) +
                command_button('mycal2', 'Delete Code', '__modify', kwargs={'cal_name': 'delete'}) +
                page_link('/catalog/user/', 'My Catalog', 'btn btnurl', 'icon-tree5'),
            'form_bottom':
                command_button('mycal2', 'Check Syntax', '__command', args=['syntax']) +
                command_button('mycal2', 'Format Code', '__modify', kwargs={'code': 'format'}) +
                command_button('mycal2', 'Validate Input', '__command', args=['validate']) +
                command_button('mycal2', 'AI Draft Code', '__command', args=['ai_draft']) +
                command_button('mycal2', 'AI Fix Code', '__command', args=['ai_fix']),
        },
        'calculate': 'Save',
        'kins': 'eva',
        'layout': 'tb',
    }


def mycal2(cal_name='', ai_prompt: qtexta = '', code: qcode = """
def addlen(x='7 ft',y='8 m'):
    z=Qty(x)+Qty(y)
    return z

def addlen__info():
    return {
        'title':'Add Two Lengths'
    }
"""
           ):
    _ = ai_prompt  # prompt is used by __command actions, not by save flow
    try:
        uc = UCals()
        res = uc.edit_cal(cal_name, code)
        cal_name = extract_common_prefix(get_functions(code))
        cal_id = f"{cal_name}-{uc.cal_owner}"
        open_button = qhtml(addcal_button(cal_id, f'Open {cal_name}'))
        return {
            'Remarks': res,
            'Open': open_button
        }
    except Exception as e:
        return f'Error (MC2): {e}'
