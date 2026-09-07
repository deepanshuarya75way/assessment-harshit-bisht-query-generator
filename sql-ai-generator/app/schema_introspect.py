"""
Pulls table/column/foreign-key info out of the SQLite database and formats
it as compact text the LLM can use as context. Cached in memory after the
first call -- call refresh_schema_cache() if your schema changes at runtime.
"""
import sqlite3
from app.config import DATABASE_PATH

_schema_cache = {"text": None, "tables": None}


def _get_connection():
    return sqlite3.connect(DATABASE_PATH)


def _introspect() -> tuple[str, dict[str, set[str]]]:
    conn = _get_connection()
    cur = conn.cursor()

    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    table_names = [row[0] for row in cur.fetchall()]

    lines = []
    tables: dict[str, set[str]] = {}

    for table in table_names:
        cur.execute(f"PRAGMA table_info({table})")
        columns = cur.fetchall()  # cid, name, type, notnull, dflt_value, pk
        col_descs = [f"{c[1]} {c[2]}{' PK' if c[5] else ''}" for c in columns]
        tables[table] = {c[1] for c in columns}

        cur.execute(f"PRAGMA foreign_key_list({table})")
        fks = cur.fetchall()
        fk_descs = [f"{fk[3]} -> {fk[2]}.{fk[4]}" for fk in fks]

        cur.execute(f"SELECT * FROM {table} LIMIT 2")
        sample_rows = cur.fetchall()

        block = [f"TABLE {table} ({', '.join(col_descs)})"]
        if fk_descs:
            block.append(f"  Foreign keys: {', '.join(fk_descs)}")
        if sample_rows:
            block.append(f"  Sample rows: {sample_rows}")
        lines.append("\n".join(block))

    conn.close()
    return "\n\n".join(lines), tables


def get_schema_text() -> str:
    if _schema_cache["text"] is None:
        text, tables = _introspect()
        _schema_cache["text"] = text
        _schema_cache["tables"] = tables
    return _schema_cache["text"]


def get_known_tables() -> dict[str, set[str]]:
    """Returns {table_name: {column_names}} -- used by the validator to
    reject SQL that references tables/columns that don't exist."""
    if _schema_cache["tables"] is None:
        get_schema_text()
    return _schema_cache["tables"]


def refresh_schema_cache():
    _schema_cache["text"] = None
    _schema_cache["tables"] = None
    get_schema_text()
