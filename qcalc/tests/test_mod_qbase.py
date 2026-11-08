"""Tests for qcore.mod_qbase.

Run from the qCalc project root:

    pytest -q tests/test_mod_qbase.py
"""

import pytest

from qcore.qb_qbase import QBase, QRelation
from qcore.qb_qtable import QTable


def make_products():
    return QTable(
        data={
            "columns": ["id", "name", "price"],
            "data": [
                [1, "Laptop", 1200],
                [2, "Monitor", 300],
            ],
        },
        schema={
            "id": int,
            "name": {"type": str, "required": True},
            "price": {"type": float, "min": 0},
        },
        primary_key="id",
        name="products",
    )


def make_items():
    return QTable(
        data={
            "columns": ["id", "product_id", "qty"],
            "data": [[1, 1, 2], [2, 1, 3], [3, 2, 1]],
        },
        primary_key="id",
        name="items",
    )


# QTable: construction and access


def test_qtable_accepts_qtbl_payload_and_returns_detached_data():
    source = {"columns": ["id", "name"], "data": [[1, "A"]]}
    table = QTable(source, primary_key="id")

    assert table.shape == (1, 2)
    assert table.columns == ["id", "name"]
    assert table.row(0) == [1, "A"]
    assert table.get(1) == {"id": 1, "name": "A"}

    exported = table.to_dict()
    exported["data"][0][1] = "changed"
    assert table.get(1)["name"] == "A"


def test_qtable_accepts_record_dictionaries():
    table = QTable(
        [{"id": 1, "name": "A"}, {"id": 2, "name": "B"}],
        primary_key="id",
    )

    assert table.columns == ["id", "name"]
    assert table.records(skip_blank=False) == [
        {"id": 1, "name": "A"},
        {"id": 2, "name": "B"},
    ]


def test_qtable_rejects_duplicate_columns_and_ragged_rows():
    with pytest.raises(ValueError, match="unique"):
        QTable({"columns": ["id", "id"], "data": [[1, 2]]})

    with pytest.raises(ValueError, match="row 1"):
        QTable({"columns": ["id", "name"], "data": [[1]]})


def test_qtable_filter_find_and_column():
    table = make_products()

    assert table.column("name") == ["Laptop", "Monitor"]
    assert table.find(name="Monitor")["id"] == 2
    assert table.filter(price=1200) == [
        {"id": 1, "name": "Laptop", "price": 1200}
    ]


def test_unknown_columns_are_reported():
    table = make_products()

    with pytest.raises(KeyError, match="Unknown column"):
        table.column("missing")
    with pytest.raises(KeyError, match="Unknown column"):
        table.find(missing=1)
    with pytest.raises(KeyError, match="Unknown column"):
        table.filter(missing=1)


def test_qtable_rejects_dict_without_columns_and_data():
    with pytest.raises(TypeError, match="columns"):
        QTable({"x": [1]})


# QTable: schema and validation


def test_schema_accepts_json_type_names():
    table = QTable({"columns": ["n"], "data": []}, schema={"n": {"type": "integer"}})

    assert table.add({"n": "5"}) == {"n": 5}
    with pytest.raises(ValueError, match="unknown schema type"):
        QTable({"columns": ["n"], "data": []}, schema={"n": {"type": "weird"}})


def test_schema_required_rejects_whitespace_only_value():
    table = QTable({"columns": ["a"], "data": []},
                   schema={"a": {"type": str, "required": True}})

    with pytest.raises(ValueError, match="required"):
        table.add({"a": "   "})


def test_schema_int_rejects_fractions_and_names_the_column():
    table = QTable({"columns": ["n"], "data": []}, schema={"n": int}, name="t")

    assert table.add({"n": 3.0}) == {"n": 3}
    with pytest.raises(ValueError, match="t: invalid n: 3.7"):
        table.add({"n": 3.7})
    with pytest.raises(ValueError, match="t: invalid n: 'abc'"):
        table.add({"n": "abc"})


def test_schema_coercion_and_constraints():
    table = QTable(
        {"columns": ["id", "name", "price"], "data": [["1", "Desk", "25.5"]]},
        schema={
            "id": int,
            "name": {"type": str, "required": True},
            "price": {"type": float, "min": 0},
        },
        primary_key="id",
    )

    result = table.validate()
    assert result == {"valid": True, "errors": []}
    assert table.get(1) == {"id": 1, "name": "Desk", "price": 25.5}


