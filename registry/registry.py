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

def increment_approval_count(name: str) -> int:
    conn = get_connection()
    conn.execute("UPDATE tools SET approval_count = approval_count + 1 WHERE name = ?", (name,))
    conn.commit()
    row = conn.execute("SELECT approval_count FROM tools WHERE name = ?", (name,)).fetchone()
    conn.close()
    return row["approval_count"] if row else 0


def mark_auto_approved(name: str):
    conn = get_connection()
    conn.execute("UPDATE tools SET auto_approved = 1 WHERE name = ?", (name,))
    conn.commit()
    conn.close()

FAILURE_RATE_THRESHOLD = 0.5  # if 50%+ of calls fail
MIN_CALLS_BEFORE_CHECK = 3    # don't judge a tool on 1-2 calls, too noisy


def needs_reforge(name: str) -> bool:
    conn = get_connection()
    row = conn.execute(
        "SELECT success_count, failure_count FROM tools WHERE name = ? AND status = 'approved'",
        (name,)
    ).fetchone()
    conn.close()

    if not row:
        return False

    total = row["success_count"] + row["failure_count"]
    if total < MIN_CALLS_BEFORE_CHECK:
        return False

    failure_rate = row["failure_count"] / total
    return failure_rate >= FAILURE_RATE_THRESHOLD

def add_new_version(name: str, description: str, input_schema: dict, code: str,
                     class_name: str, risk_tier: str, source: str = "forged") -> int:
    """
    Deprecates the current approved version of `name` and inserts a new one
    with an incremented version number. Old versions are kept (status='deprecated'),
    never deleted — so history is preserved for the report/demo.
    """
    conn = get_connection()
    cursor = conn.cursor()

    old = cursor.execute(
        "SELECT version FROM tools WHERE name = ? AND status = 'approved'", (name,)
    ).fetchone()
    new_version = (old["version"] + 1) if old else 1

    cursor.execute("UPDATE tools SET status = 'deprecated' WHERE name = ? AND status = 'approved'", (name,))

    cursor.execute("""
        INSERT INTO tools (name, description, input_schema, code, class_name, source, risk_tier, version)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (name, description, json.dumps(input_schema), code, class_name, source, risk_tier, new_version))

    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id