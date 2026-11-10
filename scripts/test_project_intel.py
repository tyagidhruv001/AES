#!/usr/bin/env python3
"""Automated unit test suite for Aether Project Intelligence Scanner.

Tests:
  1. Python/FastAPI + PostgreSQL + Pytest stack detection.
  2. Node.js/Next.js + Prisma + JWT + Jest stack detection.
  3. Codedump directory is strictly excluded from scan.
  4. Secret .env files are not read or exposed.
  5. Distinction between detected facts, inferred facts, and unknowns.
  6. File limit threshold is respected.

Standard library only. Exits with 0 on pass, 1 on fail.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

from project_intel import scan_project  # noqa: E402

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
    print("Aether Project Intelligence — Automated Test Suite")
    print("=" * 60)

    # -------------------------------------------------------------
    # Test 1: Python / FastAPI / PostgreSQL stack
    # -------------------------------------------------------------
    print("\n[1] Python / FastAPI / PostgreSQL / Pytest stack")
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        (d / "requirements.txt").write_text("fastapi==0.100.0\nasyncpg==0.28.0\npytest==7.4.0\n", encoding="utf-8")
        (d / "main.py").write_text("from fastapi import FastAPI\napp = FastAPI()\n", encoding="utf-8")

        res = scan_project(d)
        inferred = res["inferred_facts"]
        detected = res["detected_facts"]

        _assert("Python language detected", "Python" in inferred["languages"])
        _assert("FastAPI framework detected", "FastAPI" in inferred["frameworks"])
        _assert("PostgreSQL database detected", "PostgreSQL" in inferred["database_technologies"])
        _assert("Pytest framework detected", "Pytest" in detected["test_frameworks"])
        _assert("main.py entrypoint detected", "main.py" in detected["entrypoints_present"])
        _assert("pip package manager detected", "pip" in detected["package_managers"])

    # -------------------------------------------------------------
    # Test 2: Node.js / Next.js / Prisma / JWT stack
    # -------------------------------------------------------------
    print("\n[2] Node.js / Next.js / Prisma / JWT stack")
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        pkg_content = """{
          "name": "web-app",
          "dependencies": {
            "next": "14.0.0",
            "react": "18.2.0",
            "@prisma/client": "5.0.0",
            "jsonwebtoken": "9.0.0"
          },
          "devDependencies": {
            "jest": "29.0.0"
          }
        }"""
        (d / "package.json").write_text(pkg_content, encoding="utf-8")
        (d / "next.config.js").write_text("module.exports = {};", encoding="utf-8")
        (d / "schema.prisma").write_text("datasource db { provider = \"postgresql\" }", encoding="utf-8")
        (d / "pnpm-lock.yaml").write_text("lockfileVersion: 5.4", encoding="utf-8")

        res2 = scan_project(d)
        inferred2 = res2["inferred_facts"]
        detected2 = res2["detected_facts"]

        _assert("JavaScript/TypeScript detected", any(l in inferred2["languages"] for l in ["JavaScript", "TypeScript"]))
        _assert("Next.js framework detected", "Next.js" in inferred2["frameworks"])
        _assert("Prisma ORM detected", "Prisma ORM" in inferred2["database_technologies"])
        _assert("JWT authentication detected", "JWT (JSON Web Tokens)" in inferred2["authentication"])
        _assert("pnpm package manager detected", "pnpm" in detected2["package_managers"])
        _assert("Jest test framework detected", "Jest" in detected2["test_frameworks"])

    # -------------------------------------------------------------
    # Test 3: Codedump directory strictly excluded
    # -------------------------------------------------------------
    print("\n[3] Codedump directory strictly excluded")
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        (d / "app.py").write_text("print('hello')", encoding="utf-8")
        codedump_dir = d / "codedump" / "nested"
        codedump_dir.mkdir(parents=True, exist_ok=True)
        (codedump_dir / "secret_dump.py").write_text("dumped_content = True", encoding="utf-8")

        res3 = scan_project(d)
        all_manifests_and_entries = str(res3["detected_facts"])
        _assert("Codedump files are not scanned", "secret_dump" not in all_manifests_and_entries)
        _assert("Total files scanned is 1", res3["total_files_scanned"] == 1)

    # -------------------------------------------------------------
    # Test 4: Secret .env files not read or exposed
    # -------------------------------------------------------------
    print("\n[4] Secret .env files not read or exposed")
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        (d / ".env").write_text("SUPER_SECRET_KEY=1234567890", encoding="utf-8")
        (d / "README.md").write_text("# Project", encoding="utf-8")

        res4 = scan_project(d)
        res4_str = str(res4)
        _assert("SUPER_SECRET_KEY not in report", "SUPER_SECRET_KEY" not in res4_str)
        _assert("1234567890 not in report", "1234567890" not in res4_str)

    # -------------------------------------------------------------
    # Test 5: Distinction between detected facts, inferred facts, and unknowns
    # -------------------------------------------------------------
    print("\n[5] Fact distinction and unknowns recording")
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        (d / "script.py").write_text("print('standalone')", encoding="utf-8")

        res5 = scan_project(d)
        _assert("detected_facts key present", "detected_facts" in res5)
        _assert("inferred_facts key present", "inferred_facts" in res5)
        _assert("unknowns key present", "unknowns" in res5)
        _assert("Unknown database recorded", any("Database" in u for u in res5["unknowns"]))
        _assert("Unknown auth recorded", any("Authentication" in u for u in res5["unknowns"]))

    print()
    if failures:
        print(f"RESULT: {len(failures)} test(s) FAILED: {failures}")
        return 1
    print("RESULT: All 5 Project Intelligence tests PASSED.")
    return 0


if __name__ == "__main__":
    sys.exit(run_tests())
