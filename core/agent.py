from core.planner import plan
from tools.calculator import CalculatorTool
from tools.read_file import ReadFileTool
from core.session import Session
from forge.tool_forge import forge_tool
from registry.registry import list_tools
import json
from registry.registry import get_tool_by_name

MAX_ITERATIONS = 5

# Registry of available tools (hardcoded for now — Phase 4 makes this dynamic)
TOOL_INSTANCES = {
    "calculator": CalculatorTool(),
    "read_file": ReadFileTool(),
}


def get_tool_descriptions() -> list:
    hardcoded = [tool.to_registry_entry() for tool in TOOL_INSTANCES.values()]
    forged = [
        {
            "name": t["name"],
            "description": t["description"],
            "input_schema": json.loads(t["input_schema"]),
        }
        for t in list_tools()
    ]
    return hardcoded + forged



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

            if tool:
                print(f"  → Calling hardcoded tool {tool_name} with {arguments}")
                try:
                    result = tool.run(**arguments)
                except Exception as e:
                    result = {"success": False, "error": f"Tool crashed: {str(e)}"}
            else:
                # Not hardcoded — try loading it from the registry
                stored_tool = get_tool_by_name(tool_name)
                if not stored_tool:
                    task_context += f"\n[System] Tool '{tool_name}' does not exist."
                    continue

                print(f"  → Calling forged tool {tool_name} with {arguments}")
                try:
                    namespace = {}
                    exec_globals = {"Tool": __import__("core.tool_base", fromlist=["Tool"]).Tool}
                    exec(stored_tool["code"], exec_globals, namespace)
                    tool_class = namespace[stored_tool["class_name"]]
                    instance = tool_class()
                    result = instance.run(**arguments)
                except Exception as e:
                    result = {"success": False, "error": f"Forged tool crashed: {str(e)}"}

            print(f"  → Result: {result}")
            task_context += f"\n[Tool Call] {tool_name}({arguments}) -> {result}"

        elif action == "no_tool_fits":
            reason = decision.get("reason", "Unknown capability gap.")
            print(f"  → No existing tool fits. Reason: {reason}")
            print(f"  → Attempting to forge a new tool...")

            forge_result = forge_tool(user_request, reason)

            if forge_result.get("success"):
                print(f"\n  === TOOL FORGED, TESTED, AND CRITIC-APPROVED ===")
                print(f"  Class: {forge_result.get('class_name')}")
                print(f"  Attempts: {forge_result.get('attempts')}")
                print(f"  Critic verdict: {forge_result.get('critic_verdict')}")
                print(f"  Risk tier: {forge_result.get('risk_tier')}")
                print(f"  === END ===\n")
                return "[FORGE_SUCCESS] Tool tested, critic-reviewed, and registered for reuse."
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