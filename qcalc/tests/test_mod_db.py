# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha
# Tests generated with AI assistance. Reviewed and validated by the author.

import qsett

qsett.init()

from types import SimpleNamespace

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.db import connection

import calc.qcatalog.mod_ucals as mod_ucals
from calc.mod_db import QDBTable
from calc.models import MyInput, MyStuff
from qutil import QThread


@pytest.fixture(scope="module", autouse=True)
def db_setup():
    old_name = connection.settings_dict["NAME"]
    connection.creation.create_test_db(verbosity=0, autoclobber=True)
    yield
    connection.creation.destroy_test_db(old_name, verbosity=0)
    connection.close()  # sqlite keeps the in-memory test db open until closed with the restored name


@pytest.fixture(autouse=True)
def clean():
    MyInput.objects.all().delete()
    MyStuff.objects.all().delete()
    QThread.set_req(None)
    yield
    QThread.set_req(None)


def _user(name):
    user, _ = get_user_model().objects.get_or_create(username=name)
    return user


def _login(user):
    QThread.set_req(SimpleNamespace(user=user))


@pytest.fixture
def alice():
    return _user("alice")


@pytest.fixture
def bob():
    return _user("bob")


@pytest.fixture
def table():
    return QDBTable(prefix="input")


# ---------- authentication ----------

@pytest.mark.parametrize("request_obj", [None, SimpleNamespace(user=AnonymousUser())], ids=["no-request", "anonymous"])
def test_calls_that_need_a_user_raise_permission_error(table, request_obj):
    QThread.set_req(request_obj)
    with pytest.raises(PermissionError):
        table.clear("bmi")
    with pytest.raises(PermissionError):
        table.set_variant("bmi", 0, {})
    with pytest.raises(PermissionError):
        table.delete_variant("bmi", 1)
    with pytest.raises(PermissionError):
        table.get_variants("bmi")


# ---------- variants ----------

def test_set_variant_assigns_next_free_id_and_default_description(table, alice):
    _login(alice)
    assert table.set_variant("bmi", 0, {"weight": 70}) == 1
    assert table.set_variant("bmi", 0, {"weight": 80}) == 2
    assert table.set_variant("age", 0, {}) == 1  # ids are counted per item
    assert [v.description for v in table.get_variants("bmi").order_by("variant_id")] == ["Variant 1", "Variant 2"]


def test_set_variant_keeps_explicit_id_and_description(table, alice):
    _login(alice)
    assert table.set_variant("bmi", 7, {"description": "My case", "weight": 70}) == 7
    record = table.get_variants("bmi").get()
    assert (record.variant_id, record.description) == (7, "My case")
    assert table.set_variant("bmi", 0, {}) == 8  # the next id follows the highest one


def test_set_variant_with_same_id_and_description_updates_the_data(table, alice):
    _login(alice)
    table.set_variant("bmi", 3, {"description": "d", "weight": 70})
    table.set_variant("bmi", 3, {"description": "d", "weight": 90})
    record = table.get_variants("bmi").get()
    assert record.item["weight"] == 90


def test_set_variant_with_same_id_and_new_description_updates_the_record(table, alice):
    _login(alice)
    table.set_variant("bmi", 3, {"description": "old", "weight": 70})
    table.set_variant("bmi", 3, {"description": "new", "weight": 90})
    record = table.get_variants("bmi").get()
    assert (record.description, record.item["weight"]) == ("new", 90)


def test_variants_are_private_to_their_user_and_prefix(table, alice, bob):
    _login(alice)
    table.set_variant("bmi", 0, {})
    QDBTable(prefix="other").set_variant("bmi", 0, {})
    assert table.get_variants("bmi").count() == 1
    _login(bob)
    assert table.get_variants("bmi").count() == 0


def test_delete_variant_and_clear(table, alice):
    _login(alice)
    table.set_variant("bmi", 0, {})
    table.set_variant("bmi", 0, {})
    assert table.delete_variant("bmi", 1) is True
    assert table.delete_variant("bmi", 1) is False
    table.clear("bmi")
    assert table.get_variants("bmi").count() == 0


def test_delete_variant_does_not_touch_another_users_variant(table, alice, bob):
    _login(alice)
    table.set_variant("bmi", 0, {})
    _login(bob)
    assert table.delete_variant("bmi", 1) is False
    _login(alice)
    assert table.get_variants("bmi").count() == 1


# ---------- reading a variant ----------

def test_get_variant_returns_own_variant_with_restored_data(table, alice):
    _login(alice)
    variant_id = table.set_variant("bmi", 0, {"weight": 70, "name": "x"})
    record = table.get_variant("bmi", variant_id, "alice")
    assert record.item["weight"] == 70 and record.item["name"] == "x"


