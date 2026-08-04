import subprocess
import sys
import os
import tempfile
import psutil
import time

DEFAULT_TIMEOUT_SECONDS = 5
DEFAULT_MEMORY_LIMIT_MB = 100


def _total_memory_mb(ps_proc: psutil.Process) -> float:
    """
    Sums RSS memory across the process AND all its descendants —
    on Windows, venv's python.exe can spawn a child interpreter that
    does the real work, so measuring only the parent undercounts badly.
    """
    total_bytes = 0
    try:
        total_bytes += ps_proc.memory_info().rss
        for child in ps_proc.children(recursive=True):
            try:
                total_bytes += child.memory_info().rss
            except psutil.NoSuchProcess:
                continue
    except psutil.NoSuchProcess:
        pass
    return total_bytes / (1024 * 1024)


def run_in_sandbox(
    code: str,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
    memory_limit_mb: int = DEFAULT_MEMORY_LIMIT_MB,
) -> dict:
    NETWORK_BLOCK_HEADER = '''
import socket as _socket

def _blocked_socket(*args, **kwargs):
    raise OSError("Network access is disabled in the ANVIL sandbox.")

_socket.socket = _blocked_socket
_socket.create_connection = _blocked_socket
'''

    full_code = NETWORK_BLOCK_HEADER + "\n" + code

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8"
    ) as tmp:
        tmp.write(full_code)
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

            mem_mb = _total_memory_mb(ps_proc)
            if mem_mb > memory_limit_mb:
                killed_reason = f"Memory limit of {memory_limit_mb}MB exceeded (used {mem_mb:.1f}MB)."
                proc.kill()
                break

            time.sleep(0.05)

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