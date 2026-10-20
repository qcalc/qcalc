# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from qcore.mod_anno import *
from qcore.mod_fields import ai_prompt_field, br
from calc import UCals
from qutil import (
    addcal_button,
    callback_button,
    escape_markdown,
    extract_common_prefix,
    get_functions,
    md2html,
    md_math_script,
    page_link,
)

from .cal_mycal import validate_calculator_defaults, validate_calculator_info, mycal__modify
from .mod_mycal_agent import AIGenerationError, MyCalAgent


def _render_agent_history():
    sections = ['### MyCal AI Conversation']
    for turn in MyCalAgent.get_history():
        user_prompt = turn.get('user_prompt', '').strip()
        assistant_message = turn.get('assistant_message', '').strip()
        validation_error = turn.get('validation_error', '').strip()
        response_code = turn.get('response_code', '').strip()

        sections.append('---')
        if user_prompt:
            sections.extend(['#### You', escape_markdown(user_prompt)])
        sections.append('#### qCalc Agent')
        if assistant_message:
            sections.append(escape_markdown(assistant_message))
        if validation_error:
            sections.append(
                f'**Validation:** {escape_markdown(validation_error)}'
            )
        if response_code:
            sections.append(f'```python\n{response_code}\n```')

    return qchat(md2html('\n\n'.join(sections), wrap=True))


def mycal2__command(fkwargs, extra):
    result = ''
    final_prompt = ''
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
    elif action == 'ai_send':
        try:
            prompt = fkwargs.get('ai_prompt', '')
            cal_name = fkwargs.get('cal_name', '')
            response = MyCalAgent.send(
                prompt,
                user_code,
                cal_name_hint=cal_name,
                max_attempts=1,
                reference_cals=fkwargs.get('reference_cals', ''),
            )
            final_prompt = response.prompt
            result = _render_agent_history()
        except AIGenerationError as e:
            final_prompt = e.prompt
            result = f'AI response failed: {e}'
        except Exception as e:
            result = f'AI response failed: {e}'
    elif action == 'ai_new':
        MyCalAgent.reset()
        result = qhtml(md2html(
            '### New AI Task\n\nConversation cleared. '
            'Enter an Agent Message and select **Send to AI**.'
        ))
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
        'title': 'Create My Calculator - AI Assisted',
        'desc': 'Generate and validate calculator code with AI assistance before saving.',
        'kins': 'eva, mycal, ai_chat',
        'tags': 'create calculator, prompt',
        'schema': {
            'ai_prompt': ai_prompt_field(
                label='Agent Message',
                placeholder='Ask a question, clarify requirements, or request calculator changes...',
                rows=8,
                max_chars=16000,
                monospace=True,
                token_hint=True,
            ),
            'reference_cals': {
                'type': 'qtext',
                'label': 'Reference Calculators',
                'help_text': 'Optional: 1-3 existing calculator names (comma/newline separated) used as style references.',
                'attrs': {
                    'placeholder': 'e.g. addlen, bmi, npv',
                    'maxlength': '300',
                },
            },
        },
        'inserts': {
            'form_bottom':
                callback_button('mycal2', 'Check Syntax', '__command', args=['syntax']) +
                callback_button('mycal2', 'Format Code', '__modify', kwargs={'code': 'format'}) +
                callback_button('mycal2', 'Validate Input', '__command', args=['validate']) +
                page_link('/catalog/user/', 'My Catalog', 'btn btnurl', 'icon-tree5'),
            'out_bottom': md_math_script(),
        },
        'calculate': 'Save',
        'layout': 'tb',
    }


def mycal2(cal_name='',
           _cal_buttons=qhtml(br(
               callback_button('mycal2', 'Load Code', '__modify', kwargs={'code': 'load'}) +
               callback_button('mycal2', 'Delete Code', '__modify', kwargs={'cal_name': 'delete'}))),
           reference_cals='',
           ai_prompt: qtexta = '',
           _ai_buttons=qhtml(br(
               callback_button('mycal2', 'New AI Task', '__command', args=['ai_new']) +
               callback_button('mycal2', 'Send to AI', '__command', args=['ai_send']))),
           code: qcode = """
def addlen(x='7 ft',y='8 m'):
    z=Qty(x)+Qty(y)
    return z.to('m')

def addlen__info():
    return {
        'title':'Add Two Lengths'
    }
"""
           ):
    _ = ai_prompt  # prompt is used by __command actions, not by save flow
    _ = reference_cals  # references are used by __command actions, not by save flow
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
