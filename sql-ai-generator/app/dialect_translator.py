"""
Translates the SQL that was generated (and actually executed, always in
SQLite) into the syntax of whichever database the user asked to see.

Important honesty note: only the SQLite database is real in this project.
Execution ALWAYS happens against SQLite -- that's the only way we can
guarantee the results are correct. For relational targets (MySQL, Postgres,
SQL Server, Oracle) we transpile the already-validated SQL text using
sqlglot, which is a reliable syntax-level translation. For non-relational
targets (MongoDB, Redis) there is no reliable mechanical translation, so we
ask the LLM to produce a best-effort equivalent for reference -- it is
clearly labeled as non-executable in the UI.
"""
import sqlglot

# Maps our UI's dialect id -> sqlglot's dialect name
SQL_DIALECT_MAP = {
    "sqlite": "sqlite",
    "mysql": "mysql",
    "postgresql": "postgres",
    "mssql": "tsql",
    "oracle": "oracle",
}

# These have no SQL syntax at all -- handled via LLM-generated reference text
NOSQL_DIALECTS = {"mongodb", "redis"}

ALL_DIALECTS = set(SQL_DIALECT_MAP) | NOSQL_DIALECTS

DISPLAY_NAMES = {
    "sqlite": "SQLite",
    "mysql": "MySQL",
    "postgresql": "PostgreSQL",
    "mssql": "Microsoft SQL Server",
    "oracle": "Oracle",
    "mongodb": "MongoDB",
    "redis": "Redis",
}


class TranslationError(Exception):
    pass


def translate_sql(sql: str, target_dialect: str) -> str:
    """Transpiles already-validated SQLite SQL into another SQL dialect's syntax."""
    if target_dialect not in SQL_DIALECT_MAP:
        raise TranslationError(f"{target_dialect} is not a SQL dialect.")
    sqlglot_name = SQL_DIALECT_MAP[target_dialect]
    try:
        translated = sqlglot.transpile(sql, read="sqlite", write=sqlglot_name, pretty=True)
        return translated[0]
    except Exception as e:
        raise TranslationError(f"Could not translate SQL to {DISPLAY_NAMES[target_dialect]}: {e}")
