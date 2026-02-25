import sqlite3
from typing import Optional

from repos.store_repo import add_store, find_store_id
from repos.price_repo import add_price
from services.pricing_service import resolve_pack_id_or_reason
from utils import euros_to_cents

def ensure_store(conn: sqlite3.Connection, store_name: str) -> int:
    store_id = find_store_id(conn, store_name)
    if store_id is not None:
        return store_id
    try:
        return add_store(conn, store_name)
    except sqlite3.IntegrityError:
        # v primeru duplikata
        store_id = find_store_id(conn, store_name)
        if store_id is None:
            raise
        return store_id

def ingest_price_observation(
    conn: sqlite3.Connection,
    *,
    store_name: str,
    name: str,
    brand: Optional[str],
    size: float,
    unit: str,
    note: Optional[str],
    price_eur,
    observed_on: str,
    source: str,
) -> int:
    store_id = ensure_store(conn, store_name)


    pack_id, reason = resolve_pack_id_or_reason(conn, name, brand, size, unit, note)
    if pack_id is None:
        if reason == "product_missing":
            raise ValueError("product_missing")
        if reason == "pack_missing":
            raise ValueError("pack_missing")
        raise ValueError("pack_missing")

    price_cents = euros_to_cents(str(price_eur))
    try:
        return add_price(conn, store_id, pack_id, price_cents, observed_on, source)
    except sqlite3.IntegrityError:
        # že obstaja cena za ta store+pack+datum -> idempotentno
        return 0