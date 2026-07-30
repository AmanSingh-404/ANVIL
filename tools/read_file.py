import os
from core.tool_base import Tool

SCRATCH_DIR = os.path.abspath("scratch")


class ReadFileTool(Tool):
    name = "read_file"
    description = "Reads the contents of a text file inside the scratch directory."
    input_schema = {
        "filename": {"type": "string", "description": "Filename inside the scratch directory"}
    }

    def run(self, **kwargs) -> dict:
        filename = kwargs.get("filename", "")
        target_path = os.path.abspath(os.path.join(SCRATCH_DIR, filename))

        # Prevent path traversal outside scratch/ (e.g. "../../secrets.txt")
        if not target_path.startswith(SCRATCH_DIR):
            return {"success": False, "error": "Access outside scratch directory is not allowed."}

        if not os.path.exists(target_path):
            return {"success": False, "error": f"File not found: {filename}"}

        try:
            with open(target_path, "r", encoding="utf-8") as f:
                return {"success": True, "output": f.read()}
        except Exception as e:
            return {"success": False, "error": str(e)}