from core.planner import plan
from tools.calculator import CalculatorTool
from tools.read_file import ReadFileTool
from core.session import Session

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
            result = tool.run(**arguments)
            print(f"  → Result: {result}")

            task_context += f"\n[Tool Call] {tool_name}({arguments}) -> {result}"

        elif action == "no_tool_fits":
            reason = decision.get("reason", "Unknown capability gap.")
            return f"[NO_TOOL_FITS] {reason}"

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