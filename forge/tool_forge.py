import os
import json
from groq import Groq
from dotenv import load_dotenv
import re
from sandbox.executor import run_in_sandbox
from .forge_log import log_forge_attempt
from registry.registry import add_tool

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


def generate_tool_code(task_description: str, reason: str, prior_failure: str = None) -> str:
    user_prompt = f"""A user requested: "{task_description}"

No existing tool could handle it. Reason: {reason}

Write a new Tool class that would accomplish this task. Follow all requirements exactly."""

    if prior_failure:
        user_prompt += f"""

IMPORTANT: A previous attempt failed. Here is what went wrong — fix this specific issue:
{prior_failure}"""

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


TEST_GEN_SYSTEM_PROMPT = """You are a test-writer for AI-generated tools.

Given a Tool class's code, write 2-3 simple test cases as a Python list of dicts.
Each dict must have:
- "input": a dict of kwargs to pass to run()
- "expect_success": True or False (whether you expect this call to succeed)

Output ONLY a valid Python list literal, nothing else. No markdown, no explanation.

Example output:
[
    {"input": {"text": "hello"}, "expect_success": True},
    {"input": {}, "expect_success": True}
]
"""


def generate_test_cases(tool_code: str) -> list:
    user_prompt = f"""Here is the tool code:

{tool_code}

Write 2-3 test cases for it."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": TEST_GEN_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0,
    )

    raw = response.choices[0].message.content.strip()

    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.startswith("python"):
            raw = raw[6:]
        raw = raw.strip()

    try:
        import ast
        test_cases = ast.literal_eval(raw)
        return test_cases
    except (ValueError, SyntaxError):
        return []  # if parsing fails, we'll treat it as "no tests generated" downstream

def forge_tool(task_description: str, reason: str, max_attempts: int = 2) -> dict:
    """
    Given a task the agent couldn't accomplish with existing tools,
    generates a new tool, tests it in the sandbox, and reports the outcome.
    Registration (Phase 4) comes next — for now we just validate.
    """
    last_error = None

    for attempt in range(1, max_attempts + 1):
        generated_code = generate_tool_code(task_description, reason, prior_failure=last_error)
        class_name = _extract_class_name(generated_code)

        if not class_name:
            last_error = "Could not find a valid Tool subclass in generated code."
            continue

        test_cases = generate_test_cases(generated_code)
        if not test_cases:
            last_error = "Could not generate valid test cases."
            continue

        test_script = _build_test_script(generated_code, class_name, test_cases)
        sandbox_result = run_in_sandbox(test_script, timeout=10)

        if sandbox_result["success"] and "ALL_PASSED" in sandbox_result["stdout"]:
            tool_name, description, input_schema = _extract_tool_metadata(generated_code, class_name)

            add_tool(
                name=tool_name,
                description=description,
                input_schema=input_schema,
                code=generated_code,
                class_name=class_name,
                source="forged",
            )

            result = {
                "success": True,
                "generated_code": generated_code,
                "class_name": class_name,
                "tool_name": tool_name,
                "test_cases": test_cases,
                "test_output": sandbox_result["stdout"],
                "attempts": attempt,
            }
            log_forge_attempt(task_description, reason, result)
            return result
        else:
            last_error = (
                f"Tests failed.\nstdout: {sandbox_result['stdout']}\nstderr: {sandbox_result['stderr']}"
            )
            # Loop continues — retry with a fresh generation attempt

    # Only reached if the loop finishes without ever returning above —
    # i.e. every attempt failed.
    final_result = {
        "success": False,
        "error": f"Failed after {max_attempts} attempts. Last error: {last_error}",
    }
    log_forge_attempt(task_description, reason, final_result)
    return final_result

def _extract_tool_metadata(tool_code: str, class_name: str):
    """
    Actually imports the generated code in-process to read its class
    attributes cleanly, rather than regex-parsing them out of source text.
    Safe here because this code has ALREADY passed sandbox testing —
    we only do this AFTER validation, never before.
    """
    namespace = {}
    exec_globals = {"Tool": __import__("core.tool_base", fromlist=["Tool"]).Tool}
    exec(tool_code, exec_globals, namespace)
    tool_class = namespace[class_name]
    return tool_class.name, tool_class.description, tool_class.input_schema

def _extract_class_name(tool_code: str) -> str:
    match = re.search(r"class\s+(\w+)\s*\(\s*Tool\s*\)", tool_code)
    return match.group(1) if match else None


def _build_test_script(tool_code: str, class_name: str, test_cases: list) -> str:
    test_script = f'''
import sys
sys.path.insert(0, r"{os.getcwd()}")
from core.tool_base import Tool

{tool_code}

instance = {class_name}()
test_cases = {test_cases}

all_passed = True
for i, case in enumerate(test_cases):
    try:
        result = instance.run(**case["input"])
        actual_success = result.get("success", False)
        expected_success = case["expect_success"]
        if actual_success == expected_success:
            print(f"TEST {{i}} PASS")
        else:
            print(f"TEST {{i}} FAIL - expected success={{expected_success}}, got {{actual_success}}, result={{result}}")
            all_passed = False
    except Exception as e:
        print(f"TEST {{i}} ERROR - {{e}}")
        all_passed = False

print("ALL_PASSED" if all_passed else "SOME_FAILED")
'''
    return test_script