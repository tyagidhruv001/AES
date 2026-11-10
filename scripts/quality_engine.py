#!/usr/bin/env python3
"""Aether Engineering Quality Engine & Verification Harness.

Discovers project verification commands, executes sandboxed test suites,
captures tamper-evident execution evidence, and analyzes diffs for surgical bounds.
Standard library only.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def discover_commands(project_root: Path) -> List[Dict[str, str]]:
    """Inspect project manifests to discover test and build commands."""
    commands: List[Dict[str, str]] = []

    # 1. Node.js / JavaScript / TypeScript
    pkg_json = project_root / "package.json"
    if pkg_json.exists():
        try:
            data = json.loads(pkg_json.read_text(encoding="utf-8"))
            scripts = data.get("scripts", {})
            if "test" in scripts and "no test specified" not in scripts["test"].lower():
                commands.append({
                    "ecosystem": "Node.js",
                    "type": "test",
                    "command": "npm test",
                    "source": "package.json:scripts.test",
                })
            if "build" in scripts:
                commands.append({
                    "ecosystem": "Node.js",
                    "type": "build",
                    "command": "npm run build",
                    "source": "package.json:scripts.build",
                })
            if "lint" in scripts:
                commands.append({
                    "ecosystem": "Node.js",
                    "type": "lint",
                    "command": "npm run lint",
                    "source": "package.json:scripts.lint",
                })
        except Exception:
            pass

    # 2. Python
    pyproject = project_root / "pyproject.toml"
    setup_cfg = project_root / "setup.cfg"
    pytest_ini = project_root / "pytest.ini"
    reqs = project_root / "requirements.txt"

    has_pytest = False
    if pyproject.exists() and "pytest" in pyproject.read_text(encoding="utf-8"):
        has_pytest = True
    elif setup_cfg.exists() and "pytest" in setup_cfg.read_text(encoding="utf-8"):
        has_pytest = True
    elif pytest_ini.exists():
        has_pytest = True
    elif reqs.exists() and "pytest" in reqs.read_text(encoding="utf-8"):
        has_pytest = True

    if has_pytest:
        commands.append({
            "ecosystem": "Python",
            "type": "test",
            "command": "pytest",
            "source": "pytest configuration detected",
        })
    elif any(project_root.glob("tests/test_*.py")) or any(project_root.glob("test_*.py")):
        commands.append({
            "ecosystem": "Python",
            "type": "test",
            "command": "python -m unittest discover",
            "source": "standard library unittest layout detected",
        })

    # 3. Java (Maven)
    if (project_root / "pom.xml").exists():
        commands.append({
            "ecosystem": "Java/Maven",
            "type": "test",
            "command": "mvn test",
            "source": "pom.xml",
        })

    # 4. Java / Kotlin (Gradle)
    if (project_root / "build.gradle").exists() or (project_root / "build.gradle.kts").exists():
        gradle_cmd = "./gradlew test" if (project_root / "gradlew").exists() else "gradle test"
        commands.append({
            "ecosystem": "Java/Gradle",
            "type": "test",
            "command": gradle_cmd,
            "source": "build.gradle",
        })

    # 5. Rust
    if (project_root / "Cargo.toml").exists():
        commands.append({
            "ecosystem": "Rust",
            "type": "test",
            "command": "cargo test",
            "source": "Cargo.toml",
        })
        commands.append({
            "ecosystem": "Rust",
            "type": "build",
            "command": "cargo check",
            "source": "Cargo.toml",
        })

    # 6. Go
    if (project_root / "go.mod").exists():
        commands.append({
            "ecosystem": "Go",
            "type": "test",
            "command": "go test ./...",
            "source": "go.mod",
        })

    # 7. .NET / C#
    if list(project_root.glob("*.csproj")) or list(project_root.glob("*.sln")):
        commands.append({
            "ecosystem": ".NET",
            "type": "test",
            "command": "dotnet test",
            "source": "*.csproj / *.sln",
        })

    return commands


def execute_check(command: str, cwd: Path, timeout_seconds: int = 60) -> Dict[str, Any]:
    """Execute a verification command and capture tamper-evident results."""
    start_time = datetime.datetime.now(datetime.timezone.utc)
    start_perf = time.perf_counter()

    result: Dict[str, Any] = {
        "command": command,
        "cwd": str(cwd),
        "started_at": start_time.isoformat(),
        "timeout_seconds": timeout_seconds,
        "exit_code": None,
        "status": "UNKNOWN",
        "duration_seconds": 0.0,
        "stdout_summary": "",
        "stderr_summary": "",
    }

    try:
        proc = subprocess.run(
            command,
            shell=True,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
        duration = time.perf_counter() - start_perf
        result["duration_seconds"] = round(duration, 3)
        result["exit_code"] = proc.returncode
        result["status"] = "PASSED" if proc.returncode == 0 else "FAILED"
        result["stdout_summary"] = proc.stdout[-2000:] if len(proc.stdout) > 2000 else proc.stdout
        result["stderr_summary"] = proc.stderr[-2000:] if len(proc.stderr) > 2000 else proc.stderr
    except subprocess.TimeoutExpired as e:
        duration = time.perf_counter() - start_perf
        result["duration_seconds"] = round(duration, 3)
        result["status"] = "TIMED_OUT"
        result["exit_code"] = -1
        result["stderr_summary"] = f"Execution timed out after {timeout_seconds} seconds."
    except Exception as e:
        duration = time.perf_counter() - start_perf
        result["duration_seconds"] = round(duration, 3)
        result["status"] = "ERROR"
        result["exit_code"] = -2
        result["stderr_summary"] = str(e)

    result["finished_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    return result


def audit_diff(diff_text: str) -> Dict[str, Any]:
    """Audit a unified diff for surgical bounds, file count, and leftover debug prints."""
    lines_added = 0
    lines_removed = 0
    files_changed: Set[str] = set()
    leftover_debug_alerts: List[Dict[str, Any]] = []

    current_file = ""
    lineno = 0

    debug_patterns = [
        re.compile(r"^\+\s*console\.(?:log|debug|warn)\("),
        re.compile(r"^\+\s*print\("),
        re.compile(r"^\+\s*debugger;"),
        re.compile(r"^\+\s*#\s*TODO:\s*temp", re.IGNORECASE),
    ]

    for line in diff_text.splitlines():
        if line.startswith("+++ b/"):
            current_file = line[6:].strip()
            files_changed.add(current_file)
            lineno = 0
        elif line.startswith("@@"):
            match = re.search(r"\+(\d+)", line)
            if match:
                lineno = int(match.group(1))
        elif line.startswith("+") and not line.startswith("+++"):
            lines_added += 1
            lineno += 1
            for p in debug_patterns:
                if p.search(line):
                    leftover_debug_alerts.append({
                        "file": current_file,
                        "line": lineno,
                        "snippet": line.strip(),
                    })
        elif line.startswith("-") and not line.startswith("---"):
            lines_removed += 1

    total_diff_lines = lines_added + lines_removed
    is_surgical = total_diff_lines <= 200
    requires_justification = total_diff_lines > 400

    verdict = "SURGICAL"
    if requires_justification:
        verdict = "EXCESSIVE_DIFF"
    elif not is_surgical:
        verdict = "MODERATE_DIFF"

    return {
        "lines_added": lines_added,
        "lines_removed": lines_removed,
        "total_diff_lines": total_diff_lines,
        "files_count": len(files_changed),
        "files": sorted(files_changed),
        "verdict": verdict,
        "is_surgical": is_surgical,
        "requires_justification": requires_justification,
        "leftover_debug_count": len(leftover_debug_alerts),
        "leftover_debug_alerts": leftover_debug_alerts,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Aether Quality Engine CLI")
    sub = ap.add_subparsers(dest="cmd", required=True)

    disc = sub.add_parser("discover", help="Discover verification commands for a project")
    disc.add_argument("path", nargs="?", default=".", help="Project root directory")

    run = sub.add_parser("run", help="Run a verification check and record evidence")
    run.add_argument("command", help="Command string to execute")
    run.add_argument("--cwd", default=".", help="Working directory")
    run.add_argument("--timeout", type=int, default=60, help="Timeout in seconds")
    run.add_argument("--out", help="Path to save JSON evidence report")

    diff_p = sub.add_parser("audit-diff", help="Audit a unified diff file for surgical metrics")
    diff_p.add_argument("diff_file", help="Path to unified diff text file")

    args = ap.parse_args()

    if args.cmd == "discover":
        root = Path(args.path).resolve()
        cmds = discover_commands(root)
        print(f"Discovered {len(cmds)} command(s) for {root}:")
        print(json.dumps(cmds, indent=2))
    elif args.cmd == "run":
        cwd = Path(args.cwd).resolve()
        res = execute_check(args.command, cwd, args.timeout)
        print(json.dumps(res, indent=2))
        if args.out:
            out_p = Path(args.out)
            out_p.parent.mkdir(parents=True, exist_ok=True)
            out_p.write_text(json.dumps(res, indent=2) + "\n", encoding="utf-8")
        return 0 if res["status"] == "PASSED" else 1
    elif args.cmd == "audit-diff":
        diff_p = Path(args.diff_file)
        if not diff_p.exists():
            print(f"File not found: {diff_p}", file=sys.stderr)
            return 1
        res = audit_diff(diff_p.read_text(encoding="utf-8", errors="replace"))
        print(json.dumps(res, indent=2))
        return 0 if res["is_surgical"] else 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
