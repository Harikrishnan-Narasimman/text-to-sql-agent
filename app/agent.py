import sqlite3
import os
from dataclasses import dataclass, field
from typing import List, Optional

import anthropic
from dotenv import load_dotenv

from .schema import get_schema_metadata, format_schema_for_prompt
from .guardrails import check_query_safety, UnsafeQueryError

MAX_ATTEMPTS = 3
MODEL = "claude-sonnet-5"

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

@dataclass
class AgentResult:
    question: str
    final_sql: Optional[str] = None
    final_answer: Optional[str] = None
    attempts: int = 0
    valid_answer: bool = False
    attempt_log: List[dict] = field(default_factory=list)

SQL_SYSTEM_PROMPT = """You are a SQL generation assistant for a SQLite database.
This is a READ-ONLY system. Even if the question is phrased as a command
(e.g. "delete", "update", "remove"), you must only ever generate a SELECT
query that retrieves the relevant data -- never a query that modifies it.

Given the schema below and a natural-language question, write ONE SQL SELECT
query that answers the question. Only output the raw SQL, no explanation,
no markdown formatting, no semicolon at the end.

Schema:
{schema}
"""

RETRY_SYSTEM_PROMPT = """The previous SQL query you wrote failed or returned
no useful result. Fix it based on the error/result below and write a
corrected SQL SELECT query. Only output the raw SQL, no explanation, no
markdown formatting.

Schema:
{schema}

Previous SQL:
{previous_sql}

Error or issue:
{error}
"""

ANSWER_SYSTEM_PROMPT = """You answer questions using SQL query results.
Given the original question and the raw rows returned from the database,
write a short, natural-language answer based ONLY on what the data shows.

Important: the query that ran was always a read-only SELECT, regardless of
how the question was phrased. If the question asked for an action (delete,
update, insert, etc.), do not claim that action was performed. Instead,
report what the SELECT query found, and note that no data was modified.

Do not mention SQL or the database explicitly -- just answer the question
directly, the way a helpful analyst would summarize a finding.
"""

def _call_llm(system_prompt: str, user_prompt: str) -> str:
    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=system_prompt,
        messages=[
            {"role": "user", "content": user_prompt},
        ],
    )
    for block in response.content:
        if block.type == "text":
            return block.text.strip()
    raise ValueError("No text block found in Claude's response.")

def _clean_sql(raw_sql: str) -> str:
    sql = raw_sql.strip()
    if sql.startswith("```"):
        sql = sql.strip("`")
        sql = sql.replace("sql\n", "", 1).replace("sql\r\n", "", 1)
    return sql.strip().rstrip(";")

def _execute_query(db_path: str, sql: str):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(sql)
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def answer_question(question: str, db_path: str) -> AgentResult:
    schema = get_schema_metadata(db_path)
    schema_text = format_schema_for_prompt(schema)

    result = AgentResult(question=question)
    sql = None
    error = None
    rows = None

    for attempt in range(1, MAX_ATTEMPTS+1):
        result.attempts = attempt

        if attempt == 1:
            sql = _call_llm(SQL_SYSTEM_PROMPT.format(schema=schema_text), question)
        else:
            sql = _call_llm(RETRY_SYSTEM_PROMPT.format(schema=schema_text, previous_sql=sql, error=error), question)

        sql = _clean_sql(sql)

        try:
            check_query_safety(sql)
            rows = _execute_query(db_path, sql)

            result.attempt_log.append(
                {"attempt": attempt, "sql": sql, "row_count": len(rows)}
            )

            if len(rows) == 0:
                error = "Query executed successfully but returned zero rows."
                continue

            result.final_sql = sql
            result.valid_answer = True
            break

        except (sqlite3.Error, UnsafeQueryError) as e:
            error = str(e)
            result.attempt_log.append(
                {"attempt": attempt, "sql": sql, "error": error}
            )
            continue

    if not result.valid_answer:
        result.final_answer = (
            "I couldn't find a reliable answer after "
            f"{MAX_ATTEMPTS} attempts. Last issue: {error}"
        )
        return result

    answer_prompt = f"Question: {question}\nRows: {rows}"
    result.final_answer = _call_llm(ANSWER_SYSTEM_PROMPT, answer_prompt)
    return result