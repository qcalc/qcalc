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
    assert table.select(skip_blank=False) == [
        {"id": 1, "name": "A"},
        {"id": 2, "name": "B"},
    ]


def test_qtable_rejects_duplicate_columns_and_ragged_rows():
    with pytest.raises(ValueError, match="unique"):
        QTable({"columns": ["id", "id"], "data": [[1, 2]]})

    with pytest.raises(ValueError, match="row 1"):
        QTable({"columns": ["id", "name"], "data": [[1]]})


def test_qtable_select_find_and_column():
    table = make_products()

    assert table.column("name") == ["Laptop", "Monitor"]
    assert table.find(name="Monitor")["id"] == 2
    assert table.select(price=1200) == [
        {"id": 1, "name": "Laptop", "price": 1200}
    ]


def test_unknown_columns_are_reported():
    table = make_products()

    with pytest.raises(KeyError, match="Unknown column"):
        table.column("missing")
    with pytest.raises(KeyError, match="Unknown column"):
        table.find(missing=1)
    with pytest.raises(KeyError, match="Unknown column"):
        table.select(missing=1)


def test_qtable_rejects_dict_without_columns_and_data():
    with pytest.raises(TypeError, match="columns"):
        QTable({"x": [1]})


# QTable: schema and validation


def test_schema_accepts_json_type_names():
    table = QTable({"columns": ["n"], "data": [["5"]]}, schema={"n": {"type": "integer"}})
    table.validate(raise_exception=True)

    assert table.select() == [{"n": 5}]
    with pytest.raises(ValueError, match="unknown schema type"):
        QTable({"columns": ["n"], "data": []}, schema={"n": {"type": "weird"}})


def test_schema_required_rejects_whitespace_only_value():
    table = QTable({"columns": ["a", "b"], "data": [["   ", 1]]},
                   schema={"a": {"type": str, "required": True}}, validate=False)

    with pytest.raises(ValueError, match="required"):
        table.validate(raise_exception=True)


def test_schema_int_rejects_fractions_and_names_the_column():
    def table(value):
        return QTable({"columns": ["n"], "data": [[value]]}, schema={"n": int}, name="t")

    whole = table(3.0)
    whole.validate(raise_exception=True)
    assert whole.select() == [{"n": 3}]
    with pytest.raises(ValueError, match="t: invalid n: 3.7"):
        table(3.7).validate(raise_exception=True)
    with pytest.raises(ValueError, match="t: invalid n: 'abc'"):
        table("abc").validate(raise_exception=True)


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
        validate=False,
    )

    result = table.validate()
    assert not result["valid"]
    assert "required" in result["errors"][0]


def test_schema_rejects_value_outside_range():
    table = QTable(
        {"columns": ["id", "price"], "data": [[1, -2]]},
        schema={"price": {"type": float, "min": 0}},
        primary_key="id",
        validate=False,
    )

    with pytest.raises(ValueError, match="at least"):
        table.validate(raise_exception=True)