def test_get_variant_of_a_missing_variant_is_none(table, alice):
    _login(alice)
    assert table.get_variant("bmi", 99, "alice") is None


def test_get_variant_of_another_user_needs_login_unless_it_is_an_example(table, alice, bob):
    _login(alice)
    variant_id = table.set_variant("bmi", 0, {"weight": 70})
    _login(bob)
    with pytest.raises(PermissionError):
        table.get_variant("bmi", variant_id, "alice")
    QThread.set_req(None)
    with pytest.raises(PermissionError):
        table.get_variant("bmi", variant_id, "alice")

    MyInput.objects.filter(user=alice).update(is_example=True)
    assert table.get_variant("bmi", variant_id, "alice").item["weight"] == 70


def test_get_var_info(table, alice):
    _login(alice)
    table.set_variant("bmi", 0, {})
    record = table.get_variants("bmi").get()
    assert table.get_var_info(0) is None
    assert table.get_var_info(record.id).pk == record.pk
    assert table.get_var_info(record.id + 1000) is None


# ---------- shared variants (token) ----------

def _shared_variant(user, function="bmi", is_shared=True):
    return MyInput.objects.create(user=user, object_id="input", item_id=function, variant_id=1, description="d",
                                  item={"function": function}, is_shared=is_shared)


def test_get_variant_from_token_needs_matching_function_and_a_shared_variant(table, alice):
    shared = _shared_variant(alice)
    assert shared.access_token
    assert table.get_variant_from_token("bmi", shared.access_token).pk == shared.pk
    assert table.get_variant_from_token("age", shared.access_token) is None
    assert table.get_variant_from_token("bmi", "unknown-token") is None


def test_unshared_variant_cannot_be_read_by_token(table, alice):
    shared = _shared_variant(alice)
    token = shared.access_token
    shared.is_shared = False
    shared.save()
    assert shared.access_token is None
    assert table.get_variant_from_token("bmi", token) is None


# ---------- shared calculators ----------

def test_is_shared_cal_follows_the_othcal_record(table, alice):
    _login(alice)
    assert table.is_shared_cal("bmi-bob") is False
    MyStuff.objects.create(user=alice, object_id="othcal", item_id="bmi-bob", item="")
    assert table.is_shared_cal("bmi-bob") is True


def test_save_shared_cal_reports_unknown_exists_and_saved(table, alice, monkeypatch):
    registered = []
    monkeypatch.setattr(mod_ucals, "register_shared_cal", lambda func_id, token: registered.append((func_id, token)))

    QThread.set_req(None)
    assert table.save_shared_cal("bmi-bob", "tok") is None  # not logged in: unknown

    _login(alice)
    assert table.save_shared_cal("bmi-alice", "tok") is None  # own calculator
    assert table.save_shared_cal("bmi-bob", "tok") == "0"  # check only, does not exist
    assert not MyStuff.objects.filter(object_id="othcal").exists()

    assert table.save_shared_cal("bmi-bob", "tok", check_only=False) == "2"
    assert registered == [("bmi-bob", "tok")]
    assert MyStuff.objects.filter(user=alice, object_id="othcal", item_id="bmi-bob").count() == 1

    assert table.save_shared_cal("bmi-bob", "tok", check_only=False) == "1"  # registered only once
    assert registered == [("bmi-bob", "tok")]


def test_delete_shared_cal_removes_the_users_record_and_unregisters(table, alice, bob, monkeypatch):
    unregistered = []
    monkeypatch.setattr(mod_ucals, "unregister_shared_cal", lambda func_id: unregistered.append(func_id))
    MyStuff.objects.create(user=alice, object_id="othcal", item_id="bmi-bob", item="")
    MyStuff.objects.create(user=bob, object_id="othcal", item_id="bmi-bob", item="")

    _login(alice)
    table.delete_shared_cal("bmi-bob")
    assert unregistered == ["bmi-bob"]
    assert not MyStuff.objects.filter(user=alice, object_id="othcal").exists()
    assert MyStuff.objects.filter(user=bob, object_id="othcal").exists()

    table.delete_shared_cal("bmi-bob")  # nothing left to delete
    assert unregistered == ["bmi-bob", "bmi-bob"]


def test_delete_shared_cal_keeps_the_record_of_the_owner(table, bob, monkeypatch):
    monkeypatch.setattr(mod_ucals, "unregister_shared_cal", lambda func_id: None)
    MyStuff.objects.create(user=bob, object_id="othcal", item_id="bmi-bob", item="")
    _login(bob)
    table.delete_shared_cal("bmi-bob")
    assert MyStuff.objects.filter(user=bob, object_id="othcal").exists()
