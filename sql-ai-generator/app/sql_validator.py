"""
Defense-in-depth check on whatever SQL the LLM returns. This is the real
safety boundary -- never trust the prompt instructions alone.
"""
import sqlglot
from sqlglot import exp
from app.schema_introspect import get_known_tables


class ValidationError(Exception):
    pass


ALLOWED_STATEMENT_TYPES = (exp.Select,)


def validate_sql(sql: str) -> str:
    """Returns the validated SQL (possibly with a row limit appended), or
    raises ValidationError with a human-readable reason."""
    sql = sql.strip().rstrip(";")

    if sql.startswith("--") or not sql:
        raise ValidationError("The model could not answer this question with the current schema.")

    try:
        parsed_statements = sqlglot.parse(sql, read="sqlite")
    except Exception as e:
        raise ValidationError(f"Generated SQL failed to parse: {e}")

    if len(parsed_statements) != 1:
        raise ValidationError("Only a single SQL statement is allowed.")

    tree = parsed_statements[0]
    if tree is None or not isinstance(tree, ALLOWED_STATEMENT_TYPES):
        raise ValidationError("Only SELECT statements are allowed.")

    # Reject any modification keywords that might sneak in via a subquery/CTE trick
    forbidden = (exp.Insert, exp.Update, exp.Delete, exp.Drop, exp.Alter, exp.Create)
    for node in tree.walk():
        node_obj = node[0] if isinstance(node, tuple) else node
        if isinstance(node_obj, forbidden):
            raise ValidationError("Query contains a disallowed write operation.")

    # Check every referenced table exists in the real schema
    known_tables = get_known_tables()
    referenced_tables = {t.name.lower() for t in tree.find_all(exp.Table)}
    unknown = referenced_tables - {t.lower() for t in known_tables}
    if unknown:
        raise ValidationError(f"Query references unknown table(s): {', '.join(unknown)}")

    return tree.sql(dialect="sqlite")
