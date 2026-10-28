import ast
from types import SimpleNamespace

import qsett

qsett.init()

import pytest

from calculators.all.general.user import cal_chat


def test_q2cal_uses_ai_prompt_field_for_query():
    query_schema = cal_chat.q2cal__info()['schema']['query']

    assert query_schema['type'] == 'qtexta'
    assert query_schema['label'] == 'Query'
    assert query_schema['attrs']['rows'] == 4
    assert 'include known values, units, and constraints' in (
        query_schema['help_text']
    )


def bmi(mass='70 kg', height='1.75 m'):
    pass


def bmr(weight=70, height=175, age=30):
    pass


def _candidate(func, title):
    return {
        'name': func.__name__,
        'title': title,
        'description': f'{title}.',
        'code': f'def {func.__name__}(): pass',
    }


BMI = _candidate(bmi, 'Body Mass Index')
BMR = _candidate(bmr, 'Basal Metabolic Rate')


@pytest.fixture
def openai_reply(monkeypatch):
    functions = {'bmi': bmi, 'bmr': bmr}
    monkeypatch.setattr(
        cal_chat.QCals, 'addr', lambda name, scope='q': functions[name]
    )

    def reply(candidates, content):
        captured = {}

        def create_completion(messages, max_tokens):
            captured['messages'] = messages
            captured['max_tokens'] = max_tokens
            message = SimpleNamespace(content=content)
            return SimpleNamespace(choices=[SimpleNamespace(message=message)])

        monkeypatch.setattr(
            cal_chat.MyCalTools,
            'find_relevant_calculators',
            lambda _query: candidates,
        )
        monkeypatch.setattr(
            cal_chat, 'create_openai_chat_completion', create_completion
        )
        return captured

    return reply


def test_q2cal_returns_links_for_relevant_calculators(openai_reply):
    captured = openai_reply(
        [BMI, BMR],
        "[bmi('80 kg', '1.8 m'), bmr(weight=70, height=175, age=40)]",
    )

    result = cal_chat.q2cal('BMI for 80 kg and 1.8 m')

    assert isinstance(result, cal_chat.qhtml)
    assert 'bmi/mass/80%20kg/height/1.8%20m' in result
    assert '<span>bmi(mass=&#x27;80 kg&#x27;, height=&#x27;1.8 m&#x27;)</span>' in result
    assert 'bmr/weight/70/height/175/age/40' in result
    assert result.count('<div class="mb-2">') == 2
    assert 'Calculator: bmi' in captured['messages'][1]['content']
    assert 'Maximum calculator calls: 2' in captured['messages'][1]['content']


def test_q2cal_accepts_a_single_call(openai_reply):
    openai_reply([BMI], 'bmi()')

    result = cal_chat.q2cal('body mass index calculate')

    assert '/calc/add/?fname=bmi' in result


def test_q2cal_keeps_values_the_user_specified(openai_reply):
    openai_reply([BMI], "bmi(mass='70 kg', height='1.75 m')")

    result = cal_chat.q2cal('bmi for 70 kg and 1.75 m')

    assert 'bmi/mass/70%20kg/height/1.75%20m' in result


def test_q2cal_accepts_markdown_fenced_calls(openai_reply):
    openai_reply([BMI], "```python\n[bmi(mass='70 kg', height='1.75 m')]\n```")

    result = cal_chat.q2cal('bmi for 70 kg and 1.75 m')

    assert 'bmi/mass/70%20kg/height/1.75%20m' in result


def test_q2cal_accepts_calls_surrounded_by_prose(openai_reply):
    openai_reply([BMI], "Here you go:\n[bmi()]\nHope this helps.")

    assert '/calc/add/?fname=bmi' in cal_chat.q2cal('body mass index')


def test_q2cal_accepts_calls_returned_as_strings(openai_reply):
    openai_reply([BMI, BMR], '["bmi(mass=\'80 kg\')", "bmr(age=40)"]')

    result = cal_chat.q2cal('body mass index calculate')

    assert 'bmi/mass/80%20kg' in result
    assert 'bmr/age/40' in result


def test_q2cal_ignores_calls_outside_search_results(openai_reply):
    openai_reply([BMI], '[bmi(), not_a_qcalc_calculator()]')

    result = cal_chat.q2cal('body mass index calculate')

    assert result.count('<div class="mb-2">') == 1
    assert 'not_a_qcalc_calculator' not in result


def test_q2cal_error_includes_unusable_response(openai_reply):
    openai_reply([BMI], '[not_a_qcalc_calculator()]')

    with pytest.raises(ValueError, match=r'searched calculator.*not_a_qcalc'):
        cal_chat.q2cal('body mass index calculate')


def test_q2cal_deduplicates_calculators(openai_reply):
    openai_reply([BMI], '[bmi(70, 1.75), bmi(80, 1.8)]')

    result = cal_chat.q2cal('Calculate BMI')

    assert result.count('<div class="mb-2">') == 1
    assert 'bmi/mass/70/height/1.75' in result
    assert 'mass/80' not in result


def test_q2cal_stops_when_no_calculator_is_found(openai_reply):
    openai_reply([], '')

    with pytest.raises(ValueError, match='No relevant qCalc calculator'):
        cal_chat.q2cal('an unknown calculation')


def test_q2cal_rejects_result_count_outside_supported_range():
    with pytest.raises(ValueError, match='between 1 and 5'):
        cal_chat.q2cal('BMI for 70 kg and 1.75 m', n=6)


def test_calculator_call_link_skips_non_literal_arguments(openai_reply):
    call = ast.parse("bmi(mass=weight, height='1.8 m')", mode='eval').body

    link = cal_chat._calculator_call_link(call)

    assert '?path=bmi/height/1.8%20m"' in link


def test_calculator_call_link_supports_keyword_arguments(openai_reply):
    call = ast.parse("bmi(height='1.8 m', mass='80 kg')", mode='eval').body

    assert 'bmi/height/1.8%20m/mass/80%20kg' in cal_chat._calculator_call_link(call)
