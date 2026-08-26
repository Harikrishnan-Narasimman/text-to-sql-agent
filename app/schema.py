import sqlite3
from typing import List, Tuple, Dict

def get_schema_metadata(db_path: str) -> Dict[str, List[dict]]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row["name"] for row in cursor.fetchall()]

    schema = {}
    for table in tables:
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [
            {"name": row["name"], "type": row["type"]} for row in cursor.fetchall()
        ]

        cursor.execute(f"SELECT * FROM {table} LIMIT 2")

        sample_rows = [dict(row) for row in cursor.fetchall()]

        schema[table] = {"columns": columns, "sample_rows": sample_rows}

    conn.close()
    return schema

def format_schema_for_prompt(schema: Dict[str, dict]) -> str:
    lines = []
    for table, info in schema.items():
        col_str = ", ".join(f"{c['name']} ({c['type']})" for c in info["columns"])
        lines.append(f"Table '{table}': {col_str}")
        if info["sample_rows"]:
            lines.append(f"  Sample row: {info['sample_rows'][0]}")
    return "\n".join(lines)