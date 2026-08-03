import subprocess
import sys
import os
import tempfile
import psutil
import time

DEFAULT_TIMEOUT_SECONDS = 5
DEFAULT_MEMORY_LIMIT_MB = 100


def run_in_sandbox(
    code: str,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
    memory_limit_mb: int = DEFAULT_MEMORY_LIMIT_MB,
) -> dict:
    """
    Executes a string of Python code in an isolated subprocess,
    enforcing both a timeout and a memory ceiling.
    """
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8"
    ) as tmp:
        tmp.write(code)
        tmp_path = tmp.name

    proc = None
    try:
        proc = subprocess.Popen(
            [sys.executable, tmp_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        ps_proc = psutil.Process(proc.pid)
        start_time = time.time()
        killed_reason = None

        while proc.poll() is None:
            elapsed = time.time() - start_time

            if elapsed > timeout:
                killed_reason = f"Execution timed out after {timeout} seconds."
                proc.kill()
                break

            try:
                mem_mb = ps_proc.memory_info().rss / (1024 * 1024)
                print(f"    [debug] pid={ps_proc.pid} name={ps_proc.name()} mem={mem_mb:.1f} MB")  # TEMP DEBUG
                if mem_mb > memory_limit_mb:
                    killed_reason = f"Memory limit of {memory_limit_mb}MB exceeded."
                    proc.kill()
                    break
            except psutil.NoSuchProcess:
                break

            time.sleep(0.05)  # poll interval

        stdout, stderr = proc.communicate()

        if killed_reason:
            return {
                "success": False,
                "stdout": stdout,
                "stderr": killed_reason,
                "returncode": None,
            }

        return {
            "success": proc.returncode == 0,
            "stdout": stdout,
            "stderr": stderr,
            "returncode": proc.returncode,
        }

    except Exception as e:
        if proc:
            proc.kill()
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