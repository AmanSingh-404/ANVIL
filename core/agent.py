from core.planner import plan
from tools.calculator import CalculatorTool
from tools.read_file import ReadFileTool

MAX_ITERATIONS = 5

# Registry of available tools (hardcoded for now — Phase 4 makes this dynamic)
TOOL_INSTANCES = {
    "calculator": CalculatorTool(),
    "read_file": ReadFileTool(),
}


def get_tool_descriptions() -> list:
    return [tool.to_registry_entry() for tool in TOOL_INSTANCES.values()]


def run_agent(user_request: str) -> str:
    conversation_context = ""
    tools_available = get_tool_descriptions()

    for iteration in range(MAX_ITERATIONS):
        decision = plan(user_request, tools_available, conversation_context)
        action = decision.get("action")

        print(f"\n[Iteration {iteration + 1}] Planner decided: {action}")

        if action == "answer":
            return decision.get("content", "")

        elif action == "call_tool":
            tool_name = decision.get("tool_name")
            arguments = decision.get("arguments", {})

            tool = TOOL_INSTANCES.get(tool_name)
            if not tool:
                conversation_context += f"\n[System] Tool '{tool_name}' does not exist."
                continue

            print(f"  → Calling {tool_name} with {arguments}")
            result = tool.run(**arguments)
            print(f"  → Result: {result}")

            conversation_context += (
                f"\n[Tool Call] {tool_name}({arguments}) -> {result}"
            )
            # Loop continues — Planner sees this result on the next iteration
            # and decides whether to answer now or call another tool.

        elif action == "no_tool_fits":
            reason = decision.get("reason", "Unknown capability gap.")
            return f"[NO_TOOL_FITS] {reason}"
            # This is the exact hook Phase 3 (Tool Forge) will replace —
            # instead of giving up, it'll trigger tool creation here.

        else:
            return f"[ERROR] Unrecognized planner action: {action}"

    return "[MAX_ITERATIONS_REACHED] Agent could not complete the task in time."


if __name__ == "__main__":
    print("ANVIL — type your request (or 'exit' to quit)\n")
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ("exit", "quit"):
            break
        answer = run_agent(user_input)
        print(f"\nANVIL: {answer}\n")