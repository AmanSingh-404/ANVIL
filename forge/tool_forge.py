import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

CODEGEN_SYSTEM_PROMPT = """You are the Tool Forge of an AI agent called ANVIL.

Your job: write a single, self-contained Python tool that fills a capability gap.

STRICT REQUIREMENTS:
1. The tool must be a class that subclasses `Tool` from `core.tool_base`.
2. It must define: name (str), description (str), input_schema (dict), and a run(self, **kwargs) method.
3. run() must return a dict shaped like {"success": True, "output": ...} or {"success": False, "error": "..."}.
4. Only use Python standard library — no external packages, no network access, no file access outside a "scratch/" directory.
5. Wrap risky operations in try/except and return a clean error dict instead of raising.
6. Do NOT include the `from core.tool_base import Tool` import line yourself — it will be added automatically.
7. Output ONLY the Python class code. No explanation, no markdown fences, no extra text.

Example shape:

class ExampleTool(Tool):
    name = "example_tool"
    description = "Does something specific."
    input_schema = {"some_input": {"type": "string", "description": "..."}}

    def run(self, **kwargs) -> dict:
        try:
            value = kwargs.get("some_input", "")
            result = value.upper()
            return {"success": True, "output": result}
        except Exception as e:
            return {"success": False, "error": str(e)}
"""


def generate_tool_code(task_description: str, reason: str) -> str:
    user_prompt = f"""A user requested: "{task_description}"

No existing tool could handle it. Reason: {reason}

Write a new Tool class that would accomplish this task. Follow all requirements exactly."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": CODEGEN_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,  # slight creativity allowed for code generation, unlike the Planner
    )

    raw = response.choices[0].message.content.strip()

    # Strip markdown fences if present despite instructions
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.startswith("python"):
            raw = raw[6:]
        raw = raw.strip()

    return raw


def forge_tool(task_description: str, reason: str) -> dict:
    """
    Given a task the agent couldn't accomplish with existing tools,
    attempts to generate a brand-new tool to fill that gap.
    """
    generated_code = generate_tool_code(task_description, reason)

    # For now, just return the generated code — testing/sandboxing
    # comes in Step 3.3-3.4. We want to SEE what gets generated first.
    return {
        "success": True,
        "generated_code": generated_code,
    }