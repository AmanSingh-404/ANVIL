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


# ---------- Web approval (per-session, multi-user safe) ----------

_pending_by_session = {}  # session_id -> {"active", "tool_name", "arguments", "description", "event", "decision"}


def request_approval_web(session_id: str):
    """
    Returns an approval_fn bound to this session_id, so core.agent's
    generic approval_fn(tool_name, arguments, description) signature
    stays unchanged while each session gets its own isolated pending slot.
    """
    def _approve(tool_name: str, arguments: dict, description: str) -> bool:
        event = threading.Event()
        _pending_by_session[session_id] = {
            "active": True, "tool_name": tool_name, "arguments": arguments,
            "description": description, "event": event, "decision": None,
        }
        event.wait()
        decision = _pending_by_session[session_id]["decision"]
        _pending_by_session[session_id]["active"] = False
        return decision
    return _approve


def get_pending_approval(session_id: str):
    entry = _pending_by_session.get(session_id)
    if not entry or not entry["active"]:
        return None
    return {
        "tool_name": entry["tool_name"],
        "arguments": entry["arguments"],
        "description": entry["description"],
    }


def resolve_pending_approval(session_id: str, decision: bool) -> bool:
    entry = _pending_by_session.get(session_id)
    if not entry or not entry["active"] or entry["event"] is None:
        return False
    entry["decision"] = decision
    entry["event"].set()
    return True