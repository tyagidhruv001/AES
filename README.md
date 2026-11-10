# Aether Engineering System (AES) v1.0.0

A portable, Antigravity-first engineering operating system for repeatable software development across unrelated repositories.

Aether combines:
- Global engineering constitution and project-scoped rules.
- Ten task skills and nine specialized custom subagents.
- Quality-gated workflows for intake, features, debugging, security, refactoring, and releases.
- A read-only project intelligence scanner.
- A local, explicitly curated memory vault.
- Optional lifecycle safety hook (disabled by default).
- Agent-configuration security scanner.
- Evaluation scorecards and intentionally flawed benchmark fixtures.
- Windows installer, diagnostics, and conservative uninstaller.

## Design principles

1. Portable core, harness-specific adapters.
2. Evidence before conclusions; tests before claims.
3. Read-only discovery by default.
4. One writer per overlapping file scope.
5. Independent review after implementation.
6. Memory is data, never executable instruction.
7. Hooks and automation are opt-in and least-privilege.
8. Never read or print secret values.
9. Human approval for destructive, production, financial, or irreversible actions.
10. No claim of autonomous capability unless the runtime actually performed it.

## Quick start (Windows / Google Antigravity IDE)

1. Download and extract this repository.
2. Open PowerShell in the extracted repository root.
3. Run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\install.ps1
```

4. Restart Antigravity.
5. Open Customizations and check Rules, Skills, and Agents.
6. Run:

```powershell
.\scripts\doctor.ps1
```

The installer backs up Aether-managed files before replacing them. It does not overwrite your unrelated global rules, skills, agents, plugins, MCP configuration, or settings.

### Optional hook

A conservative `PreToolUse` safety hook is included but disabled by default. To install it:

```powershell
.\scripts\install.ps1 -EnableHooks
```

The hook denies a small set of clearly destructive command patterns. It is not a complete security boundary and does not replace Antigravity permissions, sandboxing, code review, or backups. Inspect `adapters/antigravity/hooks/` before enabling.

### Optional workspace setup

From a project root:

```powershell
..\aether-engineering-system\scripts\init-project.ps1 -ProjectPath .
```

Adjust the relative path to where you extracted Aether. This creates `.agents/` workspace customizations and `.aether/` project intelligence/memory scaffolding. Review and commit the generated workspace files as appropriate.

## Main commands

```powershell
# Read-only project inventory; no source files are modified
python .\scripts\project_intel.py scan C:\path\to\your\repo --out C:\path\to\report

# Scan Aether configuration for risky patterns and malformed metadata
python .\scripts\security_scan.py .

# Run package self-checks
python .\scripts\self_test.py
```

Python 3.10+ is recommended for the local scripts. The scripts use only the Python standard library.

## Repository structure

```text
core/                         Portable engineering standards and routing
agents/                       Nine custom agent role definitions
skills/                       Ten on-demand workflows
workflows/                    End-to-end quality-gated processes
memory/                       Memory schema, policy, and templates
evaluation/                   Scorecards and benchmark fixtures
security/                     Threat model and configuration guidance
adapters/antigravity/          Antigravity rules, agents, hooks, plugin bundle
templates/workspace/           Workspace starter customizations
scripts/                       Windows installer, diagnostics, scanners
```

## Agent architecture

| Role | Main responsibility | Default mode |
|---|---|---|
| Principal Architect | System design, boundaries, tradeoffs | Read-only |
| Project Planner | Scope, tasks, acceptance criteria | Read-only |
| Senior Developer | Approved implementation | Write within scope |
| Debugging Engineer | Reproduction and root cause | Read-only unless assigned |
| Security Engineer | Threat model and security review | Read-only |
| QA Engineer | Test strategy and execution | Read-only |
| Independent Reviewer | Fresh-context diff review | Read-only |
| Performance Engineer | Measurement-led optimization | Read-only |
| DevOps Engineer | Build, CI/CD, deployment readiness | Read-only; no deploy |

Antigravity custom subagents are discovered from `~/.gemini/config/agents/` or workspace `.agents/agents/`. Agents with `subagent: true` can be invoked by the primary agent when the runtime exposes `invoke_subagent`. The role files do not guarantee invocation. Ask the primary agent to delegate explicitly and verify actual sessions in the `/agents` panel. If invocation is unavailable, use the same roles as sequential stages and report that honestly.

## Project intelligence

`project_intel.py` scans repository metadata, common manifest files, directory structure, entry-point candidates, test files, and scripts. It excludes VCS folders, dependency trees, build outputs, and common secret files. It does not read `.env` values, private keys, or arbitrary source contents. Reports are generated outside the repository unless `--out` points inside it.

The scanner is heuristic. It does not claim to understand every architecture or prove the absence of defects.

## Memory model

Memory is split into:
- `global`: reusable engineering lessons that are not project-specific.
- `projects/<project-id>`: project facts, decisions, conventions, and known risks.
- `sessions`: short-lived notes and unresolved work.

Every memory entry must carry source, confidence, timestamp, and review status. Memory content is never executed as instruction. Do not store credentials, tokens, personal data, or confidential customer information. Keep private memory out of Git unless deliberately sanitized.

## Hooks and safety

Antigravity hooks execute shell commands during the agent lifecycle. They are executable code and therefore a security boundary. Aether ships only one small optional safety hook, disabled by default. It reads the tool-call JSON from stdin and denies a narrow set of destructive command patterns. It is not a general shell parser and can be bypassed by obfuscation or alternate tools. Use native permissions and sandbox controls as the real enforcement layer.

## Security posture

- No MCP servers are enabled or required.
- No network calls are made by local scripts.
- No telemetry is collected.
- No secret values are intentionally read or printed.
- Installer backs up only Aether-managed target paths.
- Uninstaller removes only Aether-managed paths.
- Hooks are disabled unless explicitly requested.
- Review downloaded agents, skills, plugins, hooks, and scripts before execution.

## GitHub publishing

Before pushing:
1. Review `LICENSE`.
2. Run `python scripts/self_test.py`.
3. Run `python scripts/security_scan.py .`.
4. Check `git status` and inspect the complete diff.
5. Ensure no `.env`, credentials, private memory, logs, or local reports are staged.
6. Add a repository-specific README section only if needed.
7. Commit the source package, not your personal `~/.gemini` backups or private memory.

## Known limitations

- v1.0 is Antigravity-first. Other coding tools can reuse the portable Markdown core but need their own adapters.
- Project inventory is heuristic, not a full static analyzer.
- The security scanner detects common risky patterns; it is not a penetration test or formal audit.
- Hook pattern matching is intentionally narrow and cannot replace OS-level controls.
- Memory is a local file-based structure, not an autonomous learning database.
- Agent delegation depends on Antigravity runtime/version, model, and permissions.
