import threading

GRADUATION_THRESHOLD = 3

# ---------- CLI approval (unchanged behavior, used by core.agent when run via terminal) ----------

def request_approval_cli(tool_name: str, arguments: dict, description: str) -> bool:
    print(f"\n  ⚠ APPROVAL REQUIRED")
    print(f"  Tool: {tool_name}")
    print(f"  Description: {description}")
    print(f"  Arguments: {arguments}")

    while True:
        response = input("  Approve this action? (y/n): ").strip().lower()
        if response in ("y", "yes"):
            return True
        elif response in ("n", "no"):
            return False
        else:
            print("  Please type 'y' or 'n'.")


def offer_graduation(tool_name: str, approval_count: int) -> bool:
    if approval_count < GRADUATION_THRESHOLD:
        return False
    print(f"\n  You've approved '{tool_name}' {approval_count} times.")
    response = input(f"  Auto-approve this tool from now on? (y/n): ").strip().lower()
    return response in ("y", "yes")


# ---------- Web approval (used by api_server.py, no terminal available) ----------
# Single global pending slot — matches the existing "one session per server run" simplification.

_pending = {
    "active": False, "tool_name": None, "arguments": None,
    "description": None, "event": None, "decision": None,
}


def request_approval_web(tool_name: str, arguments: dict, description: str) -> bool:
    """
    Registers a pending approval the dashboard can see via polling, then
    blocks THIS REQUEST THREAD ONLY on a threading.Event until /api/approve
    resolves it. Requires Flask running with threaded=True so other routes
    (the poll and the approve endpoint) can still be served concurrently.
    """
    event = threading.Event()
    _pending.update({
        "active": True, "tool_name": tool_name, "arguments": arguments,
        "description": description, "event": event, "decision": None,
    })
    event.wait()
    decision = _pending["decision"]
    _pending["active"] = False
    return decision


def get_pending_approval():
    if not _pending["active"]:
        return None
    return {
        "tool_name": _pending["tool_name"],
        "arguments": _pending["arguments"],
        "description": _pending["description"],
    }


def resolve_pending_approval(decision: bool) -> bool:
    if not _pending["active"] or _pending["event"] is None:
        return False
    _pending["decision"] = decision
    _pending["event"].set()
    return True