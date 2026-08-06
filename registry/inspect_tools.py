import sys
from registry.registry import list_tools, get_tool_by_name


def print_all_tools():
    tools = list_tools()
    if not tools:
        print("No tools in registry.")
        return
    print(f"{'Name':<25} {'Version':<8} {'Source':<10} {'Success':<8} {'Fail':<6}")
    print("-" * 65)
    for t in tools:
        print(f"{t['name']:<25} {t['version']:<8} {t['source']:<10} {t['success_count']:<8} {t['failure_count']:<6}")


def print_tool_code(name: str):
    tool = get_tool_by_name(name)
    if not tool:
        print(f"No approved tool found named '{name}'")
        return
    print(f"--- {name} (v{tool['version']}) ---")
    print(tool["code"])


if __name__ == "__main__":
    if len(sys.argv) > 1:
        print_tool_code(sys.argv[1])
    else:
        print_all_tools()