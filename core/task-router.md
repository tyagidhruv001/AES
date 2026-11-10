# Aether Task Router & Context Selection Engine

Provides deterministic task classification, role routing, and minimal context bundling across Aether subagents.

---

## 1. Complexity Classification

| Complexity | Criteria | Protocol |
|---|---|---|
| **Trivial** | Single-line fix, typo, simple documentation edit, minor config tweak | Direct developer execution. Skip multi-agent ceremony. Execute test & self-audit diff. |
| **Standard** | Scoped feature, clear bug with known reproduction, isolated refactoring | Standard pipeline (Developer -> QA / Regression -> Independent Reviewer). |
| **Complex** | Architectural change, cross-cutting feature, performance regression, security vulnerability | Full pipeline (Planner / Architect -> Developer -> QA -> Reviewer). |

---

## 2. Request Routing Matrix

| Request Shape | Primary Workflow | Agent & Skill Pipeline |
|---|---|---|
| **Unfamiliar repository / broad audit** | `workflows/new-project.md` | `skills/project-intake` -> `principal-architect` + `security-engineer` + `qa-engineer` (parallel read-only) -> `project-planner` |
| **Feature request (scoped)** | `workflows/feature-delivery.md` | `project-planner` -> `senior-developer` -> `qa-engineer` -> `independent-reviewer` |
| **Feature request (architectural/cross-cutting)**| `workflows/feature-delivery.md` | `project-planner` + `principal-architect` -> `senior-developer` -> `qa-engineer` -> `security-engineer` -> `independent-reviewer` |
| **Bug / incident / runtime failure** | `workflows/incident-debugging.md` | `debugging-engineer` (reproduce & root cause) -> `senior-developer` (minimal surgical fix) -> `qa-engineer` (regression test) -> `independent-reviewer` |
| **Security audit / vulnerability triage** | `workflows/security-review.md` | `security-engineer` (threat model & scan) -> `principal-architect` -> `senior-developer` (remediation) -> `qa-engineer` -> `independent-reviewer` |
| **Performance bottleneck / slow system** | `skills/architecture-review` | `performance-engineer` (baseline measurement & bottleneck identification) -> `senior-developer` -> `performance-engineer` (benchmark verification) -> `independent-reviewer` |
| **Refactoring / technical debt** | `workflows/refactoring.md` | `principal-architect` (contract map) -> `senior-developer` (step-by-step equivalence) -> `qa-engineer` -> `independent-reviewer` |
| **UI / UX improvement** | `skills/ui-ux-review` | `skills/ui-ux-review` -> `senior-developer` -> `independent-reviewer` |
| **Release / deployment readiness** | `workflows/release-readiness.md` | `devops-engineer` -> `qa-engineer` -> `security-engineer` -> `independent-reviewer` -> Human authorization |

---

## 3. Core Routing Rules

1. **Simplicity First — No Ceremonial Overkill:**
   - Never invoke every agent for a trivial or single-file request.
   - For trivial edits (typos, single constant change), proceed directly to surgical implementation with automated test verification.

2. **Think Before Coding — Read-Only Parallel Discovery:**
   - Begin complex tasks with bounded, read-only analysis.
   - Run intake, architecture review, and security audit in parallel without granting write tools.

3. **Surgical Changes — Single-Writer Principle:**
   - Only ONE subagent (`senior-developer`) is granted file-write capabilities (`write_to_file`, `replace_file_content`).
   - Never assign multiple concurrent writers to the same codebase or overlapping file sets.

4. **Goal-Driven Handoffs:**
   - Every delegation between agents must transmit an explicit task envelope: Objective, Scope, Constraints, Invariants, and Deliverable format.

5. **Independent Review in Fresh Context:**
   - Code reviews must be performed by `independent-reviewer` inspecting the raw diff in a separate context, never rubber-stamping the author's summary.

6. **Transparent Sequential Fallback:**
   - If native subagent delegation (`invoke_subagent`) is unsupported or unavailable in the host runtime, execute the required role stages sequentially and explicitly disclose the fallback mode in the task report.
