# Google Antigravity Adapter

Antigravity discovers global customizations in `~/.gemini/config/` and workspace customizations in `.agents/`.

- Rules: `rules/*.md` with valid YAML `trigger`.
- Skills: `skills/<name>/SKILL.md`.
- Custom agents: `agents/<name>.md` with YAML frontmatter and `subagent: true`.
- Hooks: `hooks.json`.

The root installer copies the global rule, agents, and skills to the global configuration directory. It does not install hooks unless `-EnableHooks` is passed. Existing hooks are backed up but never merged automatically.

After restart, inspect Customizations. Use `/agents` to inspect active subagents. A discovered agent definition does not prove it has been invoked.
