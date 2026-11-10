from pathlib import Path
import json, re, sys

ROOT = Path(__file__).resolve().parents[1]
errors = []
required = [
    "README.md","LICENSE","core/constitution.md","agents/principal-architect.md",
    "agents/independent-reviewer.md","skills/agent-orchestration/SKILL.md",
    "adapters/antigravity/rules/aether-engineering.md",
    "adapters/antigravity/hooks/safety_gate.py",
    "scripts/project_intel.py","scripts/security_scan.py",
    "memory/README.md","evaluation/scorecard.md"
]
for rel in required:
    if not (ROOT/rel).exists():
        errors.append(f"Missing required file: {rel}")
for p in (ROOT/"agents").glob("*.md"):
    text = p.read_text(encoding="utf-8")
    if not text.startswith("---\n") or "\nsubagent: true\n" not in text:
        errors.append(f"Invalid custom agent frontmatter: {p.name}")
for p in (ROOT/"skills").glob("*/SKILL.md"):
    text = p.read_text(encoding="utf-8")
    if not text.startswith("---\n") or f"name: {p.parent.name}" not in text:
        errors.append(f"Invalid skill frontmatter: {p}")
try:
    json.loads((ROOT/"adapters/antigravity/hooks/hooks.template.json").read_text(encoding="utf-8"))
except Exception as e:
    errors.append(f"Invalid hooks JSON: {e}")
if errors:
    print("SELF TEST FAILED")
    print("\n".join(errors))
    sys.exit(1)
print("SELF TEST PASSED")
print(f"Agents: {len(list((ROOT/'agents').glob('*.md')))}")
print(f"Skills: {len(list((ROOT/'skills').glob('*/SKILL.md')))}")
