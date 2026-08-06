import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

CRITIC_SYSTEM_PROMPT = """You are a security-focused code reviewer for an AI agent called ANVIL.

ANVIL's Tool Forge generates Python tools automatically. Your job is to review
generated code and catch unsafe patterns BEFORE it is trusted — independent of
whether the code's own tests passed.

Specifically look for:
1. Unbounded loops or recursion with no clear termination condition
2. Filesystem access outside a "scratch/" directory, or attempts to bypass
   path restrictions (e.g. using os.path tricks, symlinks, ctypes)
3. Any network access attempt (sockets, urllib, requests, etc.)
4. Attempts to access environment variables, credentials, or secrets
5. Use of eval(), exec(), or dynamic imports that could execute arbitrary code
6. Any subprocess, os.system, or shell command execution
7. Anything that looks deliberately obfuscated or unusually complex for the
   tool's stated purpose

Be an ADVERSARIAL reviewer — assume the code might be trying to hide something,
even if it looks innocent. But do not reject code just for being simple or for
using try/except — that is expected and good practice.

Respond ONLY with valid JSON in exactly this shape:
{"verdict": "approve", "reason": "brief justification"}
or
{"verdict": "reject", "reason": "specific unsafe pattern found"}
or
{"verdict": "needs_human_review", "reason": "ambiguous case, explain why"}
"""


def review_code(tool_code: str) -> dict:
    user_prompt = f"""Review this generated tool code:

{tool_code}

Give your verdict."""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": CRITIC_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0,
        )
        raw = response.choices[0].message.content.strip()

        if raw.startswith("```"):
            raw = raw.strip("`")
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        return json.loads(raw)

    except json.JSONDecodeError:
        return {"verdict": "needs_human_review", "reason": f"Critic returned invalid JSON: {raw}"}
    except Exception as e:
        return {"verdict": "needs_human_review", "reason": f"Critic API call failed: {str(e)}"}