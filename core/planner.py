import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SYSTEM_PROMPT = """You are the planning brain of an AI agent called ANVIL.

You are given:
1. The user's request
2. A list of tools currently available to you
3. Conversation and tool-call history so far

You must decide ONE of the following:
- "answer": you can respond directly without any tool
- "call_tool": you need to use one of the available tools
- "no_tool_fits": none of the available tools can accomplish this task

CRITICAL RULE: If the conversation history shows a tool call was DENIED by
the user ("DENIED by user"), you MUST choose "answer" and inform the user
their request was not completed because they denied approval. Do NOT attempt
to forge a new tool or find another way to accomplish the same action — a
denial means the user does not want this action performed right now, not
that a better tool is needed.

Respond ONLY with valid JSON in exactly this shape, nothing else:

For answering directly:
{"action": "answer", "content": "your response text"}

For calling a tool:
{"action": "call_tool", "tool_name": "exact_tool_name", "arguments": {"key": "value"}}

For no tool fitting:
{"action": "no_tool_fits", "reason": "brief explanation of what capability is missing"}
"""


def plan(user_request: str, available_tools: list, conversation_context: str = "") -> dict:
    tools_description = json.dumps(available_tools, indent=2)

    user_prompt = f"""Available tools:
{tools_description}

Conversation so far:
{conversation_context}

User request: {user_request}

Decide your next action. Respond with JSON only."""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0,
        )
        raw = response.choices[0].message.content.strip()
        usage = response.usage
    except Exception as e:
        return {"action": "no_tool_fits", "reason": f"Planner API call failed: {str(e)}"}

    # Strip markdown code fences if the model adds them despite instructions
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        result = {"action": "no_tool_fits", "reason": f"Planner returned invalid JSON: {raw}"}
    result["_usage"] = {"prompt_tokens": usage.prompt_tokens, "completion_tokens": usage.completion_tokens}
    return result