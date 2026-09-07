import sqlite3
from app.config import DATABASE_PATH, MAX_ROWS_RETURNED, QUERY_TIMEOUT_SECONDS


def execute_query(sql: str) -> dict:
    """Runs an already-validated SELECT query against a connection opened
    read-only, with a timeout and a hard row cap. Returns columns + rows."""
    # SQLite's URI mode with mode=ro opens the file for reading only --
    # even if the SQL somehow slipped past validation, the OS-level file
    # handle cannot write.
    uri = f"file:{DATABASE_PATH}?mode=ro"
    conn = sqlite3.connect(uri, uri=True, timeout=QUERY_TIMEOUT_SECONDS)
    conn.execute(f"PRAGMA query_only = 1")

    try:
        cur = conn.cursor()
        cur.execute(sql)
        columns = [d[0] for d in cur.description] if cur.description else []
        rows = cur.fetchmany(MAX_ROWS_RETURNED)
        truncated = cur.fetchone() is not None
        return {
            "columns": columns,
            "rows": [list(r) for r in rows],
            "truncated": truncated,
        }
    finally:
        conn.close()
