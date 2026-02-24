import sqlite3
from decimal import Decimal
from typing import Optional, Tuple

from repos.product_repo import find_product_id
from repos.pack_repo import find_pack_id
from repos.store_repo import find_store_id
from repos.price_repo import (
    latest_prices_for_pack_with_packinfo,
    price_history,
    price_history_for_store,
)
from utils import unit_price_eur


# --------------------------------------------------
# Resolve
# --------------------------------------------------

def resolve_pack_id_or_reason(
    conn: sqlite3.Connection,
    name: str,
    brand: Optional[str],
    size: float,
    unit: str,
    note: Optional[str],
) -> Tuple[Optional[int], Optional[str]]:
    product_id = find_product_id(conn, name, brand)
    if product_id is None:
        return None, "product_missing"

    pack_id = find_pack_id(conn, product_id, size, unit, note)
    if pack_id is None:
        return None, "pack_missing"

    return pack_id, None


def resolve_pack_id(
    conn: sqlite3.Connection,
    name: str,
    brand: Optional[str],
    size: float,
    unit: str,
    note: Optional[str],
) -> Optional[int]:
    pack_id, _reason = resolve_pack_id_or_reason(conn, name, brand, size, unit, note)
    return pack_id


# --------------------------------------------------
# Latest + unit price
# --------------------------------------------------

def latest_with_unit_price(conn: sqlite3.Connection, pack_id: int):
    rows = latest_prices_for_pack_with_packinfo(conn, pack_id)

    result = []
    for r in rows:
        up, label = unit_price_eur(r["price_cents"], r["pack_size"], r["base_unit"])
        result.append(
            {
                "store": r["store"],
                "observed_on": r["observed_on"],
                "price_cents": r["price_cents"],
                "unit_price": up,
                "unit_label": label,
            }
        )
    return result


# --------------------------------------------------
# Cheapest ranking
# --------------------------------------------------

def cheapest_now(conn: sqlite3.Connection, pack_id: int):
    rows = latest_with_unit_price(conn, pack_id)
    return sorted(rows, key=lambda r: r["unit_price"])


# --------------------------------------------------
# History + unit price
# --------------------------------------------------

def history_with_unit_price(
    conn: sqlite3.Connection,
    pack_id: int,
    size: float,
    unit: str,
    store_id: Optional[int] = None,
):
    rows = price_history(conn, pack_id, store_id)

    result = []
    for r in rows:
        up, label = unit_price_eur(r["price_cents"], size, unit)
        result.append(
            {
                "store": r["store"],
                "observed_on": r["observed_on"],
                "price_cents": r["price_cents"],
                "unit_price": up,
                "unit_label": label,
            }
        )
    return result


# --------------------------------------------------
# Trend
# --------------------------------------------------

def trend(conn: sqlite3.Connection, pack_id: int, store_name: str):
    store_id = find_store_id(conn, store_name)
    if store_id is None:
        return None

    rows = price_history_for_store(conn, pack_id, store_id)
    if len(rows) < 2:
        return "not_enough"

    first = rows[0]["price_cents"]
    last = rows[-1]["price_cents"]

    diff = Decimal(last - first) / Decimal(100)
    percent = (Decimal(last - first) / Decimal(first) * Decimal(100))

    return {
        "store": store_name,
        "first": first,
        "last": last,
        "diff": diff.quantize(Decimal("0.01")),
        "percent": percent.quantize(Decimal("0.01")),
    }
