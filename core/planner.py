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
- "no_tool_fits": no tool exists yet, but one COULD be built to handle this
- "unsupported": this task falls into a KNOWN LIMITATION below and can NEVER
  be handled by forging a tool — do not confuse this with "no_tool_fits"

KNOWN LIMITATIONS — ANVIL cannot forge a working tool for these categories,
ever, regardless of retries. If a request falls into any of these, choose
"no_tool_fits" IMMEDIATELY on the first iteration, name which limitation
applies, and do NOT attempt to forge:

1. LIVE NETWORK ACCESS — checking a URL, calling an external API, fetching
   current exchange rates/weather/prices, web scraping. The sandbox
   permanently blocks all network access; no retry can work around this.

2. NON-STANDARD-LIBRARY PACKAGES — image generation, QR codes, PDF creation,
   or anything requiring a package beyond Python's standard library. The
   sandbox only permits stdlib; a forged tool cannot install dependencies.

3. MULTI-FILE OR NON-FUNCTION ARTIFACTS — web pages, full applications,
   anything requiring ongoing design decisions rather than a single
   deterministic function with clear inputs and outputs. ANVIL forges
   narrow tools, not projects.

4. REAL-TIME OR STATEFUL DATA — anything requiring live/current information
   the LLM's training data cannot know and the tool cannot fetch (network
   blocked). This overlaps with #1 but also covers cases phrased as pure
   "knowledge" questions about current events/prices/status.

For any of these, respond with "unsupported" and a reason naming the
specific limitation — this stops the system from wasting a forge attempt on
something that can never succeed.

CRITICAL RULE: If the conversation history already shows a successful tool
call whose output directly answers the current request, choose "answer"
using that output — do NOT call the same tool again with the same or
equivalent arguments.

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

For a known, permanent limitation:
{"action": "unsupported", "reason": "which known limitation applies and why"}
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
            model="openai/gpt-oss-20b",
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