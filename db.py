import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = Path("prices.db")

def connect(db_path: str = "prices.db") -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db(conn: sqlite3.Connection, schema_path: str | Path = "schema.sql") -> None:
    schema = Path(schema_path).read_text(encoding="utf-8")
    conn.executescript(schema)
    conn.commit()
