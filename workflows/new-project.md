# New Project Intake Workflow

A read-only discovery workflow for analyzing unfamiliar codebases, mapping architecture, cataloging dependencies, identifying security postures, and establishing project memory.

---

## 1. Automated Project Intelligence Discovery
1. **Execute Project Intelligence Scanner:**
   - Scan repository structure, manifests, entrypoints, and tech stacks (excluding `codedump/` and caches):
     ```bash
     python scripts/project_intel.py scan . --out .aether/reports/project_intel.json
     ```
2. **Review Discovered Facts:**
   - Inspect detected languages, package managers, test frameworks, databases, and detected vs inferred facts.

---

## 2. Security Baseline & Threat Modeling
3. **Run Initial Security Audit:**
   - Audit repository for exposed secrets, unsafe permissions, and prompt injection payloads:
     ```bash
     python scripts/security_scan.py .
     ```
4. **Map Trust Boundaries (`security-engineer`):**
   - Identify external input vectors, authentication schemes, public endpoints, and cloud resource bindings.

---

## 3. Architecture & Contract Mapping
5. **Component & Data Flow Mapping (`principal-architect`):**
   - Map module dependencies, interface contracts, and storage integrations.
   - Catalog existing technical debt, circular dependencies, and single points of failure.
6. **Test Strategy Inventory (`qa-engineer`):**
   - Discover native test runners using Quality Engine:
     ```bash
     python scripts/quality_engine.py discover .
     ```
   - Identify gaps in unit, integration, and end-to-end test coverage.

---

## 4. Workspace Memory & Agent Bootstrapping
7. **Initialize Workspace Memory:**
   - Store baseline architecture decisions and stack conventions into project memory:
     ```bash
     python scripts/memory_engine.py add "Primary Architecture & Stack" "<stack summary>" --category project_knowledge --project default
     ```
8. **Populate `AGENTS.md` Workspace Context:**
   - Document stack invariants, build/test commands, and architectural constraints in `AGENTS.md`.

---

## 5. Milestone Planning
9. **Formulate Initial Roadmap (`project-planner`):**
   - Synthesize intake findings into prioritized milestones, ordered tasks, and binary acceptance criteria.
   - Resolve all blocking unknowns before authorizing code modifications.
