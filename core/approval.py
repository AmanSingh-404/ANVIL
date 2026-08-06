def request_approval(tool_name: str, arguments: dict, description: str) -> bool:
    """
    Pauses execution and asks the user (via CLI for now) to approve
    a side-effecting tool call before it runs.

    Returns True if approved, False if denied.
    """
    print(f"\n  ⚠ APPROVAL REQUIRED")
    print(f"  Tool: {tool_name}")
    print(f"  Description: {description}")
    print(f"  Arguments: {arguments}")

    while True:
        response = input("  Approve this action? (y/n): ").strip().lower()
        if response in ("y", "yes"):
            return True
        elif response in ("n", "no"):
            return False
        else:
            print("  Please type 'y' or 'n'.")