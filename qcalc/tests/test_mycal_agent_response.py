import json

import qsett

qsett.init()

from calculators.all.general.user.mod_mycal_agent import MyCalAgent


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
