import qsett

qsett.init()

import pytest

from calculators.all.general.user import cal_myalias


def test_myalias_saves_normalized_alias_map(monkeypatch):
    stored = {}

    monkeypatch.setattr(cal_myalias.QCals, "quick_find_func", lambda name: "bmi" if name == "bmi" else None)
    monkeypatch.setattr(cal_myalias.QCalAlias, "clear", lambda: stored.clear())
    monkeypatch.setattr(cal_myalias.QCalAlias, "setp1", lambda alias, target: stored.__setitem__(alias, target))

    result = cal_myalias.myalias(
        aliases={
            "columns": ["Alias", "Calculator"],
            "data": [["  MyBmi  ", " BMI "], ["", ""], ["quick", "bmi"]],
        }
    )

    assert stored == {"mybmi": "bmi", "quick": "bmi"}
    assert result["Saved Aliases"] == 2


def test_myalias_rejects_invalid_alias(monkeypatch):
    monkeypatch.setattr(cal_myalias.QCals, "quick_find_func", lambda name: "bmi" if name == "bmi" else None)

    with pytest.raises(ValueError, match="Invalid alias"):
        cal_myalias.myalias(
            aliases={
                "columns": ["Alias", "Calculator"],
                "data": [["bad-alias", "bmi"]],
            }
        )


def test_myalias_rejects_missing_target(monkeypatch):
    monkeypatch.setattr(cal_myalias.QCals, "quick_find_func", lambda _name: None)

    with pytest.raises(ValueError, match="was not found"):
        cal_myalias.myalias(
            aliases={
                "columns": ["Alias", "Calculator"],
                "data": [["mybmi", "missing_target"]],
            }
        )


def test_myalias_input_reflects_saved_aliases(monkeypatch):
    monkeypatch.setattr(cal_myalias.QCalAlias, "getp", lambda _default=None: {"X1": "bmi", "abc": "bond"})

    inputs = cal_myalias.myalias__input({})
    assert inputs["aliases"]["columns"] == ["Alias", "Calculator"]
    assert inputs["aliases"]["data"] == [["abc", "bond"], ["x1", "bmi"]]


def test_myalias_rejects_alias_conflicting_with_existing_calculator(monkeypatch):
    monkeypatch.setattr(cal_myalias.QCals, "quick_find_func", lambda name: "bmi" if name in ("bmi", "bond") else None)

    with pytest.raises(ValueError, match="conflicts with existing calculator name"):
        cal_myalias.myalias(
            aliases={
                "columns": ["Alias", "Calculator"],
                "data": [["bmi", "bond"]],
            }
        )
