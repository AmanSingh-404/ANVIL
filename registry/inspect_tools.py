import sys
from registry.registry import list_tools, get_tool_by_name
from registry.db import get_connection


def print_all_tools():
    tools = list_tools()
    if not tools:
        print("No tools in registry.")
        return
    print(f"{'Name':<25} {'Version':<8} {'Source':<10} {'Success':<8} {'Fail':<6}")
    print("-" * 65)
    for t in tools:
        print(f"{t['name']:<25} {t['version']:<8} {t['source']:<10} {t['success_count']:<8} {t['failure_count']:<6}")


def print_tool_code(name: str):
    tool = get_tool_by_name(name)
    if not tool:
        print(f"No approved tool found named '{name}'")
        return
    print(f"--- {name} (v{tool['version']}) ---")
    print(tool["code"])

def print_version_history(name: str):
    conn = get_connection()
    rows = conn.execute(
        "SELECT version, status, success_count, failure_count, created_at FROM tools WHERE name = ? ORDER BY version",
        (name,)
    ).fetchall()
    conn.close()

    if not rows:
        print(f"No tool found named '{name}'")
        return

    print(f"--- Version history for '{name}' ---")
    for r in rows:
        total = r["success_count"] + r["failure_count"]
        rate = f"{r['failure_count']}/{total} failed" if total > 0 else "no calls yet"
        print(f"  v{r['version']} [{r['status']}] - {rate} - created {r['created_at']}")

if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--history":
        print_version_history(sys.argv[2])
    elif len(sys.argv) > 1:
        print_tool_code(sys.argv[1])
    else:
        print_all_tools()

