# Aether Threat Model

## Assets
- User source code and project metadata.
- Credentials and secrets present in repositories.
- Local Antigravity configuration and permissions.
- Agent-generated edits and shell commands.
- Memory records and audit reports.

## Trust boundaries
- User prompt -> model.
- Repository content -> model context.
- Agent/skill/rule files -> runtime configuration.
- Hook scripts -> local command execution.
- MCP/plugin dependencies -> external systems.
- Local scanner output -> Git repository.

## Threats
- Prompt injection embedded in source/docs/issues.
- Malicious or over-permissioned agent/skill/plugin/hook.
- Secret leakage through logs, reports, or commits.
- Destructive command execution.
- Cross-project memory contamination.
- False-positive/false-negative scanner results.
- Unverified delegated-agent claims.

## Mitigations
- Inspect all executable configuration before enabling.
- Least-privilege tool allowlists and native sandbox/permission controls.
- Hooks disabled by default; narrow deny rules only.
- Never print secret values.
- Memory source/confidence/status metadata and explicit review.
- One writer per overlapping scope; independent review.
- Generated reports outside source repo by default.
- Human approval for irreversible operations.

## Residual risk
No prompt, rule, scanner, or hook can guarantee safety. Use OS permissions, backups, branch protection, CI, sandboxing, and human review.
