from sandbox.executor import run_in_sandbox


def test_normal_execution():
    result = run_in_sandbox("print(2 + 2)")
    assert result["success"] is True
    assert "4" in result["stdout"]
    print("[PASS] test_normal_execution")


def test_infinite_loop_times_out():
    result = run_in_sandbox("while True: pass", timeout=3)
    assert result["success"] is False
    assert "timed out" in result["stderr"]
    print("[PASS] test_infinite_loop_times_out")


def test_memory_limit_enforced():
    code = "import time; x = [0] * (10**8); time.sleep(2)"
    result = run_in_sandbox(code, memory_limit_mb=50, timeout=5)
    assert result["success"] is False
    assert "Memory limit" in result["stderr"]
    print("[PASS] test_memory_limit_enforced")


def test_network_access_blocked():
    code = 'import socket; s = socket.socket(); s.connect(("google.com", 80))'
    result = run_in_sandbox(code)
    assert result["success"] is False
    assert "Network access is disabled" in result["stderr"]
    print("[PASS] test_network_access_blocked")


def test_filesystem_access_outside_scratch_blocked():
    code = 'open("C:/Windows/System32/drivers/etc/hosts", "r")'
    result = run_in_sandbox(code)
    assert result["success"] is False
    assert "outside scratch directory" in result["stderr"]
    print("[PASS] test_filesystem_access_outside_scratch_blocked")


def test_filesystem_access_inside_scratch_allowed():
    code = 'open("scratch/test.txt", "r").read()'
    result = run_in_sandbox(code)
    assert result["success"] is True
    print("[PASS] test_filesystem_access_inside_scratch_allowed")


if __name__ == "__main__":
    test_normal_execution()
    test_infinite_loop_times_out()
    test_memory_limit_enforced()
    test_network_access_blocked()
    test_filesystem_access_outside_scratch_blocked()
    test_filesystem_access_inside_scratch_allowed()
    print("\nAll sandbox tests passed.")