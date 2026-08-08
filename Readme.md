# ANVIL — A self-extending AI agent that forges its own tools

ANVIL is a personal AI agent that starts with a minimal toolset and grows its own
capabilities at runtime — writing new tools, testing them in a sandbox, getting
them reviewed by an independent safety-critic agent, and keeping what works.

## Setup

### Backend (Python)
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install groq python-dotenv psutil sentence-transformers chromadb flask flask-cors


Create a `.env` file in the project root:

GROQ_API_KEY=your_key_here


Initialize the databases:

python -m registry.db
python -m registry.migrate_add_risk_tier
python -m registry.migrate_add_approval_tracking


### Frontend (Next.js)

cd dashboard
npm install


## Running it

**Terminal 1 — API server:**

python api_server.py


**Terminal 2 — Dashboard:**

cd dashboard
npm run dev


Open `http://localhost:3000` for the landing page, or `http://localhost:3000/dashboard`
directly for the chat interface.

**CLI mode (no dashboard):**

python -m core.agent


## Architecture

- `core/` — planner, agent loop, session memory, approval mechanisms
- `forge/` — tool code generation, test generation, forge pipeline
- `sandbox/` — isolated execution environment (timeout, memory limits, network/filesystem restrictions)
- `critic/` — independent adversarial code review
- `registry/` — SQLite tool storage + Chroma vector store for semantic retrieval
- `memory/` — reflection engine, forge attempt logging
- `dashboard/` — Next.js frontend (chat, tool registry view, approval queue, trace replay)

## Known limitations

- Sandboxing is process-level (Python `subprocess` + monitoring), not OS-level
  (e.g. Docker network namespaces) — sufficient against naive/accidental unsafe
  code, not a hardened defense against a determined adversary.
- Fork-bomb protection is untested on Windows since `os.fork` is POSIX-only.
- Single global session/approval state — not multi-user safe (fine for a local,
  single-user demo; would need per-session state for production).
- Lesson memory is capped at 200 entries with no consolidation/pruning strategy.

Built by Aman Singh — final year B.Tech CSE (AI & ML), Lloyd Institute of
Engineering & Technology.