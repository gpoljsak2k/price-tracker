import sqlite3
from typing import Optional


def add_product(conn: sqlite3.Connection, name: str, brand: Optional[str]) -> int:
    name = name.strip()
    brand_norm = (brand.strip() if brand else "")
    if not name:
        raise ValueError("Ime izdelka ne sme biti prazno.")

    cur = conn.execute(
        "INSERT INTO product(name, brand) VALUES (?, ?)",
        (name, brand_norm),
    )
    conn.commit()
    return int(cur.lastrowid)


def list_products(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT id, name, brand
        FROM product
        ORDER BY name ASC, IFNULL(brand,'') ASC
        """
    ).fetchall()


def list_products_with_pack_status(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT
          p.id,
          p.name,
          p.brand,
          CASE WHEN COUNT(pp.id) > 0 THEN 1 ELSE 0 END AS packed
        FROM product p
        LEFT JOIN product_pack pp ON pp.product_id = p.id
        GROUP BY p.id, p.name, p.brand
        ORDER BY p.name ASC, IFNULL(p.brand,'') ASC
        """
    ).fetchall()


def find_product_id(conn: sqlite3.Connection, name: str, brand: Optional[str]) -> Optional[int]:
    name = name.strip()
    brand_norm = (brand.strip() if brand else "")
    row = conn.execute(
        "SELECT id FROM product WHERE name = ? AND brand = ?",
        (name, brand_norm),
    ).fetchone()
    return int(row["id"]) if row else None


def delete_product(conn: sqlite3.Connection, product_id: int) -> None:
    conn.execute("DELETE FROM product WHERE id = ?", (product_id,))
    conn.commit()