def test_schema_rejects_missing_required_value():
    table = QTable(
        {"columns": ["id", "name"], "data": [[1, ""]]},
        schema={"name": {"type": str, "required": True}},
        primary_key="id",
    )

    result = table.validate()
    assert not result["valid"]
    assert "required" in result["errors"][0]


def test_schema_rejects_value_outside_range():
    table = QTable(
        {"columns": ["id", "price"], "data": [[1, -2]]},
        schema={"price": {"type": float, "min": 0}},
        primary_key="id",
    )

    with pytest.raises(ValueError, match="at least"):
        table.validate(raise_exception=True)


def test_primary_and_unique_keys_are_checked():
    table = QTable(
        {"columns": ["id", "email"], "data": [[1, "a@x"], [2, "a@x"]]},
        primary_key="id",
        unique="email",
    )

    result = table.validate()
    assert not result["valid"]
    assert "duplicate key" in result["errors"][0]


def test_composite_primary_key():
    table = QTable(
        {
            "columns": ["order_id", "line_no", "sku"],
            "data": [[10, 1, "A"], [10, 2, "B"]],
        },
        primary_key=["order_id", "line_no"],
    )

    assert table.get((10, 2)) == {
        "order_id": 10,
        "line_no": 2,
        "sku": "B",
    }


# QTable: CRUD and atomicity


def test_add_update_delete_and_clear():
    table = make_products()

    added = table.add({"id": "3", "name": "Keyboard", "price": "50"})
    assert added == {"id": 3, "name": "Keyboard", "price": 50.0}

    updated = table.update(3, {"price": "45"})
    assert updated["price"] == 45.0

    assert table.delete(3) is True
    assert table.delete(3) is False
    assert table.nrows == 2

    table.clear()
    assert table.shape == (0, 3)


def test_add_many_is_atomic_when_a_row_is_invalid():
    table = make_products()
    before = table.to_dict()

    with pytest.raises((ValueError, TypeError)):
        table.add_many([
            {"id": 3, "name": "Keyboard", "price": 50},
            {"id": 4, "name": "", "price": 20},
        ])

    assert table.to_dict() == before


def test_add_rejects_duplicate_primary_key_without_mutating_table():
    table = make_products()
    before = table.to_dict()

    with pytest.raises(ValueError, match="duplicate key"):
        table.add({"id": 1, "name": "Duplicate", "price": 10})

    assert table.to_dict() == before


def test_update_rejects_unknown_record():
    with pytest.raises(KeyError, match="record not found"):
        make_products().update(999, {"name": "Missing"})


# QTable: input normalization and mapping


def test_records_skips_blank_and_repeated_header_rows():
    table = QTable(
        {
            "columns": ["id", "name"],
            "data": [
                ["id", "name"],
                [1, " A "],
                ["", "  "],
            ],
        }
    )

    assert table.records() == [{"id": 1, "name": "A"}]


def test_read_casts_columns():
    table = QTable(
        {"columns": ["id", "amount"], "data": [["1", "12.5"]]}
    )

    assert table.read(casts={"id": int, "amount": float}) == [
        {"id": 1, "amount": 12.5}
    ]


def test_read_can_return_key_value_mapping():
    table = QTable(
        {"columns": ["code", "label"], "data": [["A", "Alpha"], ["B", "Beta"]]}
    )

    assert table.read(key="code", value="label") == {
        "A": "Alpha",
        "B": "Beta",
    }


# QRelation and QBase


def test_relation_validation_and_master_detail_lookup():
    db = QBase({"products": make_products(), "items": make_items()})
    db.relate(
        master="products",
        detail="items",
        master_key="id",
        detail_key="product_id",
    )

    assert db.validate()["valid"]
    assert [row["id"] for row in db.master_detail("products", "items", 1)] == [1, 2]


def test_relation_detects_orphan_foreign_key():
    products = make_products()
    items = QTable(
        {"columns": ["id", "product_id"], "data": [[1, 999]]},
        primary_key="id",
    )
    db = QBase({"products": products, "items": items})
    db.relate("products", "items", master_key="id", detail_key="product_id")

    result = db.validate()
    assert not result["valid"]
    assert any("not found" in error for error in result["errors"]["relation_1"])


