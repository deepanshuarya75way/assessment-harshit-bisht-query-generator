# AI SQL query generator

Turns plain-English questions into SQL, validates it, runs it read-only, and shows the results.

## How it works

1. **Frontend** (`static/index.html`) sends your question to the backend.
2. **Backend** (`app/main.py`) orchestrates the request.
3. **Schema introspection** (`app/schema_introspect.py`) reads the database's tables/columns/foreign keys once and caches them as text.
4. **Prompt builder** (`app/prompt_builder.py`) combines the schema, safety rules, and a few example question/SQL pairs into the system prompt.
5. **LLM client** (`app/llm_client.py`) sends your question + that prompt to either a local Ollama model or Claude, and gets SQL back.
6. **Validator** (`app/sql_validator.py`) parses the SQL, rejects anything that isn't a single `SELECT`, and rejects unknown tables/columns.
7. **Executor** (`app/query_executor.py`) runs the validated query against a read-only connection with a row limit and timeout.
8. **Dialect translator** (`app/dialect_translator.py`) rewrites the already-executed SQL into whichever database syntax you picked in the dropdown, purely for display.
9. Results (and the query itself, so you can check it) go back to the frontend.

## Choosing a database type

The dropdown next to the question box lets you see the equivalent query in **SQLite, MySQL, PostgreSQL, Microsoft SQL Server, Oracle, MongoDB, or Redis**.

Important honesty note about how this actually works: this project only has one real database (the SQLite `sample.db`). Execution *always* happens against that SQLite database, no matter what you pick in the dropdown -- that's the only way the results shown are guaranteed accurate. What changes based on your selection is only the *displayed* query text:

- **SQLite, MySQL, PostgreSQL, SQL Server, Oracle**: the already-validated SQL is mechanically translated into that dialect's syntax using `sqlglot` (e.g. `LIMIT 5` becomes `TOP 5` for SQL Server, `FETCH FIRST 5 ROWS ONLY` for Oracle). This translation is reliable and copy-paste usable against a real database of that type.
- **MongoDB, Redis**: these aren't relational databases and have no SQL syntax, so there's no mechanical translation possible. Instead, the LLM generates a best-effort reference query or explanation of the equivalent approach (e.g. a MongoDB aggregation pipeline, or a note on how you'd model this in Redis). This is clearly labeled as **reference only, not executed** -- treat it as a learning aid, not a runnable query.

If you want this to genuinely execute against a real MySQL/Postgres/etc. database instead of just displaying translated syntax, see "Using your own database" below -- you'd swap the actual connection in `query_executor.py` and `schema_introspect.py`.

## Setup (free, runs entirely on your machine)

By default this uses **Ollama** -- a free local LLM runner. No API key, no cost, no internet needed once set up.

```bash
# 1. Install Ollama: https://ollama.com (one-line installer for Mac/Linux/Windows)
ollama pull qwen2.5-coder     # downloads a model good at code/SQL, ~4-5GB
ollama serve                  # starts the local model server (leave running)

# 2. In a separate terminal, set up the app
cd sql-ai-generator
python -m venv venv
source venv/bin/activate      # on Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env          # defaults to LLM_PROVIDER=ollama -- no editing needed

python seed_db.py             # creates sample.db with demo data
uvicorn app.main:app --reload
```

Then open **http://localhost:8000** and try questions like:
- "How many customers do we have?"
- "Which customers spent the most money?"
- "What products are in the Electronics category?"
- "Show me all cancelled orders"

Local open-source models are noticeably less reliable at complex multi-table SQL than Claude -- expect to lean more on the few-shot examples in `app/prompt_builder.py`, and possibly add a retry-on-validation-failure loop (see Extending this below), to get good results consistently.

## Optional: switch to Claude for better accuracy

Claude is meaningfully better at generating correct SQL, especially for multi-table joins and edge cases. It's a paid API with no permanent free tier, but new accounts get a small one-time free credit that's enough to build and test this project without spending anything.

1. Go to https://console.anthropic.com and sign up (no credit card needed for the free trial credit; phone verification required)
2. Go to **Settings -> API Keys** and create a new key
3. In `.env`, set:
   ```
   LLM_PROVIDER=anthropic
   ANTHROPIC_API_KEY=sk-ant-your-key-here
   ```
4. `pip install -r requirements-anthropic.txt` (adds the Anthropic SDK)

Once the free credit runs out, further use is billed pay-as-you-go -- check current pricing at https://docs.claude.com before relying on it for anything beyond testing.

## Using your own database instead of the sample

Point `DATABASE_PATH` in `.env` at your own SQLite file, or:
- Rewrite `app/schema_introspect.py` and `app/query_executor.py` to use a Postgres/MySQL driver (e.g. `psycopg2`, `pymysql`) instead of `sqlite3` -- the rest of the app doesn't need to change.
- Make sure the database user/connection you use is **read-only** at the database level, not just in your application code.

## Extending this

- **Retry on validation failure**: if `sql_validator.py` rejects a query, you can send the error back to the model and ask it to fix the query (one retry usually resolves most issues, especially useful for weaker local models).
- **Logging and feedback**: log every `question -> generated_sql -> success/failure` to a table, and turn corrected failures into new few-shot examples in `prompt_builder.py`.
- **Follow-up questions**: pass conversation history in `llm_client.py` instead of a single message, so users can say "now filter that to last month."