def test_primary_and_unique_keys_are_checked():
    table = QTable(
        {"columns": ["id", "email"], "data": [[1, "a@x"], [2, "a@x"]]},
        primary_key="id",
        unique="email",
        validate=False,
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


# QTable: input normalization and mapping


def test_select_skips_blank_and_repeated_header_rows():
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

    assert table.select() == [{"id": 1, "name": "A"}]


def test_schema_cast_replaces_per_read_casts():
    table = QTable(
        {"columns": ["id", "amount"], "data": [["1", "12.5"]]},
        schema={"id": {"cast": int}, "amount": {"cast": float}},
    )
    table.validate(raise_exception=True)

    assert table.select() == [{"id": 1, "amount": 12.5}]


def test_to_map_returns_key_value_mapping():
    table = QTable(
        {"columns": ["code", "label"], "data": [["A", "Alpha"], ["B", "Beta"]]}
    )

    assert table.to_map("code", "label") == {
        "A": "Alpha",
        "B": "Beta",
    }


def test_to_map_composite_key_and_value_use_tuples():
    table = QTable(
        {"columns": ["a", "b", "c", "d"], "data": [[1, 2, 3, 4], ["", "", "", ""]]}
    )

    assert table.to_map(["a", "b"], ["c", "d"]) == {(1, 2): (3, 4)}


def test_to_map_rejects_duplicate_keys_unless_allowed():
    table = QTable({"columns": ["k", "v"], "data": [[1, "x"], [1, "y"]]}, name="t")

    with pytest.raises(ValueError, match="t: Duplicate key: 1"):
        table.to_map("k", "v")
    assert table.to_map("k", "v", unique=False) == {1: "y"}
    with pytest.raises(KeyError, match="Unknown column"):
        table.to_map("k", "missing")

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


def test_qbase_register_unregister_and_duplicate_names():
    db = QBase()
    db.register("products", make_products())

    with pytest.raises(ValueError, match="already registered"):
        db.register("products", make_products())

    with pytest.raises(KeyError, match="Register both tables"):
        db.relate("products", "missing")

    assert db.unregister("products").nrows == 2
    assert "products" not in db


def test_qbase_serializes_tables_and_relationships():
    db = QBase({"products": make_products(), "items": make_items()})
    db.relate("products", "items", master_key="id", detail_key="product_id")

    payload = db.to_dict()
    assert set(payload) == {"tables", "relations"}
    assert set(payload["tables"]) == {"products", "items"}
    assert payload["relations"][0]["master"] == "products"


def test_qbase_round_trip_keeps_schema_and_keys():
    db = QBase({"products": make_products(), "items": make_items()})
    db.relate("products", "items", master_key="id", detail_key="product_id")

    copy = QBase(**db.to_dict())

    assert copy["products"].primary_key == ["id"]
    assert copy["products"].schema_dict()["price"]["min"] == 0
    assert copy.validate()["valid"]
    assert copy.relations[0].to_dict() == db.relations[0].to_dict()


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


def test_assert_columns_normalizes_headers_and_updates_key_metadata():
    table = QTable(
        {"columns": [" ID ", " Product Name "], "data": [[1, "Desk"]]},
        primary_key=" ID ",
    )

    resolved = table.assert_columns(["id", "Product Name"])

    assert resolved == {"id": "id", "Product Name": "Product Name"}
    assert table.columns == ["id", "Product Name"]
    assert table.primary_key == ["id"]
    assert table.get(1)["Product Name"] == "Desk"


def test_assert_unique_returns_canonical_values():
    table = QTable(
        {"columns": ["Code"], "data": [[" A "], ["B"]]}
    )

    assert table.assert_unique("Code") == ["A", "B"]


def test_assert_unique_detects_case_insensitive_duplicates():
    table = QTable(
        {"columns": ["Code"], "data": [["abc"], [" ABC "]]}
    )

    with pytest.raises(ValueError, match="duplicate"):
        table.assert_unique("Code")


def test_assert_unique_pairs_returns_normalized_pairs():
    table = QTable(
        {"columns": ["From", "To"], "data": [["A", "B"], ["B", "C"]]}
    )

    assert table.assert_unique_pairs("From", "To") == {("a", "b"), ("b", "c")}


def test_assert_foreign_key_checks_child_against_parent():
    parent = QTable({"columns": ["Code"], "data": [["A"], ["B"]]}, name="parent")
    child = QTable({"columns": ["Parent Code"], "data": [["A"], ["B"]]}, name="child")

    child.assert_foreign_key(parent, "Parent Code", "Code")


def test_assert_foreign_key_rejects_unknown_child_value():
    parent = QTable({"columns": ["Code"], "data": [["A"]]}, name="parent")
    child = QTable({"columns": ["Parent Code"], "data": [["X"]]}, name="child")

    with pytest.raises(ValueError, match="not found"):
        child.assert_foreign_key(parent, "Parent Code", "Code")


def test_assert_complete_cross_join():
    table = QTable({
        "columns": ["From", "To"],
        "data": [["A", "X"], ["A", "Y"], ["B", "X"], ["B", "Y"]],
    })

    assert table.assert_complete_cross_join(
        "From", "To", ["A", "B"], ["X", "Y"]
    ) is None


def test_assert_columns_match_domain_normalizes_matrix_headers():
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

