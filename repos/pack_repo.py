import sqlite3
from typing import Optional


ALLOWED_UNITS = {"g", "kg", "ml", "l", "pcs"}


def add_pack(
    conn: sqlite3.Connection,
    product_id: int,
    pack_size: float,
    base_unit: str,
    note: Optional[str],
) -> int:
    base_unit = base_unit.strip()
    note_norm = (note.strip() if note else "")

    if base_unit not in ALLOWED_UNITS:
        raise ValueError(
            f"Neveljavna enota '{base_unit}'. Dovoljene: {sorted(ALLOWED_UNITS)}"
        )
    if pack_size <= 0:
        raise ValueError("pack_size mora biti > 0")

    cur = conn.execute(
        """
        INSERT INTO product_pack(product_id, pack_size, base_unit, note)
        VALUES (?,?,?,?)
        """,
        (product_id, pack_size, base_unit, note_norm),
    )
    conn.commit()
    return int(cur.lastrowid)


def find_pack_id(
    conn: sqlite3.Connection,
    product_id: int,
    pack_size: float,
    base_unit: str,
    note: Optional[str],
) -> Optional[int]:
    note_norm = (note.strip() if note else "")
    row = conn.execute(
        """
        SELECT id
        FROM product_pack
        WHERE product_id = ?
          AND pack_size = ?
          AND base_unit = ?
          AND note = ?
        """,
        (product_id, pack_size, base_unit, note_norm),
    ).fetchone()
    return int(row["id"]) if row else None


def list_packs(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT
          pp.id AS pack_id,
          p.name AS product_name,
          p.brand AS brand,
          pp.pack_size,
          pp.base_unit,
          pp.note
        FROM product_pack pp
        JOIN product p ON p.id = pp.product_id
        ORDER BY p.name ASC, IFNULL(p.brand,'') ASC, pp.pack_size ASC
        """
    ).fetchall()
