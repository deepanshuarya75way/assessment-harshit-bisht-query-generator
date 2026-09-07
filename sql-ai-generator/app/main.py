from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.llm_client import generate_sql, generate_nosql_reference
from app.sql_validator import validate_sql, ValidationError
from app.query_executor import execute_query
from app.dialect_translator import (
    SQL_DIALECT_MAP,
    NOSQL_DIALECTS,
    ALL_DIALECTS,
    DISPLAY_NAMES,
    translate_sql,
    TranslationError,
)

app = FastAPI(title="AI SQL Query Generator")


class QuestionRequest(BaseModel):
    question: str
    dialect: str = "sqlite"


@app.get("/api/dialects")
def list_dialects():
    """Lets the frontend build its dropdown from a single source of truth."""
    return {"dialects": [{"id": d, "label": DISPLAY_NAMES[d]} for d in ALL_DIALECTS]}


@app.post("/api/query")
def run_query(req: QuestionRequest):
    question = req.question.strip()
    dialect = (req.dialect or "sqlite").strip().lower()

    if not question:
        return {"error": "Question cannot be empty."}
    if dialect not in ALL_DIALECTS:
        return {"error": f"Unknown database type: {dialect!r}"}

    # Step 1: LLM generates the REAL, executable SQL (always SQLite -- this
    # is the only database that actually exists in this project, so it's
    # the only thing we can honestly execute and trust the results of).
    try:
        raw_sql = generate_sql(question)
    except Exception as e:
        return {"error": f"Failed to generate SQL: {e}"}

    # Step 2: validate before anything touches the real database
    try:
        safe_sql = validate_sql(raw_sql)
    except ValidationError as e:
        return {"error": str(e), "generated_sql": raw_sql}

    # Step 3: execute against a read-only connection with limits
    try:
        result = execute_query(safe_sql)
    except Exception as e:
        return {"error": f"Query execution failed: {e}", "generated_sql": safe_sql}

    # Step 4: build the query to DISPLAY in the user's requested dialect.
    # Results always come from the SQLite execution above -- only the
    # displayed query text changes.
    note = None
    if dialect == "sqlite":
        display_query = safe_sql
        executable = True
    elif dialect in SQL_DIALECT_MAP:
        try:
            display_query = translate_sql(safe_sql, dialect)
        except TranslationError as e:
            display_query = safe_sql
            note = f"Could not translate to {DISPLAY_NAMES[dialect]} ({e}); showing the original SQLite query instead."
        else:
            note = (
                f"Shown in {DISPLAY_NAMES[dialect]} syntax for reference. "
                f"Results were computed using the underlying SQLite database."
            )
        executable = False
    else:  # NoSQL: mongodb, redis
        try:
            display_query = generate_nosql_reference(question, dialect)
        except Exception as e:
            display_query = f"-- Could not generate a {DISPLAY_NAMES[dialect]} reference: {e}"
        note = (
            f"{DISPLAY_NAMES[dialect]} reference shown for learning purposes only -- "
            f"it is not executed. Results were computed using the underlying SQLite database."
        )
        executable = False

    return {
        "generated_sql": display_query,
        "dialect": dialect,
        "dialect_label": DISPLAY_NAMES[dialect],
        "executable": executable,
        "note": note,
        "columns": result["columns"],
        "rows": result["rows"],
        "truncated": result["truncated"],
    }


@app.get("/")
def serve_index():
    return FileResponse("static/index.html")


app.mount("/static", StaticFiles(directory="static"), name="static")
