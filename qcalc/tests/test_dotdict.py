from qutil import DotDict

def test_empty():
    d = DotDict()

    assert d == {}


def test_create_nested():
    d = DotDict()

    d.person.name = "John"
    d.person.age = 30

    assert d == {
        "person": {
            "name": "John",
            "age": 30,
        }
    }


def test_create_deep_nested():
    d = DotDict()

    d.person.address.city = "Dhaka"

    assert d == {
        "person": {
            "address": {
                "city": "Dhaka",
            }
        }
    }


def test_update_existing():
    d = DotDict()

    d.person.name = "John"
    d.person.name = "David"

    assert d.person.name == "David"
    assert d == {
        "person": {
            "name": "David",
        }
    }


def test_add_to_existing_nested_dict():
    d = DotDict()

    d.person.name = "John"
    d.person.age = 30
    d.person.city = "Dhaka"

    assert d.person.name == "John"
    assert d.person.age == 30
    assert d.person.city == "Dhaka"


def test_initialize_from_dict():
    d = DotDict({
        "person": {
            "name": "John",
            "address": {
                "city": "Dhaka"
            }
        }
    })

    assert d.person.name == "John"
    assert d.person.address.city == "Dhaka"


def test_assign_dict():
    d = DotDict()

    d.person = {
        "name": "John",
        "age": 30,
    }

    assert isinstance(d.person, DotDict)
    assert d.person.name == "John"
    assert d.person.age == 30


def test_missing_attribute_creates_dict():
    d = DotDict()

    result = d.foo

    assert isinstance(result, DotDict)
    assert "foo" in d


def test_missing_deep_attribute_creates_nested_dict():
    d = DotDict()

    d.a.b.c = 123

    assert d.a.b.c == 123
    assert d == {
        "a": {
            "b": {
                "c": 123,
            }
        }
    }


def test_normal_dict_access_still_works():
    d = DotDict()

    d.person.name = "John"

    assert d["person"]["name"] == "John"


def test_mixed_dict_and_dot_access():
    d = DotDict()

    d["person"] = DotDict()
    d["person"]["name"] = "John"

    assert d.person.name == "John"

    d.person.age = 30

    assert d["person"]["age"] == 30


def test_values_are_preserved():
    d = DotDict()

    d.number = 123
    d.text = "hello"
    d.boolean = True
    d.none = None
    d.items_list = [1, 2, 3]

    assert d.number == 123
    assert d.text == "hello"
    assert d.boolean is True
    assert d.none is None
    assert d.items_list == [1, 2, 3]


def test_nested_dict_is_converted_recursively():
    d = DotDict({
        "a": {
            "b": {
                "c": 123
            }
        }
    })

    assert isinstance(d.a, DotDict)
    assert isinstance(d.a.b, DotDict)
    assert d.a.b.c == 123
