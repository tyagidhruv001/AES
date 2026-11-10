#!/usr/bin/env python3
"""Automated unit test suite for Aether Quality Engine.

Tests:
  1. Multi-ecosystem command discovery (Node.js, Python, Java, Rust, Go).
  2. Execution harness with passing exit code 0.
  3. Execution harness with non-zero exit code.
  4. Execution harness timeout handling.
  5. Diff audit: Surgical diff under 200 lines.
  6. Diff audit: Excessive diff over 400 lines flagged.
  7. Diff audit: Leftover debug prints flagged.

Standard library only. Exits with 0 on pass, 1 on fail.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

from quality_engine import audit_diff, discover_commands, execute_check  # noqa: E402

PASS = "\033[32mPASS\033[0m"
FAIL = "\033[31mFAIL\033[0m"
failures: list[str] = []


def _assert(name: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"  {PASS}  {name}")
    else:
        label = f"  {FAIL}  {name}"
        if detail:
            label += f"\n         {detail}"
        print(label)
        failures.append(name)


def run_tests() -> int:
    print("=" * 60)
    print("Aether Quality Engine — Automated Test Suite")
    print("=" * 60)

    # -------------------------------------------------------------
    # Test 1: Multi-ecosystem command discovery
    # -------------------------------------------------------------
    print("\n[1] Multi-ecosystem command discovery")
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)

        # Node.js mock
        (d / "package.json").write_text('{"scripts": {"test": "jest", "build": "vite build"}}', encoding="utf-8")
        # Python mock
        (d / "pytest.ini").write_text('[pytest]\naddopts = -v', encoding="utf-8")
        # Rust mock
        (d / "Cargo.toml").write_text('[package]\nname = "demo"', encoding="utf-8")
        # Go mock
        (d / "go.mod").write_text('module example.com/demo', encoding="utf-8")
        # Java mock
        (d / "pom.xml").write_text('<project></project>', encoding="utf-8")

        cmds = discover_commands(d)
        ecosystems = {c["ecosystem"] for c in cmds}
        types = {c["type"] for c in cmds}

        _assert("Node.js ecosystem discovered", "Node.js" in ecosystems)
        _assert("Python ecosystem discovered", "Python" in ecosystems)
        _assert("Rust ecosystem discovered", "Rust" in ecosystems)
        _assert("Go ecosystem discovered", "Go" in ecosystems)
        _assert("Java ecosystem discovered", "Java/Maven" in ecosystems)
        _assert("Test commands present", "test" in types)
        _assert("Build commands present", "build" in types)

    # -------------------------------------------------------------
    # Test 2: Execution harness with passing exit code
    # -------------------------------------------------------------
    print("\n[2] Execution harness with passing command")
    pass_res = execute_check("python -c \"print('Hello from test')\"", cwd=Path.cwd())
    _assert("Status is PASSED", pass_res["status"] == "PASSED")
    _assert("Exit code is 0", pass_res["exit_code"] == 0)
    _assert("Duration is recorded", pass_res["duration_seconds"] >= 0.0)
    _assert("Stdout contains output", "Hello from test" in pass_res["stdout_summary"])

    # -------------------------------------------------------------
    # Test 3: Execution harness with failing exit code
    # -------------------------------------------------------------
    print("\n[3] Execution harness with failing command")
    fail_res = execute_check("python -c \"import sys; sys.exit(42)\"", cwd=Path.cwd())
    _assert("Status is FAILED", fail_res["status"] == "FAILED")
    _assert("Exit code is 42", fail_res["exit_code"] == 42)

    # -------------------------------------------------------------
    # Test 4: Execution harness timeout handling
    # -------------------------------------------------------------
    print("\n[4] Execution harness timeout handling")
    timeout_res = execute_check("python -c \"import time; time.sleep(10)\"", cwd=Path.cwd(), timeout_seconds=1)
    _assert("Status is TIMED_OUT", timeout_res["status"] == "TIMED_OUT")
    _assert("Exit code is -1", timeout_res["exit_code"] == -1)

    # -------------------------------------------------------------
    # Test 5: Diff audit — Surgical diff
    # -------------------------------------------------------------
    print("\n[5] Diff audit: Surgical diff under 200 lines")
    sample_diff = """--- a/src/auth.py
+++ b/src/auth.py
@@ -10,6 +10,12 @@
 def verify_token(token):
-    return False
+    if not token:
+        return False
+    return is_valid(token)
"""
    diff_res = audit_diff(sample_diff)
    _assert("Verdict is SURGICAL", diff_res["verdict"] == "SURGICAL")
    _assert("is_surgical is True", diff_res["is_surgical"] is True)
    _assert("Files count is 1", diff_res["files_count"] == 1)
    _assert("File name captured", "src/auth.py" in diff_res["files"])

    # -------------------------------------------------------------
    # Test 6: Diff audit — Excessive diff over 400 lines
    # -------------------------------------------------------------
    print("\n[6] Diff audit: Excessive diff over 400 lines flagged")
    large_lines = ["--- a/big.py", "+++ b/big.py", "@@ -1,1 +1,500 @@"]
    for i in range(450):
        large_lines.append(f"+    line_content_{i} = {i}")
    large_diff = "\n".join(large_lines)

    large_res = audit_diff(large_diff)
    _assert("Verdict is EXCESSIVE_DIFF", large_res["verdict"] == "EXCESSIVE_DIFF")
    _assert("requires_justification is True", large_res["requires_justification"] is True)
    _assert("is_surgical is False", large_res["is_surgical"] is False)

    # -------------------------------------------------------------
    # Test 7: Diff audit — Leftover debug prints flagged
    # -------------------------------------------------------------
    print("\n[7] Diff audit: Leftover debug prints flagged")
    debug_diff = """--- a/app.js
+++ b/app.js
@@ -1,5 +1,8 @@
 function handleEvent(e) {
+    console.log("DEBUG: event received", e);
+    debugger;
     return process(e);
 }
"""
    debug_res = audit_diff(debug_diff)
    _assert("Leftover debug count is 2", debug_res["leftover_debug_count"] == 2)
    snippets = [a["snippet"] for a in debug_res["leftover_debug_alerts"]]
    _assert("console.log caught", any("console.log" in s for s in snippets))
    _assert("debugger caught", any("debugger" in s for s in snippets))

    print()
    if failures:
        print(f"RESULT: {len(failures)} test(s) FAILED: {failures}")
        return 1
    print("RESULT: All 7 Quality Engine tests PASSED.")
    return 0


if __name__ == "__main__":
    sys.exit(run_tests())
