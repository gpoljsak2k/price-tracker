from datetime import date

from repos.store_repo import add_store
from repos.product_repo import add_product
from repos.pack_repo import add_pack
from repos.price_repo import add_price

from services.pricing_service import cheapest_now, trend


def test_cheapest_now_sorts_by_unit_price(conn):
    sid_a = add_store(conn, "A")
    sid_b = add_store(conn, "B")

    pid = add_product(conn, "Mleko 3.5%", "Alpsko")
    pack_id = add_pack(conn, pid, 1.0, "l", "tetrapak")

    today = date.today().isoformat()

    # B is cheaper
    add_price(conn, sid_a, pack_id, 119, today, "manual")
    add_price(conn, sid_b, pack_id, 109, today, "manual")

    rows = cheapest_now(conn, pack_id)
    assert [r["store"] for r in rows] == ["B", "A"]


def test_trend_not_enough_when_only_one_price(conn):
    sid = add_store(conn, "Mercator")
    pid = add_product(conn, "Mleko 3.5%", "Alpsko")
    pack_id = add_pack(conn, pid, 1.0, "l", "tetrapak")

    today = date.today().isoformat()
    add_price(conn, sid, pack_id, 119, today, "manual")

    result = trend(conn, pack_id, "Mercator")
    assert result == "not_enough"


def test_trend_returns_none_for_missing_store(conn):
    pid = add_product(conn, "Mleko 3.5%", "Alpsko")
    pack_id = add_pack(conn, pid, 1.0, "l", "tetrapak")

    result = trend(conn, pack_id, "Neobstajam")
    assert result is None
