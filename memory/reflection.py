import os
import json
from groq import Groq
from dotenv import load_dotenv
import uuid
from registry.vector_store import store_lesson, query_relevant_lessons

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

REFLECTION_SYSTEM_PROMPT = """You are the reflection module of an AI agent called ANVIL.

After a task completes, review what happened and decide if there's a genuinely
useful, reusable lesson worth remembering for future similar tasks.

Only write a note if there's a REAL, actionable insight — e.g. a tool that
failed and why, a tool that worked well for a specific kind of task, a pattern
in what the user asks for. Do NOT write a note for routine, uneventful
successes with nothing to learn.

Respond ONLY with valid JSON in exactly this shape:
{"has_lesson": true, "lesson": "short, specific, reusable note"}
or
{"has_lesson": false}
"""


def reflect_on_task(user_request: str, task_trace: str, final_result: str) -> dict:
    user_prompt = f"""Task: {user_request}

What happened (tool calls, forge attempts, errors):
{task_trace}

Final result given to the user: {final_result}

Is there a genuinely useful lesson here worth remembering?"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": REFLECTION_SYSTEM_PROMPT},
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

    except (json.JSONDecodeError, Exception) as e:
        return {"has_lesson": False, "error": str(e)}

def reflect_and_store(user_request: str, task_trace: str, final_result: str):
    from registry.vector_store import lesson_count, MAX_LESSONS

    reflection = reflect_on_task(user_request, task_trace, final_result)
    if reflection.get("has_lesson"):
        if lesson_count() >= MAX_LESSONS:
            print(f"  [reflection] Lesson learned but memory cap ({MAX_LESSONS}) reached — not stored. (Future work: consolidation/pruning.)")
            return reflection
        lesson_text = reflection["lesson"]
        lesson_id = str(uuid.uuid4())
        store_lesson(lesson_id, lesson_text)
        print(f"  [reflection] Learned: {lesson_text}")
    return reflection