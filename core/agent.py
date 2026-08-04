from core.planner import plan
from tools.calculator import CalculatorTool
from tools.read_file import ReadFileTool
from core.session import Session
from forge.tool_forge import forge_tool

MAX_ITERATIONS = 5

# Registry of available tools (hardcoded for now — Phase 4 makes this dynamic)
TOOL_INSTANCES = {
    "calculator": CalculatorTool(),
    "read_file": ReadFileTool(),
}


def get_tool_descriptions() -> list:
    return [tool.to_registry_entry() for tool in TOOL_INSTANCES.values()]



def run_agent(user_request: str, session: Session) -> str:
    tools_available = get_tool_descriptions()
    task_context = ""  # scoped to this single task's tool-call trace

    for iteration in range(MAX_ITERATIONS):
        full_context = session.as_context_string() + "\n" + task_context
        decision = plan(user_request, tools_available, full_context)
        action = decision.get("action")

        print(f"\n[Iteration {iteration + 1}] Planner decided: {action}")

        if action == "answer":
            return decision.get("content", "")

        elif action == "call_tool":
            tool_name = decision.get("tool_name")
            arguments = decision.get("arguments", {})

            tool = TOOL_INSTANCES.get(tool_name)
            if not tool:
                task_context += f"\n[System] Tool '{tool_name}' does not exist."
                continue

            print(f"  → Calling {tool_name} with {arguments}")
            try:
                result = tool.run(**arguments)
            except Exception as e:
                result = {"success": False, "error": f"Tool crashed: {str(e)}"}
            print(f"  → Result: {result}")

            task_context += f"\n[Tool Call] {tool_name}({arguments}) -> {result}"

        elif action == "no_tool_fits":
            reason = decision.get("reason", "Unknown capability gap.")
            print(f"  → No existing tool fits. Reason: {reason}")
            print(f"  → Attempting to forge a new tool...")

            forge_result = forge_tool(user_request, reason)

            if forge_result.get("success"):
                generated_code = forge_result.get("generated_code", "")
                test_cases = forge_result.get("test_cases", [])
                print(f"\n  === GENERATED CODE ===\n{generated_code}\n  === END ===\n")
                print(f"  === GENERATED TESTS ===\n{test_cases}\n  === END ===\n")
                return "[FORGE_PREVIEW] Code + tests generated above — not yet sandbox-tested or registered (Step 3.4 next)."
            else:
                return f"[FORGE_FAILED] Could not create a tool for this task. Reason: {forge_result.get('error')}"

        else:
            return f"[ERROR] Unrecognized planner action: {action}"

    return "[MAX_ITERATIONS_REACHED] Agent could not complete the task in time."


if __name__ == "__main__":
    print("ANVIL — type your request (or 'exit' to quit)\n")
    session = Session()
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ("exit", "quit"):
            break
        answer = run_agent(user_input, session)
        session.add_turn("user", user_input)
        session.add_turn("agent", answer)
        print(f"\nANVIL: {answer}\n")