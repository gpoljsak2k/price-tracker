from datetime import date

from repos.store_repo import add_store
from repos.product_repo import add_product
from repos.pack_repo import add_pack
from repos.price_repo import add_price

from services.pricing_service import resolve_pack_id, latest_with_unit_price


def test_resolve_pack_id(conn):
    pid = add_product(conn, "Mleko 3.5%", "Alpsko")
    pack_id = add_pack(conn, pid, 1.0, "l", "tetrapak")

    resolved = resolve_pack_id(conn, "Mleko 3.5%", "Alpsko", 1.0, "l", "tetrapak")
    assert resolved == pack_id


def test_latest_with_unit_price(conn):
    sid = add_store(conn, "Mercator")
    pid = add_product(conn, "Mleko 3.5%", "Alpsko")
    pack_id = add_pack(conn, pid, 1.0, "l", "tetrapak")

    today = date.today().isoformat()
    add_price(conn, sid, pack_id, 119, today, "manual")

    rows = latest_with_unit_price(conn, pack_id)
    assert len(rows) == 1
    assert rows[0]["store"] == "Mercator"
    assert rows[0]["price_cents"] == 119
    assert "unit_price" in rows[0]
    assert "unit_label" in rows[0]
