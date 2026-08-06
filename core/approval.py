GRADUATION_THRESHOLD = 3


def request_approval(tool_name: str, arguments: dict, description: str) -> bool:
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


def offer_graduation(tool_name: str, approval_count: int) -> bool:
    """
    After a tool has been manually approved GRADUATION_THRESHOLD times,
    ask the user if they want to stop being prompted for it going forward.
    Returns True if the user opts to auto-approve from now on.
    """
    if approval_count < GRADUATION_THRESHOLD:
        return False

    print(f"\n  You've approved '{tool_name}' {approval_count} times.")
    response = input(f"  Auto-approve this tool from now on? (y/n): ").strip().lower()
    return response in ("y", "yes")