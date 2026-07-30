from abc import ABC, abstractmethod
from typing import Any, Dict


class Tool(ABC):
    """
    Base contract every tool (hardcoded or forged) must follow.
    """

    name: str = "unnamed_tool"
    description: str = "No description provided."

    # JSON-schema-style description of expected input, used by the Planner
    # to know what arguments to pass.
    input_schema: Dict[str, Any] = {}

    @abstractmethod
    def run(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the tool. Must return a dict like:
        {"success": True, "output": ...} or
        {"success": False, "error": "..."}
        """
        raise NotImplementedError

    def to_registry_entry(self) -> Dict[str, Any]:
        """
        Metadata shown to the Planner when deciding which tool to use.
        """
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
        }