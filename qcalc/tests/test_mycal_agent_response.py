# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha
# Tests generated with AI assistance. Reviewed and validated by the author.

import json

import qsett

qsett.init()

from calculators.all.general.author import mod_mycal_agent
from calculators.all.general.author.mod_mycal_agent import MyCalAgent


def test_answer_preserves_unexpected_code_field_as_conversation():
    response = MyCalAgent._parse_agent_response(json.dumps({
        'action': 'answer',
        'message': 'Here are some examples:',
        'code': "Use `Qty('10 kg')` for quantities.",
    }))

    assert response.action == 'answer'
    assert response.code == ''
    assert response.message == (
        "Here are some examples:\n\nUse `Qty('10 kg')` for quantities."
    )


def test_missing_action_does_not_assume_code_field_is_python():
    response = MyCalAgent._parse_agent_response(json.dumps({
        'message': 'The identity is:',
        'code': '$$(a+b)^2 = a^2 + 2ab + b^2$$',
    }))

    assert response.action == 'answer'
    assert response.code == ''
    assert '$$(a+b)^2 = a^2 + 2ab + b^2$$' in response.message


def test_propose_code_keeps_complete_calculator_code_separate():
    calculator_code = (
        "def add(x=1, y=2):\n"
        "    return x + y\n\n"
        "def add__info():\n"
        "    return {'title': 'Add'}"
    )
    response = MyCalAgent._parse_agent_response(json.dumps({
        'action': 'propose_code',
        'message': 'Here is the calculator.',
        'code': calculator_code,
    }))

    assert response.action == 'propose_code'
    assert response.message == 'Here is the calculator.'
    assert response.code == calculator_code


def test_generation_repairs_one_validation_failure(monkeypatch):
    responses = iter([
        json.dumps({
            'action': 'propose_code',
            'message': 'Initial candidate.',
            'code': (
                "def divide(x=1, y=0):\n"
                "    return x / y\n\n"
                "def divide__info():\n"
                "    return {'title': 'Divide'}\n"
            ),
        }),
        json.dumps({
            'action': 'propose_code',
            'message': 'Corrected the invalid default.',
            'code': (
                "def divide(x=1, y=1):\n"
                "    return x / y\n\n"
                "def divide__info():\n"
                "    return {'title': 'Divide'}\n"
            ),
        }),
    ])
    prompts = []

    def fake_ask_gpt(prompt):
        prompts.append(prompt)
        return next(responses)

    monkeypatch.setattr(mod_mycal_agent, 'ask_gpt', fake_ask_gpt)

    response = MyCalAgent._generate_response(
        'Create a division calculator.',
        '',
        max_validation_repairs=1,
    )

    assert len(prompts) == 2
    assert '"name": "default_execution"' in prompts[1]
    assert 'division by zero' in prompts[1]
    assert 'y=0' in prompts[1]
    assert 'y=1' in response.code
    assert response.validation_error == ''


def test_generation_does_not_retry_ai_request_failure(monkeypatch):
    calls = 0

    def failing_ask_gpt(prompt):
        nonlocal calls
        calls += 1
        raise RuntimeError('service unavailable')

    monkeypatch.setattr(mod_mycal_agent, 'ask_gpt', failing_ask_gpt)

    try:
        MyCalAgent._generate_response(
            'Create a calculator.',
            '',
            max_validation_repairs=1,
        )
    except mod_mycal_agent.AIGenerationError as error:
        assert 'service unavailable' in str(error)
    else:
        raise AssertionError('Expected AIGenerationError')

    assert calls == 1


def test_generation_stops_after_one_failed_validation_repair(monkeypatch):
    calls = 0
    invalid_response = json.dumps({
        'action': 'propose_code',
        'message': 'Candidate.',
        'code': (
            "def divide(x=1, y=0):\n"
            "    return x / y\n\n"
            "def divide__info():\n"
            "    return {'title': 'Divide'}\n"
        ),
    })

    def fake_ask_gpt(prompt):
        nonlocal calls
        calls += 1
        return invalid_response

    monkeypatch.setattr(mod_mycal_agent, 'ask_gpt', fake_ask_gpt)

    response = MyCalAgent._generate_response(
        'Create a division calculator.',
        '',
        max_validation_repairs=1,
    )

    assert calls == 2
    assert response.action == 'propose_code'
    assert 'division by zero' in response.validation_error


def test_reference_resolution_prefers_explicit_references(monkeypatch):
    state = {'reference_cals': '', 'auto_reference_cal': ''}
    monkeypatch.setattr(
        MyCalAgent,
        '_load_reference_context',
        lambda names: f'explicit:{names}',
    )

    context = MyCalAgent._resolve_reference_context(
        'body mass index',
        'bmi',
        '',
        state,
    )

    assert context == 'explicit:bmi'
    assert state['reference_cals'] == 'bmi'
    assert state['auto_reference_cal'] == ''


def test_reference_resolution_selects_and_reuses_automatic_reference(monkeypatch):
    state = {'reference_cals': '', 'auto_reference_cal': ''}
    searches = []

    def find_similar(query, exclude_names):
        searches.append((query, exclude_names))
        return {
            'found': True,
            'name': 'bmi',
            'title': 'BMI',
            'code': 'def bmi(): pass',
        }

    monkeypatch.setattr(
        mod_mycal_agent.MyCalTools,
        'find_similar_calculator',
        find_similar,
    )
    monkeypatch.setattr(
        mod_mycal_agent.MyCalTools,
        'get_similar_calculator_context',
        lambda result: f"automatic:{result['name']}",
    )
    monkeypatch.setattr(
        MyCalAgent,
        '_load_reference_context',
        lambda names: f'stored:{names}',
    )

    first_context = MyCalAgent._resolve_reference_context(
        'body mass index',
        '',
        'new_bmi',
        state,
    )
    second_context = MyCalAgent._resolve_reference_context(
        'change the title',
        '',
        'new_bmi',
        state,
    )

    assert first_context == 'automatic:bmi'
    assert second_context == 'stored:bmi'
    assert searches == [('body mass index', ['new_bmi'])]
