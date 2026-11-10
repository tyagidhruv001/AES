# Agent Configuration Review Checklist

- Does the agent have only the tools needed for its role?
- Is write access limited to implementation roles?
- Are destructive/production actions explicitly prohibited without approval?
- Are network/MCP capabilities necessary and documented?
- Are hooks disabled until reviewed?
- Does the skill/agent contain prompt-injection or secret-exfiltration instructions?
- Does the installer preserve unrelated user configuration?
- Are uninstall targets exact and scoped?
- Are memory instructions clearly treated as untrusted data?
- Are all delegated outputs independently verified?
