from core.planner import plan
from tools.calculator import CalculatorTool
from tools.read_file import ReadFileTool
from core.session import Session
from forge.tool_forge import forge_tool
from registry.registry import list_tools
import json
from registry.registry import get_tool_by_name
from core.approval import request_approval
from registry.registry import increment_approval_count, mark_auto_approved
from core.approval import request_approval, offer_graduation
from core.audit_log import log_approval_event
from registry.vector_store import query_relevant_tools

MAX_ITERATIONS = 5

# Registry of available tools (hardcoded for now — Phase 4 makes this dynamic)
TOOL_INSTANCES = {
    "calculator": CalculatorTool(),
    "read_file": ReadFileTool(),
}


def get_tool_descriptions(task_description: str = None, top_k: int = 5) -> list:
    hardcoded = [tool.to_registry_entry() for tool in TOOL_INSTANCES.values()]
    all_forged = {
        t["name"]: {
            "name": t["name"],
            "description": t["description"],
            "input_schema": json.loads(t["input_schema"]),
        }
        for t in list_tools()
    }

    if task_description is None or len(all_forged) <= top_k:
        # Small registry or no task context yet — just return everything
        return hardcoded + list(all_forged.values())

    relevant_names = query_relevant_tools(task_description, top_k=top_k)
    forged_subset = [all_forged[name] for name in relevant_names if name in all_forged]
    return hardcoded + forged_subset



def run_agent(user_request: str, session: Session) -> str:
    tools_available = get_tool_descriptions(task_description=user_request)
    task_context = ""  # scoped to this single task's tool-call trace
    executed_calls = {}  # (tool_name, sorted args json) -> result, prevents duplicate execution

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
            call_key = (tool_name, json.dumps(arguments, sort_keys=True))

            if call_key in executed_calls:
                cached_result = executed_calls[call_key]
                print(f"  → Duplicate call detected for {tool_name} — reusing cached result, not re-executing.")
                task_context += (
                    f"\n[System] You already called {tool_name}({arguments}) and got: {cached_result}. "
                    f"Do NOT call this again — use this result to answer now."
                )
                continue

            tool = TOOL_INSTANCES.get(tool_name)

            if tool:
                print(f"  → Calling hardcoded tool {tool_name} with {arguments}")
                try:
                    result = tool.run(**arguments)
                except Exception as e:
                    result = {"success": False, "error": f"Tool crashed: {str(e)}"}
                if result.get("success"):
                    executed_calls[call_key] = result
            else:
                # Not hardcoded — try loading it from the registry
                stored_tool = get_tool_by_name(tool_name)
                if not stored_tool:
                    task_context += f"\n[System] Tool '{tool_name}' does not exist."
                    continue
                if stored_tool["risk_tier"] == "side_effecting" and not stored_tool["auto_approved"]:
                    approved = request_approval(
                        tool_name, arguments, stored_tool["description"]
                    )
                    if not approved:
                        log_approval_event(tool_name, arguments, "denied")
                        result = {"success": False, "error": "User denied approval for this action."}
                        print(f"  → Denied by user.")
                        task_context += f"\n[Tool Call] {tool_name}({arguments}) -> DENIED by user"
                        continue

                    log_approval_event(tool_name, arguments, "approved")
                    new_count = increment_approval_count(tool_name)
                    if offer_graduation(tool_name, new_count):
                        mark_auto_approved(tool_name)
                        print(f"  → '{tool_name}' will now auto-approve going forward.")
                elif stored_tool["risk_tier"] == "side_effecting" and stored_tool["auto_approved"]:
                    log_approval_event(tool_name, arguments, "auto_approved")
                    print(f"  → '{tool_name}' is auto-approved, skipping prompt.")

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
                if result.get("success"):
                    executed_calls[call_key] = result

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