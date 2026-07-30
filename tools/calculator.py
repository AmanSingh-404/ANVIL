from core.tool_base import Tool


class CalculatorTool(Tool):
    name = "calculator"
    description = "Evaluates a basic arithmetic expression, e.g. '12 * (3 + 4)'."
    input_schema = {
        "expression": {"type": "string", "description": "A math expression to evaluate"}
    }

    def run(self, **kwargs) -> dict:
        expression = kwargs.get("expression", "")
        try:
            # Restrict eval to only digits/operators — no builtins, no names.
            allowed_chars = set("0123456789+-*/(). ")
            if not set(expression) <= allowed_chars:
                return {"success": False, "error": "Expression contains disallowed characters."}
            result = eval(expression, {"__builtins__": {}}, {})
            return {"success": True, "output": result}
        except Exception as e:
            return {"success": False, "error": str(e)}