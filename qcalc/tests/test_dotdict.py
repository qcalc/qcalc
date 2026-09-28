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


def test_readonly_missing_attribute_does_not_create():
    d = DotDict(readonly=True)

    try:
        _ = d.foo
        assert False, "expected AttributeError"
    except AttributeError:
        pass

    assert d == {}


def test_readonly_missing_key_does_not_create():
    d = DotDict(readonly=True)

    try:
        _ = d.key("foo")
        assert False, "expected KeyError"
    except KeyError:
        pass

    assert d == {}


def test_readonly_nested_dict_stays_readonly():
    d = DotDict(readonly=True)

    d.person = {
        "name": "John",
    }

    assert d.person.name == "John"

    try:
        _ = d.person.address
        assert False, "expected AttributeError"
    except AttributeError:
        pass


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


def test_list_of_dicts_is_converted_recursively():
    d = DotDict({
        "people": [
            {"name": "John"},
            {"name": "Jane"},
        ]
    })

    assert isinstance(d.people, list)
    assert isinstance(d.people[0], DotDict)
    assert isinstance(d.people[1], DotDict)
    assert d.people[0].name == "John"
    assert d.people[1].name == "Jane"


def test_readonly_list_of_dicts_stays_readonly():
    d = DotDict(
        {
            "people": [
                {"name": "John"},
            ]
        },
        readonly=True,
    )

    assert d.people[0].name == "John"

    try:
        _ = d.people[0].address
        assert False, "expected AttributeError"
    except AttributeError:
        pass


def test_tuple_of_dicts_is_converted_recursively():
    d = DotDict({
        "people": (
            {"name": "John"},
            {"name": "Jane"},
        )
    })

    assert isinstance(d.people, tuple)
    assert isinstance(d.people[0], DotDict)
    assert isinstance(d.people[1], DotDict)
    assert d.people[0].name == "John"
    assert d.people[1].name == "Jane"


def test_company_people_example_from_guide():
    d = DotDict({
        "company": {
            "people": [
                {"name": "John", "age": 35},
                {"name": "Jane", "age": 25},
            ]
        }
    })

    assert d.company.people[0].name == "John"
    assert d.company.people[1].age == 25
