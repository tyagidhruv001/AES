#!/usr/bin/env python3
"""Automated unit test suite for Aether PreToolUse Safety Gate Hook.

Tests:
  1. Allow safe shell command (npm test).
  2. Deny destructive rm -rf / command.
  3. Deny destructive Remove-Item -Recurse -Force command.
  4. Deny format disk command.
  5. Deny terraform destroy command.
  6. Deny kubectl delete namespace command.
  7. Deny drop database command.
  8. Ask on unparseable JSON stdin.
  9. Both CommandLine and command argument keys supported.

Standard library only. Exits with 0 on pass, 1 on fail.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
SAFETY_GATE = _HERE.parent / "adapters" / "antigravity" / "hooks" / "safety_gate.py"

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


def run_gate(payload_str: str) -> dict:
    proc = subprocess.run(
        [sys.executable, str(SAFETY_GATE)],
        input=payload_str,
        capture_output=True,
        text=True,
        timeout=5,
    )
    try:
        return json.loads(proc.stdout)
    except Exception:
        return {"decision": "ERROR", "raw": proc.stdout, "stderr": proc.stderr}


def test_safety_gate():
    print("=" * 60)
    print("Aether Safety Gate Hook — Automated Test Suite")
    print("=" * 60)

    # 1. Allow safe command
    print("\n[1] Allow safe shell commands")
    res1 = run_gate(json.dumps({"toolCall": {"tool": "run_command", "args": {"CommandLine": "npm test"}}}))
    _assert("Safe npm test is allowed", res1.get("decision") == "allow")

    # 2. Deny rm -rf /
    print("\n[2] Deny destructive rm -rf /")
    res2 = run_gate(json.dumps({"toolCall": {"tool": "run_command", "args": {"CommandLine": "rm -rf /"}}}))
    _assert("rm -rf / is denied", res2.get("decision") == "deny")
    _assert("Reason provided", "destructive" in res2.get("reason", "").lower())

    # 3. Deny Remove-Item -Recurse -Force
    print("\n[3] Deny Remove-Item -Recurse -Force")
    res3 = run_gate(json.dumps({"toolCall": {"tool": "run_command", "args": {"CommandLine": "Remove-Item C:\\ -Recurse -Force"}}}))
    _assert("Remove-Item is denied", res3.get("decision") == "deny")

    # 4. Deny format command
    print("\n[4] Deny format command")
    res4 = run_gate(json.dumps({"toolCall": {"tool": "run_command", "args": {"CommandLine": "format d: /q"}}}))
    _assert("format d: is denied", res4.get("decision") == "deny")

    # 5. Deny terraform destroy
    print("\n[5] Deny terraform destroy")
    res5 = run_gate(json.dumps({"toolCall": {"tool": "run_command", "args": {"command": "terraform destroy -auto-approve"}}}))
    _assert("terraform destroy is denied", res5.get("decision") == "deny")

    # 6. Deny kubectl delete namespace
    print("\n[6] Deny kubectl delete namespace")
    res6 = run_gate(json.dumps({"toolCall": {"tool": "run_command", "args": {"CommandLine": "kubectl delete ns production"}}}))
    _assert("kubectl delete ns is denied", res6.get("decision") == "deny")

    # 7. Deny drop database
    print("\n[7] Deny drop database")
    res7 = run_gate(json.dumps({"toolCall": {"tool": "run_command", "args": {"CommandLine": "psql -c 'DROP DATABASE production;'"}}}))
    _assert("drop database is denied", res7.get("decision") == "deny")

    # 8. Ask on malformed input
    print("\n[8] Ask on malformed unparseable input")
    res8 = run_gate("not valid json at all")
    _assert("Decision is ask on unparseable JSON", res8.get("decision") == "ask")

    # 9. Support command arg key
    print("\n[9] Support args.command fallback")
    res9 = run_gate(json.dumps({"toolCall": {"tool": "run_command", "args": {"command": "git status"}}}))
    _assert("git status via args.command is allowed", res9.get("decision") == "allow")

    print()
    if failures:
        print(f"RESULT: {len(failures)} test(s) FAILED: {failures}")
        return 1
    print("RESULT: All 9 Safety Gate tests PASSED.")
    return 0


if __name__ == "__main__":
    sys.exit(test_safety_gate())
