# Google Antigravity Host Capability Matrix

**Version:** 1.1.0  
**Status:** Canonical Host Integration Reference  
**Platform Target:** Google Antigravity (AGY) 2.0+ on Windows / macOS / Linux  

---

## 1. Antigravity Architecture Overview

Antigravity operates with a dual customization discovery model:
1. **Global Configuration:** Discovered in `~/.gemini/config/` (Windows: `%USERPROFILE%\.gemini\config`).
2. **Workspace Configuration:** Discovered in `.agents/` within the active project directory.
3. **Plugin Architecture:** Discovered as packaged plugins containing `plugin.json`, `agents/`, `skills/`, and `rules/`.

---

## 2. Capability Matrix

| Feature / Subsystem | Support Classification | Antigravity Mechanism | Runtime Verification Notes |
|---|---|---|---|
| **Global System Rules** | **HOST-NATIVE VERIFIED** | Markdown file in `rules/*.md` with `trigger: always_on` frontmatter | Active and verified in current session context. Injected automatically into root agent instructions. |
| **Custom Subagents** | **HOST-NATIVE VERIFIED** | Markdown file in `agents/*.md` with YAML frontmatter (`subagent: true`, `tools`, `commandExecutionPolicy`) | Loaded natively into Antigravity subagent directory. Discovered via `/agents`. |
| **Agent Tool Sandboxing** | **HOST-NATIVE VERIFIED** | `commandExecutionPolicy: sandbox` in agent YAML frontmatter | Enforced natively by Antigravity runner. Terminal sandbox restricts network and external writes. |
| **Agent Skills** | **HOST-NATIVE VERIFIED** | Directory in `skills/<name>/SKILL.md` with YAML `name` and `description` | Discovered natively. Auto-loaded into agent context when relevant keywords match. |
| **PreToolUse Safety Hooks** | **HOST-NATIVE VERIFIED** | JSON configuration in `hooks.json` specifying matcher and command hook script | Intercepts tool calls before execution. Returns `allow`, `deny`, or `ask`. Tested in `test_safety_gate.py`. |
| **Plugin Packaging** | **HOST-NATIVE VERIFIED** | Directory with `plugin.json` bundle | Bundles rules, agents, skills as a single distributable unit (`adapters/antigravity/plugin`). |
| **Sequential Delegation Fallback** | **SCRIPT-BASED / PROMPT-ONLY** | Orchestrator role execution protocol | Guaranteed portable fallback when native subagent concurrency reaches quotas or is disabled. |
| **Memory Engine** | **SCRIPT-BASED** | Python standard library CLI (`scripts/memory_engine.py`) | File-based JSONL vault in `.aether/memory/`. Zero third-party dependencies. Verified by test suite. |
| **Continuous Learning** | **SCRIPT-BASED** | Python CLI (`scripts/learn.py`) with mandatory human review gate | Extracts candidate lessons, detects injection, requires human approval. |
| **Quality Verification Harness**| **SCRIPT-BASED** | Python CLI (`scripts/quality_engine.py`) | Manifest discovery + sandboxed execution evidence capture. |
| **Security Scanner** | **SCRIPT-BASED** | Python CLI (`scripts/security_scan.py`) | AST and regex scanner with path self-exclusion and credential redaction. |
| **Dynamic Context Bundling** | **SCRIPT-BASED** | Python CLI (`scripts/context_router.py`) | Selects minimal subagent/skill envelope per task. |
| **Automated Benchmarking** | **SCRIPT-BASED** | Python evaluation runner (`scripts/run_eval.py`) | Repeatable scorecards against test fixtures. |
| **Cross-Session Vector Search** | **UNSUPPORTED** | N/A | Antigravity does not provide native vector store hooks; AES deliberately avoids external vector databases in favor of lightweight ranked keyword search. |
| **Silent Constitutional Mutation**| **UNSUPPORTED (FORBIDDEN)**| N/A | Strictly prohibited by Aether security model. System rules cannot be updated without explicit user git commits. |

---

## 3. Configuration Scopes & Isolation Invariants

```
Global Scope: ~/.gemini/config/
├── rules/
│   └── aether-engineering.md        <-- Global constitution enforcement
├── agents/                          <-- 9 specialized subagents
├── skills/                          <-- 10 engineering task skills
└── hooks.json (opt-in)              <-- PreToolUse destructive command gate

Workspace Scope: <Project>/.aether/
├── memory/
│   ├── projects/<id>/               <-- Scoped project facts & decisions
│   └── sessions/                    <-- Ephemeral task handoffs & notes
└── reports/                         <-- Project intelligence and audit reports
```

- **Invariant 1:** Aether installers NEVER overwrite non-Aether agents, rules, or skills in the user's config directory.
- **Invariant 2:** Aether uninstaller removes ONLY files explicitly cataloged in `scripts/managed-files.json`.
- **Invariant 3:** Hooks remain disabled by default until explicit `-EnableHooks` opt-in is chosen and safety gates are inspected.
