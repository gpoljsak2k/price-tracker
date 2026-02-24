import sqlite3
from typing import Optional


def add_price(
    conn: sqlite3.Connection,
    store_id: int,
    pack_id: int,
    price_cents: int,
    observed_on: str,
    source: str = "manual",
) -> int:
    cur = conn.execute(
        """
        INSERT INTO price_observation(
            store_id,
            product_pack_id,
            price_cents,
            observed_on,
            source
        )
        VALUES (?,?,?,?,?)
        """,
        (store_id, pack_id, price_cents, observed_on, source),
    )
    conn.commit()
    return int(cur.lastrowid)


def latest_prices_for_pack_with_packinfo(
    conn: sqlite3.Connection,
    pack_id: int,
) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT
          s.name AS store,
          po.observed_on,
          po.price_cents,
          pp.pack_size,
          pp.base_unit
        FROM price_observation po
        JOIN store s ON s.id = po.store_id
        JOIN product_pack pp ON pp.id = po.product_pack_id
        JOIN (
          SELECT store_id, MAX(observed_on) AS max_date
          FROM price_observation
          WHERE product_pack_id = ?
          GROUP BY store_id
        ) last
          ON last.store_id = po.store_id
         AND last.max_date = po.observed_on
        WHERE po.product_pack_id = ?
        ORDER BY s.name ASC
        """,
        (pack_id, pack_id),
    ).fetchall()


def price_history(
    conn: sqlite3.Connection,
    pack_id: int,
    store_id: Optional[int] = None,
) -> list[sqlite3.Row]:
    query = """
        SELECT
          s.name AS store,
          po.observed_on,
          po.price_cents
        FROM price_observation po
        JOIN store s ON s.id = po.store_id
        WHERE po.product_pack_id = ?
    """
    params = [pack_id]

    if store_id is not None:
        query += " AND po.store_id = ?"
        params.append(store_id)

    query += " ORDER BY po.observed_on ASC, s.name ASC"
    return conn.execute(query, params).fetchall()


def price_history_for_store(
    conn: sqlite3.Connection,
    pack_id: int,
    store_id: int,
) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT observed_on, price_cents
        FROM price_observation
        WHERE product_pack_id = ?
          AND store_id = ?
        ORDER BY observed_on ASC
        """,
        (pack_id, store_id),
    ).fetchall()
