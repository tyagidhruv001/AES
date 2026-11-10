# Aether Task Router

| Request shape | Route |
|---|---|
| Unfamiliar repository / broad audit | Project Intake -> Architect + Security + QA -> Planner |
| Feature request | Planner -> Architect if cross-cutting -> Developer -> QA -> Security if sensitive -> Independent Reviewer |
| Bug / runtime failure | Debugger -> Developer if approved -> QA regression -> Reviewer |
| Security concern | Security Engineer -> Architect -> approved remediation -> QA -> Reviewer |
| Slow system | Performance Engineer -> Planner -> Developer -> benchmark -> Reviewer |
| Release / deployment | DevOps -> QA -> Security -> Reviewer -> human release approval |

## Routing rules
- Do not invoke every agent for every trivial request.
- Choose only roles that materially reduce risk.
- Start with read-only parallel analysis.
- Use one implementation owner.
- Run a fresh-context review after meaningful changes.
- If subagent invocation is unavailable, execute sequential role stages and disclose the fallback.
