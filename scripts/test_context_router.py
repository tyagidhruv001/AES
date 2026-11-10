#!/usr/bin/env python3
"""Automated unit test suite for Aether Context Router & Optimizer.

Tests:
  1. Classification of Simple Coding tasks.
  2. Classification of Bug Fix / Incident tasks.
  3. Classification of Security Audit tasks.
  4. Classification of Architecture Refactoring tasks.
  5. Classification of Complex Feature tasks.
  6. Classification of UI/UX tasks.
  7. Classification of Research tasks.
  8. Context token efficiency calculation (>= 50% reduction).

Standard library only. Exits with 0 on pass, 1 on fail.
"""
from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

from context_router import build_context_envelope, classify_task  # noqa: E402

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
    print("Aether Context Router — Automated Test Suite")
    print("=" * 60)

    # 1. Simple coding task
    print("\n[1] Simple coding task classification")
    c1 = classify_task("Fix typo in README.md")
    _assert("Classified as SIMPLE_CODING", c1 == "SIMPLE_CODING", f"Got: {c1}")

    # 2. Bug fix task
    print("\n[2] Bug fix task classification")
    c2 = classify_task("Application crashes with NullPointerException in UserService on login")
    _assert("Classified as BUG_FIX", c2 == "BUG_FIX", f"Got: {c2}")

    # 3. Security task
    print("\n[3] Security vulnerability classification")
    c3 = classify_task("Audit token verification for potential JWT signature bypass and XSS vulnerabilities")
    _assert("Classified as SECURITY", c3 == "SECURITY", f"Got: {c3}")

    # 4. Architecture refactoring task
    print("\n[4] Architecture refactoring classification")
    c4 = classify_task("Decouple user service and payment system boundaries to reduce circular dependencies")
    _assert("Classified as ARCHITECTURE", c4 == "ARCHITECTURE", f"Got: {c4}")

    # 5. Complex feature task
    print("\n[5] Complex feature classification")
    c5 = classify_task("Implement a new billing subscription pipeline with Stripe webhooks and customer portal")
    _assert("Classified as COMPLEX_FEATURE", c5 == "COMPLEX_FEATURE", f"Got: {c5}")

    # 6. UI/UX task
    print("\n[6] UI/UX task classification")
    c6 = classify_task("Improve responsive layout, contrast ratios, and modal accessibility for mobile screens")
    _assert("Classified as UI_UX", c6 == "UI_UX", f"Got: {c6}")

    # 7. Research task
    print("\n[7] Research task classification")
    c7 = classify_task("Investigate and evaluate library options for distributed tracing in Go")
    _assert("Classified as RESEARCH", c7 == "RESEARCH", f"Got: {c7}")

    # 8. Token efficiency reduction
    print("\n[8] Context token efficiency envelope")
    env = build_context_envelope("Fix typo in header")
    pct_str = env["context_efficiency"]["estimated_token_reduction"]
    pct = float(pct_str.replace("%", ""))
    _assert("Token reduction is >= 70% for simple tasks", pct >= 70.0, f"Got: {pct}%")
    _assert("Targeted agent is senior-developer only", env["selected_agents"] == ["senior-developer"])

    print()
    if failures:
        print(f"RESULT: {len(failures)} test(s) FAILED: {failures}")
        return 1
    print("RESULT: All 8 Context Router tests PASSED.")
    return 0


if __name__ == "__main__":
    sys.exit(run_tests())

