# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha
# Tests generated with AI assistance. Reviewed and validated by the author.

import qsett

qsett.init()

import pytest
from django.contrib.auth import get_user_model
from django.db import connection

import calc.mod_api_quota as aq
import calc.mod_cred_quota as cq
from calc.mod_api_keys import authenticate_api_key, list_api_keys
from calculators.all.general.user import cal_ucache as cu
from qutil import QThread


@pytest.fixture(scope="module", autouse=True)
def access_db():
    old_name = connection.settings_dict["NAME"]
    connection.creation.create_test_db(verbosity=0, autoclobber=True)
    yield
    connection.creation.destroy_test_db(old_name, verbosity=0)


@pytest.fixture
def me(monkeypatch):
    cq._usage().all().delete()
    monkeypatch.setattr(aq, "_PURGE_PROBABILITY", 0)
    user, _ = get_user_model().objects.get_or_create(username="calc_user")
    for key in list_api_keys(user):
        key.delete()

    class Req:
        pass

    req = Req()
    req.user = user
    monkeypatch.setattr(QThread, "get_req", classmethod(lambda cls: req))
    return user


def test_calculator_is_registered_but_not_exposed_through_the_api():
    from calc import QCals
    from calc.mod_api_core import api_enabled

    assert "api_access" in QCals.qc_dict
    assert not api_enabled("api_access")  # a key must never be able to mint more keys
    info = cu.api_access__info()
    assert info["remember"] is False and info["xpr"] is False and info["url"] is False


def test_login_required(monkeypatch):
    class Anon:
        is_authenticated = False

    class Req:
        user = Anon()

    monkeypatch.setattr(QThread, "get_req", classmethod(lambda cls: Req()))
    with pytest.raises(Exception, match="login"):
        cu.api_access()


def test_status_lists_no_keys_and_shows_limits_and_base_url(me):
    out = cu.api_access()
    assert out["My API Keys"]["data"] == []
    assert "/calc/api/v1/" in out["Base URL"]
    assert "runs/day" in out["Limits per key"]
    assert out["Max active keys"] == 5


def test_create_shows_key_once_and_it_authenticates(me):
    out = cu.api_access("create", name="spreadsheet")
    raw = str(out["New API Key"])
    assert raw.startswith("qck_")
    assert "only once" in str(out["Important"])

    listing = cu.api_access()  # the plain key is never shown again
    assert raw not in str(listing)
    row = listing["My API Keys"]["data"][0]
    assert row[0] == "spreadsheet" and row[1].endswith("_...") and row[2] == "Active" and row[4] == "Never"

    assert authenticate_api_key(raw).user == me
    assert cu.api_access()["My API Keys"]["data"][0][4] != "Never"  # first use is recorded


def test_create_rejects_duplicates_blank_names_and_the_sixth_key(me):
    with pytest.raises(Exception, match="name is required"):
        cu.api_access("create", name="")
    for i in range(5):
        cu.api_access("create", name=f"k{i}")
    with pytest.raises(Exception, match="at most 5"):
        cu.api_access("create", name="k5")
    with pytest.raises(Exception, match="already have a key named"):
        cu.api_access("create", name="K0")


def test_revoke_then_delete_by_prefix(me):
    raw = str(cu.api_access("create", name="tmp")["New API Key"])
    prefix = raw.split("_")[1]

    out = cu.api_access("revoke", prefix=prefix)
    assert "can no longer be used" in out["Revoked"]
    assert out["My API Keys"]["data"][0][2] == "Revoked"
    assert authenticate_api_key(raw) is None

    out = cu.api_access("delete", prefix=prefix)
    assert prefix in out["Deleted"] and out["My API Keys"]["data"] == []


def test_unknown_prefix_and_unsupported_action(me):
    with pytest.raises(Exception, match="No API key with prefix"):
        cu.api_access("revoke", prefix="deadbeef")
    with pytest.raises(Exception, match="Unsupported action"):
        cu.api_access("bogus")


def test_status_shows_runs_used_against_limits(me, monkeypatch):
    monkeypatch.setattr(aq.settings, "QCALC_API_KEY_QUOTA", "key_day=5,key_month=50,user_day=0", raising=False)
    cu.api_access("create", name="counted")
    aq.consume_api_quota(list_api_keys(me)[0])
    row = cu.api_access()["My API Keys"]["data"][0]
    assert row[5] == "1 / 5" and row[6] == "1 / 50"
