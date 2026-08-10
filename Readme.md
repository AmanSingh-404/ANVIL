# ANVIL

**An agent that forges its own tools.**

ANVIL is a self-extending AI agent that starts with a minimal toolset and grows its own capabilities at runtime — writing new tools, testing them in a sandbox, getting them independently reviewed for safety, and keeping what works. It's built to answer a specific question: what happens if you make *tool creation itself* an agentic task, instead of something a developer has to do by hand?

**Live demo:** [anvil-seven-pi.vercel.app](https://anvil-seven-pi.vercel.app)
**API:** [anvil-production-8a98.up.railway.app](https://anvil-production-8a98.up.railway.app)
**Repo:** [github.com/AmanSingh-404/ANVIL](https://github.com/AmanSingh-404/ANVIL)

Built by **Aman Singh** — final-year B.Tech CSE (AI & ML), Lloyd Institute of Engineering & Technology.

---

## Table of contents

- [What it does](#what-it-does)
- [Why this is different from a typical agent wrapper](#why-this-is-different-from-a-typical-agent-wrapper)
- [Architecture](#architecture)
- [Tech stack](#tech-stack)
- [Project structure](#project-structure)
- [Running it locally](#running-it-locally)
- [Environment variables](#environment-variables)
- [API reference](#api-reference)
- [Deployment](#deployment)
- [Safety design](#safety-design)
- [Known limitations](#known-limitations)
- [Roadmap / future work](#roadmap--future-work)

---

## What it does

Give ANVIL a task it has no tool for — "reverse this string," "check if this number is prime," "convert Celsius to Fahrenheit" — and instead of failing, it:

1. **Plans** — recognizes the gap and decides a new tool is needed
2. **Forges** — writes the tool's code and its own test cases
3. **Sandboxes** — runs both in an isolated environment (no network, no filesystem access outside a scratch directory, hard timeout and memory limits)
4. **Reviews** — an independent Critic agent checks the generated code for unsafe patterns, separate from whether the tests passed
5. **Registers** — keeps the tool permanently if it clears both bars, so it's instantly reusable next time — no re-forging

Every side-effecting tool (writes, deletes, sends) pauses for human approval before running, with an audit trail of every decision. After each task, a Reflection agent decides if there's a genuine, reusable lesson worth remembering — and future planning steps retrieve relevant past lessons via semantic search. Tools that fail repeatedly in real use get automatically re-forged into an improved version, with full version history preserved.

---

## Why this is different from a typical agent wrapper

Most agent demos ship with a fixed toolset and call it done. ANVIL's actual contribution is the **safety and lifecycle machinery around self-authored code**, not the code generation itself:

- **Independent review, not self-certification** — the agent that writes a tool is never the agent that approves it. The Critic runs a separate call with an adversarial system prompt, and checks the tool's own risk-tier claim against what the code actually does.
- **Sandboxed by default, always** — every generated tool is executed in isolation before it's ever trusted, with network access, filesystem scope, memory, and execution time all restricted.
- **Human approval is a first-class state, not an afterthought** — side-effecting actions block on a real approval gate (CLI `input()` locally, an async polling/resolve flow over HTTP in the deployed dashboard), with a graduation mechanism for tools you've approved repeatedly.
- **Versioned, not just retried** — a tool that starts failing in real use gets re-forged into a new version, informed by its actual failure history, while the old version stays in the database as `deprecated` rather than being deleted.
- **Measured, not assumed** — every LLM call across all four agent roles (Planner, Codegen, Critic, Reflection) logs real token usage, so cost claims (e.g. "forging costs ~5x more than reusing") are backed by actual numbers, not estimates.

---

## Architecture

```
┌────────────┐     ┌───────────┐     ┌─────────────┐     ┌──────────┐     ┌────────────┐
│  PLANNER   │ ──▶ │   FORGE    │ ──▶ │   SANDBOX   │ ──▶ │  CRITIC  │ ──▶ │  REGISTRY  │
│ decides    │     │ writes tool│     │ runs it     │     │ reviews  │     │ keeps it   │
│ what's     │     │ + its own  │     │ isolated    │     │ for      │     │ if it earns│
│ needed     │     │ tests      │     │             │     │ unsafe   │     │ a place    │
└────────────┘     └───────────┘     └─────────────┘     │ patterns │     └─────┬──────┘
       ▲                                                   └──────────┘         │
       └───────────────────────────────────────────────────────────────────────┘
                      registered tools loop back into future planning
```

| Component | Responsibility |
|---|---|
| **Planner** (`core/planner.py`) | Decides whether to answer directly, call an existing tool, or flag a capability gap |
| **Tool Forge** (`forge/tool_forge.py`) | Generates new tool code and test cases; retries with error context on failure |
| **Sandbox** (`sandbox/executor.py`) | Runs generated and existing tool code in a resource-limited, network-isolated subprocess |
| **Critic** (`critic/critic.py`) | Independently reviews generated code for unsafe patterns before it's trusted |
| **Registry** (`registry/`) | SQLite store for tool metadata/code/versions + Chroma vector store for semantic tool and lesson retrieval |
| **Reflection** (`memory/reflection.py`) | Analyzes completed tasks, writes reusable lessons back into memory (skips routine successes) |
| **Approval** (`core/approval.py`) | CLI and async-web approval mechanisms for side-effecting tool calls |
| **Agent loop** (`core/agent.py`) | Ties everything together — the ReAct-style plan → act → observe cycle |
| **API server** (`api_server.py`) | Flask layer exposing chat, tool registry, approval queue, and trace history over HTTP, with per-session isolation, rate limiting, and CORS restriction |
| **Dashboard** (`dashboard/`) | Next.js frontend — landing page, chat pane, live tool registry, approval card UI, and expandable trace replay with real token cost |

---

## Tech stack

**Backend**
- Python 3.13
- [Groq](https://groq.com) API (`llama-3.1-8b-instant`) for all four agent roles
- Flask + Flask-CORS + Flask-Limiter
- SQLite (tool registry) + ChromaDB (semantic retrieval — tools and lessons)
- `sentence-transformers` (`all-MiniLM-L6-v2`, local, CPU-only) for embeddings
- `psutil` for cross-process memory monitoring in the sandbox
- Waitress (production WSGI server)

**Frontend**
- Next.js 16 (App Router), plain JavaScript
- Space Grotesk + IBM Plex Mono (self-hosted via `next/font`)
- No CSS framework — a hand-built design system (see `dashboard/src/app/globals.css`)

**Infrastructure**
- Backend deployed on **Railway** (persistent volume for SQLite/Chroma data, separated from source code)
- Frontend deployed on **Vercel**
- Groq for LLM inference

---

## Project structure

```
ANVIL/
├── core/               # planner, agent loop, session memory, approval mechanisms
│   ├── agent.py
│   ├── planner.py
│   ├── session.py
│   ├── approval.py
│   ├── audit_log.py
│   └── tool_base.py
├── forge/              # tool code generation, test generation, forge pipeline
│   ├── tool_forge.py
│   └── forge_log.py
├── sandbox/            # isolated execution environment
│   ├── executor.py
│   └── test_executor.py
├── critic/             # independent adversarial code review
│   └── critic.py
├── registry/           # SQLite registry + Chroma vector store + migrations
│   ├── db.py
│   ├── registry.py
│   ├── vector_store.py
│   └── migrate_*.py
├── memory/             # reflection engine
│   └── reflection.py
├── tools/              # hardcoded starter tools (calculator, read_file)
├── scratch/            # sandboxed filesystem scope for tools
├── dashboard/          # Next.js frontend
│   └── src/app/
│       ├── page.js             # landing page
│       ├── dashboard/page.js   # chat + registry + approval + trace UI
│       └── components/
├── api_server.py       # Flask API layer
├── requirements.txt
└── railway.json
```

---

## Running it locally

### Backend

```bash
python -m venv venv
# Windows: .\venv\Scripts\Activate.ps1
# macOS/Linux: source venv/bin/activate

pip install -r requirements.txt
```

Create a `.env` file in the project root:
```
GROQ_API_KEY=your_key_here
```

Initialize the database:
```bash
python -m registry.db
python -m registry.migrate_add_risk_tier
python -m registry.migrate_add_approval_tracking
```
(These also run automatically on every `api_server.py` startup, so this step is a one-time convenience for CLI-only use.)

Run the API server:
```bash
python api_server.py
```

Or run ANVIL directly in the terminal, no API/dashboard needed:
```bash
python -m core.agent
```

### Frontend

```bash
cd dashboard
npm install
```

Create `dashboard/.env.local`:
```
NEXT_PUBLIC_API_URL=http://localhost:5000
```

```bash
npm run dev
```

Open `http://localhost:3000` for the landing page, or `http://localhost:3000/dashboard` directly for the chat interface.

---

## Environment variables

**Backend (`.env` locally, platform variables in production)**

| Variable | Purpose | Default |
|---|---|---|
| `GROQ_API_KEY` | Groq API key — required | — |
| `ANVIL_ENV` | `production` runs waitress; anything else runs Flask's dev server | `development` |
| `ANVIL_SANDBOX_TIMEOUT` | Sandbox execution timeout, seconds | `3` |
| `ANVIL_SANDBOX_MEMORY_MB` | Sandbox memory ceiling, MB | `60` |
| `ANVIL_DATA_DIR` | Where SQLite/Chroma data lives — keep separate from source in production | `registry` |
| `ANVIL_FRONTEND_URL` | Production frontend origin, for CORS | — |
| `PORT` | Server port (set automatically by most PaaS platforms) | `5000` |

**Frontend (`.env.local` locally, platform variables in production)**

| Variable | Purpose | Default |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | Backend API base URL | `http://localhost:5000` |

---

## API reference

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/health` | GET | Liveness check |
| `/api/chat` | POST | Send a message; returns the agent's response and a full step-by-step trace. Requires `X-Session-Id` header. Rate-limited to 15/min per session. |
| `/api/tools` | GET | List all registered tools (name, version, risk tier, success/failure counts) |
| `/api/history` | GET | Full task history for a session, including per-task traces. Requires `X-Session-Id` header. |
| `/api/cost-summary` | GET | Per-task token cost breakdown, flags which tasks involved forging. Requires `X-Session-Id` header. |
| `/api/approval/pending` | GET | Poll for a pending approval request in the current session |
| `/api/approval/resolve` | POST | Approve or deny a pending action (`{"approved": true/false}`) |

---

## Deployment

- **Backend** — Railway, using Nixpacks auto-detection from `requirements.txt`. Runs `waitress` in production mode (`ANVIL_ENV=production`). SQLite and Chroma data live on a persistent volume mounted at a path *separate* from the source code (`ANVIL_DATA_DIR`) — mounting a volume directly over a source directory wipes the code, which is a real mistake this project hit and fixed (see commit history).
- **Frontend** — Vercel, root directory set to `dashboard/`, `NEXT_PUBLIC_API_URL` pointed at the Railway backend.
- **Dependencies** — `torch` is pinned to the CPU-only build (`torch==2.13.0+cpu` with PyTorch's CPU wheel index) since `sentence-transformers` only needs CPU inference for its small embedding model; the default GPU build otherwise pulls in several unnecessary gigabytes of CUDA libraries.

---

## Safety design

- **Sandboxed execution**: subprocess isolation, hard timeout, memory ceiling (measured across the process *and* its descendants — a real Windows-specific bug where venv spawns a child interpreter was found and fixed here), no network access (patched at the `socket` level), filesystem access restricted to a scratch directory (patched at `builtins.open`, with path-traversal protection).
- **Independent Critic review**: a separate LLM call, adversarial system prompt, checks for unbounded loops, filesystem/network escape attempts, credential access, `eval`/`exec`/dynamic imports, and shell execution — regardless of whether the tool's own tests passed. Verified live to correctly reject a request for arbitrary shell execution.
- **Human-in-the-loop approval**: every `side_effecting` tool call pauses for explicit approval (fail-safe default — unclassified tools default to requiring approval, not to auto-running). Repeated approvals can graduate a tool to auto-run, opt-in only. Every decision is logged to an audit trail.
- **Code-level duplicate-call guard**: independent of prompt instructions, the agent loop caches successful tool results within a task and refuses to re-execute an identical call — a real backstop found necessary after observing the Planner occasionally attempt redundant calls despite explicit prompt instructions not to.
- **Rate limiting**: per-session limits on the chat endpoint, verified under genuine concurrent load (not just sequential requests, which don't actually test burst behavior).
- **Graceful upstream failure handling**: Groq rate-limit errors are caught and returned as a clean `503` with a user-facing message, not a raw stack trace.

---

## Known limitations

- Sandboxing is process-level (Python `subprocess` + `psutil` monitoring), not OS-level (e.g. Docker network namespaces) — sufficient against naive or accidental unsafe code, not a hardened defense against a determined adversary with low-level tricks (`ctypes`, direct syscalls).
- Fork-bomb protection is untested on Windows since `os.fork` doesn't exist there; the sandbox's timeout and memory-limit mechanisms would still constrain excessive resource use attempted through other means on this platform.
- Lesson memory is capped at 200 entries with no consolidation or pruning strategy beyond the hard cap.
- A public deployment is bounded by the shared Groq API key's daily token quota — heavy usage by any user can affect availability for others until the quota resets.
- No persistent user accounts — sessions are anonymous, tied to a browser-generated ID stored in `localStorage`.

---

## Roadmap / future work

- OS-level sandbox isolation (Docker per-execution) for stronger guarantees against adversarial generated code
- Lesson memory consolidation/summarization instead of a hard cutoff
- Per-tool cost/performance dashboards over time, not just per-task
- Exportable/importable tool packages, so a forged tool could be shared across ANVIL instances