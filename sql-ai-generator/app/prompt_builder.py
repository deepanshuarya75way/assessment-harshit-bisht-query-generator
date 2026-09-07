from app.schema_introspect import get_schema_text

# Few-shot examples specific to this schema. Add more real examples here
# over time -- this is the single biggest lever for accuracy. Base these
# on questions your users actually ask and queries you've verified by hand.
FEW_SHOT_EXAMPLES = """
Q: How many customers do we have?
SQL: SELECT COUNT(*) FROM customers;

Q: What are the top 3 most expensive products?
SQL: SELECT name, price FROM products ORDER BY price DESC LIMIT 3;

Q: Show total revenue per customer
SQL: SELECT c.name, SUM(p.price * oi.quantity) AS total_spent
FROM customers c
JOIN orders o ON o.customer_id = c.id
JOIN order_items oi ON oi.order_id = o.id
JOIN products p ON p.id = oi.product_id
WHERE o.status = 'completed'
GROUP BY c.id
ORDER BY total_spent DESC;
""".strip()

SYSTEM_PROMPT_TEMPLATE = """You are a SQL generator for a SQLite database. Given a question in plain English, output ONE valid SQLite SELECT statement that answers it.

Rules:
- Output ONLY the SQL query. No explanation, no markdown code fences, no commentary.
- Only use SELECT statements. Never write INSERT, UPDATE, DELETE, DROP, ALTER, or any statement that modifies data.
- Only reference tables and columns that appear in the schema below. Never invent column or table names.
- Always use explicit table.column references when joining multiple tables.
- If the question cannot be answered with the given schema, output exactly: -- CANNOT_ANSWER
- Prefer clear, readable SQL over clever one-liners.

Database schema:
{schema}

Example questions and correct queries for this schema:
{examples}
"""


def build_system_prompt() -> str:
    return SYSTEM_PROMPT_TEMPLATE.format(
        schema=get_schema_text(),
        examples=FEW_SHOT_EXAMPLES,
    )


# Labels/instructions for non-relational targets. These are NOT executed --
# only shown to the user as a reference translation of the same question.
NOSQL_INSTRUCTIONS = {
    "mongodb": (
        "MongoDB. Treat each SQL table as a collection with the same field names. "
        "Express the answer as a MongoDB query using db.<collection>.find({...}) for simple "
        "lookups, or db.<collection>.aggregate([...]) with $lookup for anything that would "
        "require a SQL JOIN. Output only the query, formatted as JavaScript-style MongoDB shell syntax."
    ),
    "redis": (
        "Redis. Redis is a key-value store with no native relational query support, so most "
        "multi-table questions cannot be directly translated. If the question is a simple lookup "
        "by a single key, show the Redis command(s) that would answer it (e.g. HGETALL, GET). "
        "If it requires joining or aggregating across tables, do NOT invent a fake Redis command -- "
        "instead output a short 1-3 line explanation of the data modeling (e.g. a precomputed sorted "
        "set updated on writes) that would be needed to answer this in Redis."
    ),
}

NOSQL_PROMPT_TEMPLATE = """You are translating a natural-language question about a relational database into an equivalent reference query for a different, non-relational database: {target_label}

This translation will NOT be executed -- it is shown to the user purely as a reference/learning aid, so accuracy of intent matters more than runnable syntax.

The underlying data (currently stored relationally) has this schema:
{schema}

Rules:
- Output ONLY the translated query or explanation. No markdown code fences, no extra commentary beyond what's asked for above.
- Do not use SQL syntax in your answer.
"""


def build_nosql_prompt(target: str) -> str:
    if target not in NOSQL_INSTRUCTIONS:
        raise ValueError(f"No NoSQL instructions defined for target: {target}")
    return NOSQL_PROMPT_TEMPLATE.format(
        target_label=NOSQL_INSTRUCTIONS[target],
        schema=get_schema_text(),
    )
