import json
import os
from datetime import datetime

LOG_PATH = os.path.join("memory", "forge_log.jsonl")


def log_forge_attempt(task_description: str, reason: str, result: dict):
    entry = {
        "timestamp": datetime.now().isoformat(),
        "task": task_description,
        "reason": reason,
        "success": result.get("success", False),
        "class_name": result.get("class_name"),
        "attempts": result.get("attempts"),
        "error": result.get("error"),
    }
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")