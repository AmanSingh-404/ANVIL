from flask import Flask, request, jsonify
from flask_cors import CORS
from core.agent import run_agent
from core.session import Session
from registry.registry import list_tools
from core.approval import request_approval_web, get_pending_approval, resolve_pending_approval
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from groq import RateLimitError
task_history = []  # every completed task's request + response + full trace, for the replay view

app = Flask(__name__)
CORS(app)  # allow requests from the Next.js dev server (localhost:3000)

import uuid

# Per-session state, keyed by a client-generated session ID (sent as X-Session-Id header).
sessions = {}         # session_id -> Session
session_histories = {}  # session_id -> task_history list


def get_or_create_session(session_id: str):
    if session_id not in sessions:
        sessions[session_id] = Session()
        session_histories[session_id] = []
    return sessions[session_id], session_histories[session_id]

CORS(app)  # allow requests from the Next.js dev server (localhost:3000)

def get_session_id():
    # Rate-limit per session, not per IP — multiple legitimate users could
    # share an IP (same office/college network), but each has their own session.
    return request.headers.get("X-Session-Id", get_remote_address())

limiter = Limiter(
    app=app,
    key_func=get_session_id,
    default_limits=["60 per hour"],  # generous overall ceiling
    storage_uri="memory://",  # fine for a single-process demo deployment
)


@app.route("/api/chat", methods=["POST"])
@limiter.limit("15 per minute")
def chat():
    data = request.get_json()
    user_message = data.get("message", "")
    session_id = request.headers.get("X-Session-Id")

    if not session_id:
        return jsonify({"error": "Missing X-Session-Id header"}), 400
    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    user_session, history = get_or_create_session(session_id)

    trace = []
    try:
        response = run_agent(user_message, user_session, approval_fn=request_approval_web(session_id), trace=trace)
    except RateLimitError:
        return jsonify({"error": "ANVIL's LLM provider is temporarily rate-limited. Please try again in a few minutes."}), 503
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

    history.append({"request": user_message, "response": response, "trace": trace})
    return jsonify({"response": response, "trace": trace})


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

@app.route("/api/tools", methods=["GET"])
def get_tools():
    tools = list_tools()
    # Strip the raw code out of the list view — keep the payload light,
    # the dashboard doesn't need full source for the summary table.
    summary = [
        {
            "name": t["name"],
            "version": t["version"],
            "source": t["source"],
            "risk_tier": t["risk_tier"],
            "success_count": t["success_count"],
            "failure_count": t["failure_count"],
            "auto_approved": bool(t["auto_approved"]),
            "created_at": t["created_at"],
        }
        for t in tools
    ]
    return jsonify({"tools": summary})

@app.route("/api/approval/pending", methods=["GET"])
def approval_pending():
    session_id = request.headers.get("X-Session-Id")
    if not session_id:
        return jsonify({"error": "Missing X-Session-Id header"}), 400
    pending = get_pending_approval(session_id)
    return jsonify({"pending": pending})


@app.route("/api/approval/resolve", methods=["POST"])
def approval_resolve():
    data = request.get_json()
    session_id = request.headers.get("X-Session-Id")
    if not session_id:
        return jsonify({"error": "Missing X-Session-Id header"}), 400
    decision = bool(data.get("approved", False))
    resolved = resolve_pending_approval(session_id, decision)
    return jsonify({"resolved": resolved})


@app.route("/api/history", methods=["GET"])
def get_history():
    session_id = request.headers.get("X-Session-Id")
    if not session_id:
        return jsonify({"error": "Missing X-Session-Id header"}), 400
    _, history = get_or_create_session(session_id)
    return jsonify({"history": history})

@app.route("/api/cost-summary", methods=["GET"])
def cost_summary():
    session_id = request.headers.get("X-Session-Id")
    if not session_id:
        return jsonify({"error": "Missing X-Session-Id header"}), 400
    _, history = get_or_create_session(session_id)

    summary = []
    grand_total = 0
    for task in history:
        task_tokens = 0
        forged_this_task = False

        for step in task.get("trace", []):
            tk = step.get("tokens", {})
            task_tokens += tk.get("prompt_tokens", 0) + tk.get("completion_tokens", 0)
            if step.get("type") == "forge_attempt":
                forged_this_task = True

        grand_total += task_tokens
        summary.append({
            "request": task["request"],
            "tokens": task_tokens,
            "forged": forged_this_task,
        })

    return jsonify({"tasks": summary, "grand_total": grand_total})

if __name__ == "__main__":
    app.run(port=5000, debug=True, threaded=True)