from flask import Flask, request, jsonify
from flask_cors import CORS
from core.agent import run_agent
from core.session import Session
from registry.registry import list_tools
from core.approval import request_approval_web, get_pending_approval, resolve_pending_approval
task_history = []  # every completed task's request + response + full trace, for the replay view

app = Flask(__name__)
CORS(app)  # allow requests from the Next.js dev server (localhost:3000)

# One session per server run for now — good enough for a single-user dashboard demo.
# (Multi-session support is a legitimate "future work" item if asked in your viva.)
session = Session()


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_message = data.get("message", "")

    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    trace = []
    response = run_agent(user_message, session, approval_fn=request_approval_web, trace=trace)
    task_history.append({"request": user_message, "response": response, "trace": trace})
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
    pending = get_pending_approval()
    return jsonify({"pending": pending})


@app.route("/api/approval/resolve", methods=["POST"])
def approval_resolve():
    data = request.get_json()
    decision = bool(data.get("approved", False))
    resolved = resolve_pending_approval(decision)
    return jsonify({"resolved": resolved})

@app.route("/api/history", methods=["GET"])
def get_history():
    return jsonify({"history": task_history})

@app.route("/api/cost-summary", methods=["GET"])
def cost_summary():
    summary = []
    grand_total = 0

    for task in task_history:
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