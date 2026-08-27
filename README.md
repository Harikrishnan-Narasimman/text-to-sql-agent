# Text-to-SQL Query Agent

An agent that converts natural-language questions into SQL, executes them
against a real database, and self-corrects if the query fails or returns
nothing useful. Built using the Anthropic API (Claude).

## How it works

1. **Schema grounding** — before writing any SQL, the agent pulls real
   table/column names and sample rows from the database so it isn't
   guessing at schema.
2. **Generate** — the LLM writes a SQL `SELECT` query for the question.
3. **Guardrail** — the query is checked against a blocklist (`DROP`,
   `DELETE`, `UPDATE`, etc.) before it's ever executed. Only `SELECT`
   statements are allowed.
4. **Execute** — the query runs against the database.
5. **Self-correct** — if the query errors out or returns zero rows, the
   error/result is fed back to the LLM, which tries again (up to 3
   attempts total).
6. **Answer** — once a valid result comes back, the agent converts the raw
   rows into a plain-English answer instead of returning a table dump.

## Setup

```bash
cd text-to-sql-agent
python -m venv venv
source venv/bin/activate  # on Windows: venv\Scripts\activate
pip install -r requirements.txt

export ANTHROPIC_API_KEY="sk-ant-..."   # or put it in a .env file

python -m app.seed_db            # creates and seeds sample.db
```

## Run the API

```bash
uvicorn app.main:app --reload
```

Then:

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Which customer has spent the most money?"}'
```

Response:

```json
{
  "question": "Which customer has spent the most money?",
  "answer": "Ava Thompson has spent the most, with a total of $121.47 across her orders.",
  "sql": "SELECT c.name, SUM(p.price * o.quantity) AS total_spent FROM customers c JOIN orders o ON c.customer_id = o.customer_id JOIN products p ON o.product_id = p.product_id GROUP BY c.customer_id ORDER BY total_spent DESC LIMIT 1",
  "attempts": 1,
  "success": true
}
```

## Run the evaluation harness

This runs 10 fixed test questions and reports first-attempt vs.
final (with retries) success rate — use these numbers in your resume
bullet instead of guessing:

```bash
python -m app.evaluate
```

## Sample database

`app/seed_db.py` creates a small SQLite database with `customers`,
`products`, and `orders` tables so the project runs standalone with no
external database setup required. Swap `DB_PATH` in `app/main.py` to
point at a real Postgres/Snowflake database if you want to extend this.

## Notes on design choices

- **SQLite for the demo** — zero setup, but the schema/guardrail/agent
  logic is database-agnostic; swapping in `psycopg2` or a Snowflake
  connector only touches `_execute_query` in `agent.py`.
- **Read-only by design** — the guardrail blocks any non-`SELECT`
  statement, so the agent can never mutate data, which matters a lot
  once you point this at anything real.
- **Retry cap of 3** — prevents runaway loops/costs if the LLM keeps
  generating broken SQL for a genuinely ambiguous question.
- **Claude (Anthropic API)** — used here instead of OpenAI. The system
  prompt is passed as a top-level `system` param rather than a message
  with `role: "system"`, and responses come back as `content[0].text`.