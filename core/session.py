MAX_CONTEXT_CHARS = 4000  # rough safety cap; ~1000 tokens


class Session:
    """
    Tracks conversation history across turns, and tool-call context
    within a single task. Truncates from the oldest entries first
    if it grows too large.
    """

    def __init__(self):
        self.turns = []  # list of {"role": "user"/"agent", "content": str}

    def add_turn(self, role: str, content: str):
        self.turns.append({"role": role, "content": content})
        self._trim()

    def _trim(self):
        # Drop oldest turns first if we exceed the char budget.
        while self._total_chars() > MAX_CONTEXT_CHARS and len(self.turns) > 1:
            self.turns.pop(0)

    def _total_chars(self) -> int:
        return sum(len(t["content"]) for t in self.turns)

    def as_context_string(self) -> str:
        lines = [f"[{t['role']}] {t['content']}" for t in self.turns]
        return "\n".join(lines)