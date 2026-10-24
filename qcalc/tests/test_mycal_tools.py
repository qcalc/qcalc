import qsett

qsett.init()

from calc import get_code
from calculators.all.general.user import mod_mycal_tools
from calculators.all.general.user.mod_mycal_validation import (
    format_calculator_validation_report,
    get_calculator_validation_report,
)
from calculators.all.general.user.mod_mycal_tools import MyCalTools


def test_reference_calculators_return_structured_results(monkeypatch):
    codes = {
        'addlen': "def addlen(x='1 m'):\n    return Qty(x)",
    }
    monkeypatch.setattr(
        mod_mycal_tools,
        'get_code',
        lambda name, show_meta=True, as_html=True: (
            codes.get(name, '') if not as_html else '<pre>unexpected</pre>'
        ),
    )

    result = MyCalTools.get_reference_calculators('addlen, missing, addlen')

    assert result['requested'] == ['addlen', 'missing']
    assert result['calculators'] == [{
        'name': 'addlen',
        'code': codes['addlen'],
    }]
    assert result['missing'] == ['missing']


def test_similar_calculator_uses_standard_result_and_clean_source(monkeypatch):
    monkeypatch.setattr(
        mod_mycal_tools.QSearch,
        'perform_search',
        lambda query, limit, node_types: [
            {
                'id': 'public-example',
                'node_type': 'c',
                'title': 'Public Example',
                'desc': '',
                'tags': '',
                'score': 20.0,
            },
            {
                'id': 'bmi',
                'node_type': 'c',
                'title': 'Calculate Body Mass Index',
                'desc': 'Calculate BMI from height and weight',
                'tags': 'health',
                'score': 18.0,
            },
        ],
    )
    monkeypatch.setattr(mod_mycal_tools.QCals, 'qc_user_list', ['bmi'])
    monkeypatch.setattr(
        mod_mycal_tools,
        'get_code',
        lambda name, show_meta=True, as_html=True: (
            "def bmi():\n    pass" if not as_html else '<pre>unexpected</pre>'
        ),
    )

    result = MyCalTools.find_similar_calculator(
        'Please create a body mass index calculator using height and weight'
    )

    assert result['found'] is True
    assert result['name'] == 'bmi'
    assert result['query'] == 'body mass index height weight'
    assert '<pre>' not in result['code']


def test_relevant_calculators_return_up_to_five_results(monkeypatch):
    monkeypatch.setattr(
        mod_mycal_tools.QSearch,
        'perform_search',
        lambda query, limit, node_types: [
            {
                'id': name,
                'node_type': 'c',
                'title': name.upper(),
                'desc': f'{name} description',
                'tags': '',
                'score': 10.0 - index,
            }
            for index, name in enumerate([
                'one', 'two', 'three', 'four', 'five', 'six'
            ])
        ],
    )
    monkeypatch.setattr(
        mod_mycal_tools.QCals,
        'qc_user_list',
        ['one', 'two', 'three', 'four', 'five', 'six'],
    )
    monkeypatch.setattr(
        mod_mycal_tools,
        'get_code',
        lambda name, show_meta=True, as_html=True: (
            f'def {name}():\n    pass' if not as_html else '<pre>unexpected</pre>'
        ),
    )

    result = MyCalTools.find_relevant_calculators('calculate something')

    assert [calculator['name'] for calculator in result] == [
        'one',
        'two',
        'three',
        'four',
        'five',
    ]


def test_similar_calculator_respects_exclusions(monkeypatch):
    monkeypatch.setattr(
        mod_mycal_tools.QSearch,
        'perform_search',
        lambda query, limit, node_types: [{
            'id': 'bmi',
            'node_type': 'c',
            'title': 'BMI',
            'desc': '',
            'tags': '',
            'score': 10.0,
        }],
    )
    monkeypatch.setattr(mod_mycal_tools.QCals, 'qc_user_list', ['bmi'])

    result = MyCalTools.find_similar_calculator(
        'body mass index',
        exclude_names=['bmi'],
    )

    assert result['found'] is False
    assert result['name'] == ''


def test_reference_source_mode_does_not_return_html_wrappers():
    source = get_code('gold', show_meta=True, as_html=False)

    assert '<pre>' not in source
    assert 'def gold(' in source


def test_format_does_not_add_missing_metadata():
    result = MyCalTools.format_calculator(
        'def add(x=1, y=2):\n return x+y\n'
    )
    validation = MyCalTools.validate_calculator(result['code'])

    assert "def add__info" not in result['code']
    assert validation['valid'] is False
    assert validation['checks'][-1]['name'] == 'metadata'
    assert "Missing metadata function: 'add__info'" in validation['error']


