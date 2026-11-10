# Aether Definition of Done

A task or change within the Aether Engineering System is complete if and only if all following criteria are satisfied and evidenced:

---

## Mandatory Exit Checklist

1. **Acceptance Criteria Verified:**
   - Every goal and acceptance criterion defined in the initial plan has been directly verified with observable evidence, or explicitly waived with documented justification.

2. **Think Before Coding Evidenced:**
   - Relevant architecture, call sites, and contracts were inspected prior to modifications; all assumptions were documented.

3. **Simplicity First Respected:**
   - The implementation represents the minimal complete solution. No speculative features, dead abstractions, or unjustified dependencies were introduced.

4. **Surgical Diff Audited:**
   - The final diff touches only necessary files within the approved scope.
   - No unrelated refactoring, unnecessary reformatting, or extraneous edits are included.
   - Diff size is within targeted bounds (<= 200 lines preferred, explicit justification provided if > 400 lines).

5. **Automated Tests Added / Updated:**
   - Unit, integration, or regression tests were created or updated to protect modified behavior against regressions.

6. **Checks Actually Executed:**
   - Test suites, linters, or build commands were executed in the environment.
   - Exact commands, exit codes, and test outcomes are reported verbatim.
   - No skipped or failed check is marked as passed.

7. **Security & Threat Boundaries Reviewed:**
   - Input validation, authorization, data privacy, and secret exposure risks were audited.
   - No secret values or sensitive tokens appear in diffs, logs, or reports.

8. **Independent Review Completed:**
   - An independent review (fresh-context subagent or rigorous self-audit protocol) inspected the raw diff and verified correctness and contract stability.
   - All high and medium severity findings are resolved or explicitly accepted.

9. **Honest Completion Envelope Delivered:**
   - Final completion report documents:
     - Exact list of files created, modified, or removed.
     - Exact test commands executed and results observed.
     - Known limitations, unverified edge cases, and remaining risks.
