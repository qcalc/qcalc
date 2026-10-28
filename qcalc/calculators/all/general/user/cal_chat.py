# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import ast
import inspect
import re
from html import escape
from urllib.parse import quote

from qcore import qchat, qhtml, qinfo, qtexta
from qcore.mod_fields import ai_prompt_field
from calc import QCals, ask_gpt, create_openai_chat_completion
from calc.mod_cache import QOpenAIChat
from qutil import (
    cal_link,
    calurl,
    callback_button,
    escape_markdown,
    md2html,
    md_math_script,
)

from ..author.mod_mycal_tools import MyCalTools


def _render_ai_chat(turns):
    sections = []
    for turn in turns:
        sections.extend([
            '#### You',
            escape_markdown(turn['user']),
            '#### AI',
            escape_markdown(turn['assistant']),
        ])
    return qchat(md2html('\n\n'.join(sections), wrap=True))


def ai_chat__command(_fkwargs, extra):
    if extra['args'][0] == 'new_chat':
        QOpenAIChat.clear()
        return qinfo('AI conversation cleared')
    return ''


def ai_chat__info():
    return {
        'title': 'Chat with AI',
        'kins': 'mycal, mycal2',
        'tags': 'ai, natural language',
        'schema': {
            'question': ai_prompt_field(
                label='Agent Message',
                placeholder='Ask a question or continue the conversation...',
                rows=8,
                max_chars=16000,
                monospace=True,
                token_hint=True,
            ),
        },
        'calculate': 'Send',
        'inserts': {
            'form_top': callback_button(
                'ai_chat',
                'New Chat',
                '__command',
                args=['new_chat'],
            ),
            'out_bottom': md_math_script(),
        },
    }


def ai_chat(question: qtexta = 'What is qCalc?'):
    response = ask_gpt(
        'Format mathematical expressions as LaTeX using $...$ for inline '
        'math and $$...$$ for display math.\n\n'
        f'User message:\n{question}'
    )
    state = QOpenAIChat.getp({})
    turns = state.get('turns', [])
    turns.append({
        'user': question,
        'assistant': str(response),
    })
    QOpenAIChat.setp({'turns': turns})
    return {
        'Conversation': _render_ai_chat(turns),
    }


def _calculator_context(calculators):
    blocks = []
    for calculator in calculators:
        blocks.append(
            f"Calculator: {calculator['name']}\n"
            f"Title: {calculator['title']}\n"
            f"Description: {calculator['description']}\n"
            f"Source:\n{calculator['code']}"
        )
    return '\n\n---\n\n'.join(blocks)


def _extract_call_list(content):
    # Models may wrap the list in a Markdown fence or add surrounding prose.
    text = str(content or '').strip()
    start, end = text.find('['), text.rfind(']')
    if start != -1 and end > start:
        return text[start:end + 1]
    return re.sub(r'^```[\w-]*\s*|\s*```$', '', text).strip()


def _parse_calculator_calls(content, calculator_names, max_count):
    try:
        parsed = ast.parse(_extract_call_list(content), mode='eval').body
    except SyntaxError as error:
        raise ValueError(
            f'Could not return valid function calls: {content!r}'
        ) from error

    calls = {}
    for call in parsed.elts if isinstance(parsed, ast.List) else [parsed]:
        if isinstance(call, ast.Constant) and isinstance(call.value, str):
            try:
                call = ast.parse(call.value, mode='eval').body
            except SyntaxError:
                continue
        if (
            isinstance(call, ast.Call)
            and isinstance(call.func, ast.Name)
            and call.func.id in calculator_names
        ):
            calls.setdefault(call.func.id, call)
    if not calls:
        raise ValueError(
            f'Could not return a call to a searched calculator: '
            f'{content!r}'
        )
    return list(calls.values())[:max_count]


def _calculator_call_link(call):
    name = call.func.id
    parameters = inspect.signature(QCals.addr(name, scope='q')).parameters
    arguments = list(zip(parameters, call.args))
    arguments += [(kw.arg, kw.value) for kw in call.keywords if kw.arg]
    values = []
    for key, node in arguments:
        try:
            value = ast.literal_eval(node)
        except ValueError:  # placeholder such as rate=r: keep the default
            continue
        values.append((key, value))
    path = '/'.join(
        f'{quote(key, safe="")}/{quote(str(value), safe="")}'
        for key, value in values
    )
    caption = f"{name}({', '.join(f'{key}={value!r}' for key, value in values)})"
    return cal_link(calurl(name, path), escape(caption))


def q2cal__info():
    return {
        'title': 'What do You Want to Calculate?',
        'desc': 'Find the most relevant qCalc calculator from a natural-language query.',
        'interactive': False,
        'tags': 'ai, calculator search, natural language',
        'schema': {
            'query': ai_prompt_field(
                label='Query',
                placeholder='Describe the calculation you want to perform...',
                rows=4,
                max_chars=4000,
                monospace=False,
                token_hint=True,
                help_text=(
                    'Describe the calculation and include known values, units, '
                    'and constraints so qCalc can find relevant calculators.'
                ),
            ),
            'n': {
                'label': 'Max number of results',
                'attrs': {'min': '1', 'max': '5'},
            },
        },
        'calculate': 'Submit',
    }


def q2cal(query: qtexta = 'Calculate body mass index for 70 kg and 1.75 m',
        n=3):
    n = int(n)
    if not 1 <= n <= 5:
        raise ValueError('Number of results must be between 1 and 5.')

    calculators = MyCalTools.find_relevant_calculators(query)
    if not calculators:
        raise ValueError(
            f'No relevant qCalc calculator was found for "{query}".'
        )

    result_count = min(n, len(calculators))
    messages = [
        {
            'role': 'system',
            'content': (
                'Select distinct relevant qCalc '
                'calculators from the supplied candidates, ordered from most '
                'to least relevant, without exceeding the requested maximum. '
                'Translate the user query into a Python function-call '
                'expression for each selection. Use each calculator source '
                'to map values to its real parameters. Omit every argument the '
                'user did not specify, because a calculator called without '
                'arguments runs with its defaults. Return only a Python '
                'list of function calls, without Markdown or explanation.'
            ),
        },
        {
            'role': 'user',
            'content': (
                f'User query:\n{query}\n\n'
                f'Maximum calculator calls: {result_count}\n\n'
                f'Candidate calculators:\n{_calculator_context(calculators)}'
            ),
        },
    ]
    response = create_openai_chat_completion(
        messages,
        max_tokens=300,
    )

    calls = _parse_calculator_calls(
        response.choices[0].message.content,
        {calculator['name'] for calculator in calculators},
        result_count,
    )
    return qhtml(''.join(
        f'<div class="mb-2">{_calculator_call_link(call)}</div>'
        for call in calls
    ))
