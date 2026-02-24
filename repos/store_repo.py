import sqlite3
from typing import Optional


def add_store(conn: sqlite3.Connection, name: str) -> int:
    name = name.strip()
    if not name:
        raise ValueError("Ime trgovine ne sme biti prazno.")
    cur = conn.execute("INSERT INTO store(name) VALUES (?)", (name,))
    conn.commit()
    return int(cur.lastrowid)


def list_stores(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT id, name FROM store ORDER BY name ASC"
    ).fetchall()


def find_store_id(conn: sqlite3.Connection, name: str) -> Optional[int]:
    row = conn.execute(
        "SELECT id FROM store WHERE name = ?",
        (name.strip(),),
    ).fetchone()
    return int(row["id"]) if row else None