def test_relation_supports_nullable_foreign_keys():
    products = make_products()
    items = QTable(
        {"columns": ["id", "product_id"], "data": [[1, None]]},
        primary_key="id",
    )
    db = QBase({"products": products, "items": items})
    db.relate(
        "products", "items",
        master_key="id", detail_key="product_id", nullable=True,
    )

    assert db.validate()["valid"]


def test_one_to_one_rejects_duplicate_detail_reference():
    products = make_products()
    items = QTable(
        {"columns": ["id", "product_id"], "data": [[1, 1], [2, 1]]},
        primary_key="id",
    )
    db = QBase({"products": products, "items": items})
    db.relate(
        "products", "items",
        master_key="id", detail_key="product_id",
        relation_type="one-to-one",
    )

    result = db.validate()
    assert not result["valid"]
    assert "one-to-one" in result["errors"]["relation_1"][0]


def test_restrict_delete_prevents_deleting_referenced_master():
    db = QBase({"products": make_products(), "items": make_items()})
    db.relate("products", "items", master_key="id", detail_key="product_id")

    with pytest.raises(ValueError, match="referenced by"):
        db.delete("products", 1)

    assert db["products"].get(1) is not None


def test_cascade_delete_removes_detail_rows():
    db = QBase({"products": make_products(), "items": make_items()})
    db.relate(
        "products", "items",
        master_key="id", detail_key="product_id",
        on_delete="cascade",
    )

    assert db.delete("products", 1)
    assert db["products"].get(1) is None
    assert db["items"].filter(product_id=1) == []
    assert db["items"].nrows == 1


def test_set_null_delete_updates_detail_foreign_key():
    db = QBase({"products": make_products(), "items": make_items()})
    db.relate(
        "products", "items",
        master_key="id", detail_key="product_id",
        on_delete="set_null", nullable=True,
    )

    assert db.delete("products", 1)
    assert db["items"].filter(product_id=None) == [
        {"id": 1, "product_id": None, "qty": 2},
        {"id": 2, "product_id": None, "qty": 3},
    ]


def test_set_null_requires_nullable_relationship():
    db = QBase({"products": make_products(), "items": make_items()})
    db.relate(
        "products", "items",
        master_key="id", detail_key="product_id",
        on_delete="set_null", nullable=False,
    )

    with pytest.raises(ValueError, match="requires nullable"):
        db.delete("products", 1)

    # Failed delete restores both master and detail tables.
    assert db["products"].get(1) is not None
    assert len(db["items"].filter(product_id=1)) == 2


def test_qbase_register_unregister_and_duplicate_names():
    db = QBase()
    db.register("products", make_products())

    with pytest.raises(ValueError, match="already registered"):
        db.register("products", make_products())

    with pytest.raises(KeyError, match="Register both tables"):
        db.relate("products", "missing")

    assert db.unregister("products").nrows == 2
    assert "products" not in db


def test_cascade_delete_applies_rules_on_grandchildren():
    def table(rows, cols):
        return QTable({"columns": cols, "data": rows}, primary_key="id")

    def build(grand_rule):
        db = QBase({"p": table([[1]], ["id"]),
                    "c": table([[10, 1]], ["id", "pid"]),
                    "g": table([[100, 10]], ["id", "cid"])})
        db.relate("p", "c", master_key="id", detail_key="pid", on_delete="cascade")
        db.relate("c", "g", master_key="id", detail_key="cid", on_delete=grand_rule)
        return db

    db = build("cascade")
    assert db.delete("p", 1)
    assert (db["p"].nrows, db["c"].nrows, db["g"].nrows) == (0, 0, 0)
    assert db.validate()["valid"]

    db = build("restrict")
    with pytest.raises(ValueError, match="referenced by g"):
        db.delete("p", 1)
    assert (db["p"].nrows, db["c"].nrows, db["g"].nrows) == (1, 1, 1)


def test_cascade_delete_handles_self_reference():
    tree = QTable({"columns": ["id", "parent"], "data": [[1, None], [2, 1], [3, 2], [4, None]]},
                  primary_key="id")
    db = QBase({"tree": tree})
    db.relate("tree", "tree", master_key="id", detail_key="parent",
              on_delete="cascade", nullable=True)

    assert db.delete("tree", 1)
    assert [r["id"] for r in tree.records(skip_blank=False)] == [4]


