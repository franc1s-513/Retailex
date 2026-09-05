"""Gemini Text-to-SQL agent via the google-generativeai SDK."""

import json
import os
import re
from pathlib import Path

import google.generativeai as genai

try:
    from .database_ops import execute_query, get_db_schema
except ImportError:
    from database_ops import execute_query, get_db_schema


def _load_env() -> None:
    """Load GEMINI_API_KEY (and any other keys) from the project .env file into os.environ.

    Only sets variables that are not already present, so an explicitly exported
    environment variable always takes precedence.
    """
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if not env_path.exists():
        return
    try:
        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value
    except OSError:
        pass


_load_env()

PREFERRED_MODELS = [
    "gemini-flash-latest",
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.5-flash",
    "gemini-3.6-flash",
]
NO_DATA_MESSAGE = "I do not have enough data to answer that."
_SQL_FENCE_RE = re.compile(r"```(?:sql)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)

SQL_SYSTEM_PROMPT = """\
You are Retail Copilot, a retail analyst. Translate the user's natural-language \
question into ONE valid SQLite SQL query.

Database schema:
{schema}

Rules:
- Output ONLY the SQL query text. No explanations, no markdown code fences.
- Use only read-only statements (SELECT / WITH). Never write or mutate data.
- Sale dates are stored as TEXT in the format 'YYYY-MM-DD' in the Sales.date column.
- Join Products and Inventory on product_id, and Inventory/Sales on store_id where needed.
- Aggregate with SUM/COUNT/AVG and GROUP BY as appropriate.
"""

FORMAT_SYSTEM_PROMPT = """\
You are Retail Copilot, a helpful retail analyst who translates SQL query results \
into a clear plain-language answer.

Rules:
- Never make a claim without providing the exact underlying figures.
- State the data and assumptions behind any recommendation.
- Base your answer ONLY on the database rows provided in the message. Do not invent numbers.
- If the rows do not fully answer the question, say what is missing.
- Answer concisely and conversationally.
"""


class RetailCopilotAgent:
    """Answers natural-language questions about retail data via Gemini Text-to-SQL."""

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY is not set. Provide it via os.getenv or the "
                "constructor (see .env)."
            )
        genai.configure(api_key=self.api_key)

    def ask(self, question: str) -> dict:
        """Turn a natural-language question into a plain-language answer with SQL citation."""
        if not question or not question.strip():
            return {"response": NO_DATA_MESSAGE, "sql": None, "row_count": 0}

        try:
            sql = self._generate_sql(question)
        except Exception:
            return {
                "response": "I am temporarily unable to reach the AI model to construct a database query. Please try rephrasing or asking again in a few seconds.",
                "sql": None,
                "row_count": 0,
            }

        try:
            data = execute_query(sql)
        except Exception as exc:
            return {
                "response": f"I couldn't run the generated database query ({exc}). Please try rephrasing.",
                "sql": sql,
                "row_count": 0,
            }

        if not data:
            return {"response": NO_DATA_MESSAGE, "sql": sql, "row_count": 0}

        try:
            answer = self._format_answer(question, data)
        except Exception:
            # Deterministic graceful fallback if synthesis call fails
            sample = [dict(r) for r in data[:3]]
            answer = (
                f"Retrieved {len(data)} matching record(s) from the database:\n\n"
                f"```json\n{json.dumps(sample, indent=2)}\n```"
            )

        return {
            "response": answer,
            "sql": sql,
            "row_count": len(data),
        }

    def _generate(self, system_prompt: str, content: str) -> str:
        last_error = None
        for model_name in PREFERRED_MODELS:
            try:
                model = genai.GenerativeModel(model_name, system_instruction=system_prompt)
                response = model.generate_content(content)
                if response and response.text:
                    return response.text
            except Exception as exc:
                last_error = exc
                continue
        raise RuntimeError(f"All Gemini models exhausted or failed: {last_error}")

    def _generate_sql(self, question: str) -> str:
        system_prompt = SQL_SYSTEM_PROMPT.format(schema=get_db_schema())
        text = self._generate(system_prompt, question)
        match = _SQL_FENCE_RE.search(text)
        if match:
            text = match.group(1)
        return text.strip().rstrip(";").strip()

    def _format_answer(self, question: str, data: list[dict]) -> str:
        payload = (
            f"User question: {question}\n\n"
            f"Database rows (JSON):\n{json.dumps(data)}"
        )
        return self._generate(FORMAT_SYSTEM_PROMPT, payload)