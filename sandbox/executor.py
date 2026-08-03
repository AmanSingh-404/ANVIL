import subprocess
import sys
import os
import tempfile

DEFAULT_TIMEOUT_SECONDS = 5


def run_in_sandbox(code: str, timeout: int = DEFAULT_TIMEOUT_SECONDS) -> dict:
    """
    Executes a string of Python code in an isolated subprocess.
    Returns a structured result — never raises to the caller.
    """
    # Write the code to a temp file rather than passing via -c,
    # so tracebacks reference a real filename (easier to debug later).
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8"
    ) as tmp:
        tmp.write(code)
        tmp_path = tmp.name

    try:
        result = subprocess.run(
            [sys.executable, tmp_path],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "stdout": "",
            "stderr": f"Execution timed out after {timeout} seconds.",
            "returncode": None,
        }
    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": f"Sandbox execution failed: {str(e)}",
            "returncode": None,
        }
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass