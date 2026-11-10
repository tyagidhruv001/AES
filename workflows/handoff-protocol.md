# Agent Handoff Protocol
Every delegated brief must include goal, scope, exclusions, read/write boundary, paths, constraints, deliverable, evidence format, and stop conditions.

Parallelize independent read-only work. Assign one writer per overlapping file set. Use isolated worktrees for parallel implementation where supported. Verify claims against source and test output. A reviewer must not be the sole author of the implementation being reviewed.

If native delegation is unavailable, run roles sequentially and state that no separate subagents were invoked.
