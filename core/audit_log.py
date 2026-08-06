import json
import os
from datetime import datetime

AUDIT_LOG_PATH = os.path.join("memory", "audit_log.jsonl")


def log_approval_event(tool_name: str, arguments: dict, decision: str):
    """
    decision should be one of: "approved", "denied", "auto_approved"
    """
    entry = {
        "timestamp": datetime.now().isoformat(),
        "tool_name": tool_name,
        "arguments": arguments,
        "decision": decision,
    }
    os.makedirs(os.path.dirname(AUDIT_LOG_PATH), exist_ok=True)
    with open(AUDIT_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")