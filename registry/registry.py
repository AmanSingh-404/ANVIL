import json
from registry.db import get_connection


def add_tool(name: str, description: str, input_schema: dict, code: str,
             class_name: str, source: str = "forged", risk_tier: str = "side_effecting") -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO tools (name, description, input_schema, code, class_name, source, risk_tier)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (name, description, json.dumps(input_schema), code, class_name, source, risk_tier))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id


def get_tool_by_name(name: str) -> dict:
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM tools WHERE name = ? AND status = 'approved' ORDER BY version DESC LIMIT 1",
        (name,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def list_tools(status: str = "approved") -> list:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM tools WHERE status = ? ORDER BY name, version DESC",
        (status,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def deprecate_tool(name: str):
    conn = get_connection()
    conn.execute("UPDATE tools SET status = 'deprecated' WHERE name = ?", (name,))
    conn.commit()
    conn.close()


def record_tool_outcome(name: str, succeeded: bool):
    conn = get_connection()
    if succeeded:
        conn.execute("UPDATE tools SET success_count = success_count + 1 WHERE name = ?", (name,))
    else:
        conn.execute("UPDATE tools SET failure_count = failure_count + 1 WHERE name = ?", (name,))
    conn.commit()
    conn.close()