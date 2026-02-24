from datetime import date

from repos.store_repo import add_store
from repos.product_repo import add_product
from repos.pack_repo import add_pack
from repos.price_repo import add_price

from services.analytics_service import basket_totals


def test_basket_shows_missing_items(conn):
    # stores
    merc = add_store(conn, "Mercator")
    spar = add_store(conn, "Spar")

    # item 1: milk
    milk_pid = add_product(conn, "Mleko 3.5%", "Alpsko")
    milk_pack = add_pack(conn, milk_pid, 1.0, "l", "tetrapak")

    # item 2: eggs
    eggs_pid = add_product(conn, "Jajca", "")
    eggs_pack = add_pack(conn, eggs_pid, 10.0, "pcs", None)

    today = date.today().isoformat()

    # Mercator has both
    add_price(conn, merc, milk_pack, 119, today, "manual")
    add_price(conn, merc, eggs_pack, 299, today, "manual")

    # Spar has only milk
    add_price(conn, spar, milk_pack, 109, today, "manual")

    items = [
        ("Mleko 3.5%", "Alpsko", 1.0, "l", "tetrapak"),
        ("Jajca", None, 10.0, "pcs", None),
    ]

    results, err = basket_totals(conn, items)
    assert err is None
    assert len(results) == 2

    by_store = {r["store"]: r for r in results}

    assert by_store["Mercator"]["covered"] == 2
    assert by_store["Mercator"]["missing"] == []

    assert by_store["Spar"]["covered"] == 1
    assert len(by_store["Spar"]["missing"]) == 1
    assert "Jajca" in by_store["Spar"]["missing"][0]