def test_validation_allows_additional_metadata_functions():
    result = MyCalTools.validate_calculator(
        "def projectile_motion(speed=10):\n"
        "    return speed\n\n"
        "def projectile_motion__info():\n"
        "    return {'title': 'Projectile Motion'}\n\n"
        "def projectile_motion__help(topic, detail):\n"
        "    return f'{topic}: {detail}'\n"
    )

    assert result['valid'] is True
    assert [check['name'] for check in result['checks']] == [
        'syntax',
        'security',
        'structure',
        'execution',
        'metadata',
        'default_execution',
    ]


def test_validation_allows_helper_functions():
    result = MyCalTools.validate_calculator(
        "def normalize(value):\n"
        "    return float(value)\n\n"
        "def calculate(value=1):\n"
        "    return normalize(value)\n\n"
        "def calculate__info():\n"
        "    return {'title': 'Calculate'}\n"
    )

    assert result['valid'] is True
    assert [check['name'] for check in result['checks']] == [
        'syntax',
        'security',
        'structure',
        'execution',
        'metadata',
        'default_execution',
    ]


def test_validation_reports_failing_stage_and_message():
    result = MyCalTools.validate_calculator(
        "def divide(x=1, y=0):\n"
        "    return x / y\n\n"
        "def divide__info():\n"
        "    return {'title': 'Divide'}\n"
    )

    assert result['valid'] is False
    assert result['failed_check'] == 'default_execution'
    assert result['checks'][-1]['name'] == 'default_execution'
    assert result['checks'][-1]['error_type'] == 'ValueError'
    assert 'division by zero' in result['error']


def test_validation_reports_syntax_location():
    result = MyCalTools.validate_calculator(
        "def broken(x=1)\n"
        "    return x\n"
    )

    assert result['valid'] is False
    assert result['failed_check'] == 'syntax'
    assert result['checks'][-1] == {
        'name': 'syntax',
        'passed': False,
        'error_type': 'SyntaxError',
        "message": "expected ':'",
        'line': 1,
        'column': 16,
    }


def test_validation_reports_security_failure():
    result = MyCalTools.validate_calculator(
        "import os\n\n"
        "def unsafe(x=1):\n"
        "    return x\n\n"
        "def unsafe__info():\n"
        "    return {'title': 'Unsafe'}\n"
    )

    assert result['valid'] is False
    assert result['failed_check'] == 'security'
    assert result['checks'][-1]['error_type'] == 'ImportError'
    assert "Importing 'os' is disallowed" in result['error']


def test_validation_reports_structure_failure():
    result = MyCalTools.validate_calculator(
        "def first(x=1):\n"
        "    return x\n\n"
        "def second(x=2):\n"
        "    return x\n"
    )

    assert result['valid'] is False
    assert result['failed_check'] == 'structure'
    assert 'Cannot determine the main calculator function' in result['error']


def test_validation_reports_top_level_execution_failure():
    result = MyCalTools.validate_calculator(
        "missing_name\n\n"
        "def calculate(x=1):\n"
        "    return x\n\n"
        "def calculate__info():\n"
        "    return {'title': 'Calculate'}\n"
    )

    assert result['valid'] is False
    assert result['failed_check'] == 'execution'
    assert result['checks'][-1]['error_type'] == 'NameError'


def test_human_validation_report_includes_stage_location_and_passed_checks():
    report = get_calculator_validation_report(
        "def broken(x=1)\n"
        "    return x\n"
    )

    message = format_calculator_validation_report(report)

    assert message == (
        "Validation failed (Syntax)\n"
        "SyntaxError: expected ':'\n"
        "Location: line 1, column 16"
    )


def test_human_validation_report_summarizes_success():
    report = get_calculator_validation_report(
        "def add(x=1, y=2):\n"
        "    return x + y\n\n"
        "def add__info():\n"
        "    return {'title': 'Add'}\n"
    )

    assert format_calculator_validation_report(report) == (
        'Validation successful: add'
    )


def test_syntax_report_does_not_repeat_line_number():
    report = get_calculator_validation_report(
        "def broken(value='unterminated):\n"
        "    return value\n"
    )

    message = format_calculator_validation_report(report)

    assert 'SyntaxError: unterminated string literal' in message
    assert 'Location: line 1, column ' in message
    assert message.count('line 1') == 1
