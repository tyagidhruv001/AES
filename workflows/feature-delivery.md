# Feature Delivery Workflow

A structured, quality-gated engineering workflow for delivering scoped features with zero regression risk and verifiable acceptance evidence.

---

## 1. Scope & Context Initialization
1. **Analyze User Request:** Extract concrete business outcomes, non-goals, and boundary constraints.
2. **Context Routing:** Execute context router to bundle required roles and skills:
   ```bash
   python scripts/context_router.py "<feature description>"
   ```
3. **Query Memory Vault:** Check for existing architectural decisions, conventions, or known issues:
   ```bash
   python scripts/memory_engine.py search "<feature keywords>" --category architecture_decisions
   ```

---

## 2. Planning & Architectural Alignment
4. **Planning (`project-planner`):**
   - Inspect call sites, manifests, and existing module boundaries.
   - Formulate ordered task envelopes with binary acceptance criteria.
5. **Architectural Review (`principal-architect`):**
   - If the feature introduces new data models, external APIs, or cross-module boundaries, review component coupling and data flow contracts.

---

## 3. Surgical Implementation
6. **Single-Writer Implementation (`senior-developer`):**
   - Think before coding: inspect existing tests and idioms.
   - Implement the minimal complete solution (Simplicity First).
   - Touch ONLY files listed in the task scope. Target diffs under 200 lines.
   - Add comprehensive unit tests covering happy path, negative path, and boundary conditions.

---

## 4. Verification & Quality Gates
7. **Automated Verification (`qa-engineer`):**
   - Discover and run project test suites using the Quality Engine:
     ```bash
     python scripts/quality_engine.py run "npm test" # or pytest / cargo test
     ```
   - Record exact execution duration, exit code, and test counts.
8. **Security Audit (`security-engineer`):**
   - Run the security scanner across the repository:
     ```bash
     python scripts/security_scan.py .
     ```
   - Verify input validation, secret absence, and authorization controls.
9. **Diff Audit & Peer Review (`independent-reviewer`):**
   - Audit the unified diff for surgical bounds and leftover debug statements:
     ```bash
     git diff > diff.patch && python scripts/quality_engine.py audit-diff diff.patch
     ```
   - Fresh-context peer review delivering `APPROVE` or `CHANGES_REQUIRED`.

---

## 5. Continuous Learning & Completion
10. **Candidate Lesson Extraction:**
    - If a reusable project pattern or architectural decision was established, propose it for human review:
      ```bash
      python scripts/learn.py propose "<Pattern Title>" "<Lesson Content>" --category architecture_decisions --evidence "<files:lines>"
      ```
11. **Final Delivery Report:**
    - Document files modified, test commands executed, results observed, and known limitations.
