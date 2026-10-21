import qsett

qsett.init()

from calculators.all.general.user import mod_mycal_tools
from calculators.all.general.user.mod_mycal_tools import MyCalTools


def test_reference_calculators_return_structured_results(monkeypatch):
    codes = {
        'addlen': "def addlen(x='1 m'):\n    return Qty(x)",
    }
    monkeypatch.setattr(
        mod_mycal_tools,
        'get_code',
        lambda name, show_meta=True: codes.get(name, ''),
    )

    result = MyCalTools.get_reference_calculators('addlen, missing, addlen')

    assert result['requested'] == ['addlen', 'missing']
    assert result['calculators'] == [{
        'name': 'addlen',
        'code': codes['addlen'],
    }]
    assert result['missing'] == ['missing']


def test_prepare_and_validate_calculator():
    result = MyCalTools.prepare_calculator(
        'def add(x=1, y=2):\n return x+y\n',
        'add',
    )
    validation = MyCalTools.validate_calculator(result['code'])

    assert "def add__info" in result['code']
    assert validation['valid'] is True
    assert [check['name'] for check in validation['checks']] == [
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
    assert result['checks'][-1]['name'] == 'default_execution'
    assert 'division by zero' in result['error']