def test_qbase_serializes_tables_and_relationships():
    db = QBase({"products": make_products(), "items": make_items()})
    db.relate("products", "items", master_key="id", detail_key="product_id")

    payload = db.to_dict()
    assert set(payload) == {"tables", "relations"}
    assert set(payload["tables"]) == {"products", "items"}
    assert payload["relations"][0]["master"] == "products"


def test_qbase_round_trip_keeps_schema_and_keys():
    db = QBase({"products": make_products(), "items": make_items()})
    db.relate("products", "items", master_key="id", detail_key="product_id",
              on_delete="cascade")

    copy = QBase(**db.to_dict())

    assert copy["products"].primary_key == ["id"]
    assert copy["products"].schema_dict()["price"]["min"] == 0
    assert copy.validate()["valid"]
    assert copy.delete("products", 1)
    assert copy["items"].nrows == 1
    assert db["items"].nrows == 3


def test_relation_rejects_mismatched_composite_key_lengths():
    with pytest.raises(ValueError, match="same number"):
        QRelation(
            "master", "detail",
            master_key=["a", "b"],
            detail_key=["x"],
        )


def test_many_to_many_requires_a_junction_table():
    with pytest.raises(ValueError, match="junction table"):
        QRelation("a", "b", relation_type="many-to-many")


# Existing qCalc table validation exposed through QTable methods.


def test_require_columns_normalizes_headers_and_updates_key_metadata():
    table = QTable(
        {"columns": [" ID ", " Product Name "], "data": [[1, "Desk"]]},
        primary_key=" ID ",
    )

    resolved = table.assert_columns(["id", "Product Name"])

    assert resolved == {"id": "id", "Product Name": "Product Name"}
    assert table.columns == ["id", "Product Name"]
    assert table.primary_key == ["id"]
    assert table.get(1)["Product Name"] == "Desk"


def test_require_unique_returns_canonical_values():
    table = QTable(
        {"columns": ["Code"], "data": [[" A "], ["B"]]}
    )

    assert table.assert_unique("Code") == ["A", "B"]


def test_require_unique_detects_case_insensitive_duplicates():
    table = QTable(
        {"columns": ["Code"], "data": [["abc"], [" ABC "]]}
    )

    with pytest.raises(ValueError, match="duplicate"):
        table.assert_unique("Code")


def test_require_unique_pairs_returns_normalized_pairs():
    table = QTable(
        {"columns": ["From", "To"], "data": [["A", "B"], ["B", "C"]]}
    )

    assert table.assert_unique_pairs("From", "To") == {("a", "b"), ("b", "c")}


def test_require_values_subset_checks_child_against_parent():
    parent = QTable({"columns": ["Code"], "data": [["A"], ["B"]]}, name="parent")
    child = QTable({"columns": ["Parent Code"], "data": [["A"], ["B"]]}, name="child")

    child.assert_foreign_key(parent, "Parent Code", "Code")


def test_require_values_subset_rejects_unknown_child_value():
    parent = QTable({"columns": ["Code"], "data": [["A"]]}, name="parent")
    child = QTable({"columns": ["Parent Code"], "data": [["X"]]}, name="child")

    with pytest.raises(ValueError, match="not found"):
        child.assert_foreign_key(parent, "Parent Code", "Code")


def test_require_complete_pair_grid():
    table = QTable({
        "columns": ["From", "To"],
        "data": [["A", "X"], ["A", "Y"], ["B", "X"], ["B", "Y"]],
    })

    assert table.assert_complete_cross_join(
        "From", "To", ["A", "B"], ["X", "Y"]
    ) is None


def test_require_value_columns_normalizes_matrix_headers():
    master = QTable(
        {"columns": ["Location"], "data": [["North"], ["South"]]},
        name="locations",
    )
    matrix = QTable(
        {"columns": ["Source", " north ", " south "],
         "data": [["North", 1, 2]]},
        name="cost_matrix",
    )

    result = matrix.assert_columns_match_domain(
        master, "Location", matrix_reserved_cols=["Source"]
    )

    assert matrix.columns == ["Source", "North", "South"]
    assert result["master_values"] == ["North", "South"]

