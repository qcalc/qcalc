# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import openai

from qcore import qchat, qinfo, qtexta
from qcore.mod_fields import ai_prompt_field
from calc import ask_gpt
from calc.mod_cache import QOpenAIChat
from calc.mod_credentials import get_effective_api_key
from qutil import (
    QThread,
    callback_button,
    escape_markdown,
    is_loggedin,
    md2html,
    md_math_script,
)


def _render_ai_chat(turns):
    sections = []
    for turn in turns:
        sections.extend([
            '#### You',
            escape_markdown(turn['user']),
            '#### OpenAI',
            escape_markdown(turn['assistant']),
        ])
    return qchat(md2html('\n\n'.join(sections), wrap=True))


def ai_chat__command(_fkwargs, extra):
    if extra['args'][0] == 'new_chat':
        QOpenAIChat.clear()
        return qinfo('OpenAI conversation cleared')
    return ''


def ai_chat__info():
    return {
        'title': 'Chat with OpenAI',
        'kins': 'mycal, mycal2',
        'tags': 'create calculator, prompt',
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


def q2f__info():
    return {
        "title": "Query to Function Call",
        "calculate": "Submit",
    }


def q2f(query: qtexta = "Convert 5 kilometers to miles"):
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {
            "role": "user",
            "content": f"""
    The user has a unit converter application with the function call conv(value, from_unit, to_unit).
    Interpret the user's natural language query to return a Python function call like this.

    Example:
    Query: "Convert 5 kilometers to miles."
    Function call: conv(5, 'kilometers', 'miles')

    Query: "{query}"
    Function call:
    """
        }
    ]
    req = QThread.get_req()
    user = req.user if req is not None and is_loggedin(req) else None
    api_key = get_effective_api_key(user, 'openai')
    client = openai.OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        max_tokens=50,
        temperature=0.5
    )

    function_call = response.choices[0].message.content
    return function_call
