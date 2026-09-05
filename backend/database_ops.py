"""Read-only SQL access to the local Retail Copilot database."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "database" / "retail.db"

READ_ONLY_PREFIXES = {"select", "with", "explain", "pragma"}


def _connect() -> sqlite3.Connection:
    """Open the SQLite database in a read-only, fail-fast mode."""
    if not DB_PATH.exists():
        raise ValueError(
            f"Database not found at {DB_PATH}. Run database/generate_data.py first."
        )
    conn = sqlite3.connect(f"{DB_PATH.as_uri()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def execute_query(sql_query: str) -> list[dict]:
    """Run a read-only SQL query and return the rows as a list of dicts."""
    if not isinstance(sql_query, str) or not sql_query.strip():
        raise ValueError("execute_query() requires a non-empty SQL string.")

    prefix = sql_query.lstrip().split(None, 1)[0].lower()
    if prefix not in READ_ONLY_PREFIXES:
        raise ValueError(f"Only read-only SQL is allowed (got keyword '{prefix}').")

    conn = _connect()
    try:
        cursor = conn.execute(sql_query)
        columns = [description[0] for description in cursor.description or ()]
        rows = cursor.fetchall()
    except sqlite3.Error as exc:
        raise ValueError(f"SQL query failed: {exc}") from exc
    finally:
        conn.close()

    return [dict(zip(columns, row)) for row in rows]


def get_db_schema() -> str:
    """Return the exact schema of Products, Inventory and Sales as a string."""
    lines = []
    for table in ("Products", "Inventory", "Sales"):
        columns = execute_query(f"PRAGMA table_info({table});")
        lines.append(f"Table: {table}")
        for column in columns:
            constraints = ""
            if column["notnull"]:
                constraints += " NOT NULL"
            if column["dflt_value"] is not None:
                constraints += f" DEFAULT {column['dflt_value']}"
            if column["pk"]:
                constraints += " PRIMARY KEY"
            lines.append(
                f"  {column['name']}  {column['type']}{constraints}"
            )
    return "\n".join(lines)