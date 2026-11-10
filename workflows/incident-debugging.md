# Incident Debugging & Bug-Fix Workflow

A disciplined, evidence-based procedure for reproducing software failures, isolating root causes, creating regression tests, and applying minimal surgical fixes.

---

## 1. Triage & Symptom Capture
1. **Capture Failure Artifacts:**
   - Record observed vs expected behavior, sanitized stack traces, timestamps, and environment details.
2. **Context Routing:**
   - Execute router to initialize the debugging pipeline:
     ```bash
     python scripts/context_router.py "Bug: <symptom description>"
     ```
3. **Query Memory Vault:**
   - Check if this failure or related component has documented known issues:
     ```bash
     python scripts/memory_engine.py search "<error keywords>" --category known_issues
     ```

---

## 2. Reproduction & Root Cause Analysis
4. **Controlled Reproduction (`debugging-engineer`):**
   - Reproduce the failure safely in the sandbox environment.
   - Strip away external noise to construct a minimal reproduction script or test case.
   - **Hard Rule:** No production resets, data deletion, or configuration mutations without explicit human approval.
5. **Trace & Hypothesize:**
   - Formulate ranked hypotheses based on source inspection.
   - Trace execution backwards from the failure point to input origins.
   - Isolate the definitive root cause citing exact file paths and line numbers.

---

## 3. Regression Protection & Surgical Fix
6. **Write Failing Regression Test (`debugging-engineer` / `qa-engineer`):**
   - Write an automated test case that fails against the unpatched codebase, deterministically capturing the bug.
7. **Minimal Root-Cause Patch (`senior-developer`):**
   - Implement the smallest complete code change addressing the root cause (not masking symptoms).
   - Verify the regression test transitions from RED to GREEN.
   - Run adjacent existing test suites to prevent unintended collateral breakage:
     ```bash
     python scripts/quality_engine.py run "<test command>"
     ```

---

## 4. Quality Gate & Independent Review
8. **Diff Audit & Peer Review (`independent-reviewer`):**
   - Inspect the raw unified diff in fresh context.
   - Verify that no tangential refactoring was performed and the diff is minimal.
9. **Security Audit:**
   - Run `python scripts/security_scan.py .` to ensure no accidental credential exposure or permission overrides.

---

## 5. Post-Mortem & Continuous Learning
10. **Record Debugging Lesson:**
    - Propose the root-cause finding as a reusable debugging pattern:
      ```bash
      python scripts/learn.py propose "<Bug Title>" "<Root cause & fix explanation>" --category known_issues --evidence "<failing test path>"
      ```
11. **Incident Resolution Report:**
    - Deliver root cause narrative, reproduction evidence, fix diff summary, and verification logs.
