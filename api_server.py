from flask import Flask, request, jsonify
from flask_cors import CORS
from core.agent import run_agent
from core.session import Session
from registry.registry import list_tools

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

    response = run_agent(user_message, session)
    return jsonify({"response": response})


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

if __name__ == "__main__":
    app.run(port=5000, debug=True)