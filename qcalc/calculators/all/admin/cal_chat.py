# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import openai
from qcore import qtexta
from django.conf import settings
from calc import check_setting, ask_gpt

def qchat__info():
    return {
        "title": "Chat with ChatGPT",
        "calculate": "Submit",
    }


def qchat(question: qtexta = "What is qCalc"):
    resp = ask_gpt(question)
    return resp


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
    api_key = check_setting(settings.OPENAI_API_KEY, "OPENAI_API_KEY", optional=False)
    client = openai.OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        max_tokens=50,
        temperature=0.5
    )

    function_call = response.choices[0].message.content
    return function_call
