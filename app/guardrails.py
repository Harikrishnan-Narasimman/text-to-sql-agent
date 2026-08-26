import re

BLOCKED_KEYWORDS = [
    "DROP", "DELETE", "UPDATE", "INSERT", "ALTER",
    "TRUNCATE", "CREATE", "REPLACE", "ATTACH", "PRAGMA",
]

class UnsafeQueryError(Exception):
    pass

def check_query_safety(sql: str) -> None:
    normalized_sql = sql.upper()
    for keyword in BLOCKED_KEYWORDS:
        if re.search(rf"\b{keyword}\b", normalized_sql):
            raise UnsafeQueryError(f"Unsafe SQL query detected: {keyword} is not allowed.")

    if not normalized_sql.strip().startswith("SELECT"):
        raise UnsafeQueryError("Only SELECT queries are allowed.")