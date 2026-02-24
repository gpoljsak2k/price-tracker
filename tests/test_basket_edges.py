from repos.store_repo import add_store
from repos.product_repo import add_product
from repos.pack_repo import add_pack

from services.analytics_service import basket_totals


def test_basket_empty_when_no_prices_anywhere(conn):
    # store exists, but no prices recorded
    add_store(conn, "Mercator")

    pid = add_product(conn, "Mleko 3.5%", "Alpsko")
    add_pack(conn, pid, 1.0, "l", "tetrapak")

    items = [("Mleko 3.5%", "Alpsko", 1.0, "l", "tetrapak")]
    results, err = basket_totals(conn, items)

    assert err is None
    assert results == []


def test_basket_error_when_item_pack_missing(conn):
    add_store(conn, "Mercator")
    add_product(conn, "Mleko 3.5%", "Alpsko")
    # pack not added

    items = [("Mleko 3.5%", "Alpsko", 1.0, "l", "tetrapak")]
    results, err = basket_totals(conn, items)

    assert results is None
    assert err is not None
