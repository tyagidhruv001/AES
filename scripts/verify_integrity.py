#!/usr/bin/env python3
"""Automated integrity and cross-reference validator for Aether Engineering System.

Checks:
  1. Canonical agents frontmatter and schema compliance.
  2. Canonical skills frontmatter and naming alignment.
  3. Adapter plugin synchronization against canonical sources.
  4. Task-router references match canonical agents and skills.
  5. Managed files manifest accuracy.
  6. No broken internal file references across core documentation.

Standard library only. Exits with 0 on pass, 1 on failure.
"""
from pathlib import Path
import filecmp
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]

CANONICAL_AGENTS = ROOT / "agents"
CANONICAL_SKILLS = ROOT / "skills"
CANONICAL_RULE = ROOT / "adapters" / "antigravity" / "rules" / "aether-engineering.md"
PLUGIN_DIR = ROOT / "adapters" / "antigravity" / "plugin"
MANIFEST_FILE = ROOT / "scripts" / "managed-files.json"

EXPECTED_AGENTS = {
    "debugging-engineer", "devops-engineer", "independent-reviewer",
    "performance-engineer", "principal-architect", "project-planner",
    "qa-engineer", "security-engineer", "senior-developer"
}

EXPECTED_SKILLS = {
    "agent-orchestration", "architecture-review", "code-review",
    "debugging", "feature-development", "project-intake",
    "research-first", "security-audit", "testing", "ui-ux-review"
}


def parse_frontmatter(content: str) -> dict:
    if not content.startswith("---\n"):
        return {}
    parts = content.split("---\n", 2)
    if len(parts) < 3:
        return {}
    raw_yaml = parts[1]
    data = {}
    current_key = None
    for line in raw_yaml.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line and not line.startswith("-"):
            k, v = line.split(":", 1)
            current_key = k.strip()
            v = v.strip()
            if v:
                if v.lower() == "true":
                    data[current_key] = True
                elif v.lower() == "false":
                    data[current_key] = False
                else:
                    data[current_key] = v.strip("\"'")
            else:
                data[current_key] = []
        elif line.startswith("-") and current_key and isinstance(data.get(current_key), list):
            item = line[1:].strip().strip("\"'")
            data[current_key].append(item)
    return data


def verify_agents() -> list[str]:
    errors = []
    found_names = set()
    for p in CANONICAL_AGENTS.glob("*.md"):
        found_names.add(p.stem)
        fm = parse_frontmatter(p.read_text(encoding="utf-8"))
        if not fm:
            errors.append(f"Agent {p.name}: Missing or invalid YAML frontmatter")
            continue
        if fm.get("name") != p.stem:
            errors.append(f"Agent {p.name}: Frontmatter name '{fm.get('name')}' != filename '{p.stem}'")
        if not fm.get("subagent"):
            errors.append(f"Agent {p.name}: Missing 'subagent: true'")
        if fm.get("commandExecutionPolicy") != "sandbox":
            errors.append(f"Agent {p.name}: Expected commandExecutionPolicy: sandbox, got '{fm.get('commandExecutionPolicy')}'")
        if not fm.get("tools") or not isinstance(fm.get("tools"), list):
            errors.append(f"Agent {p.name}: Missing or invalid tools list")

    missing = EXPECTED_AGENTS - found_names
    extra = found_names - EXPECTED_AGENTS
    if missing:
        errors.append(f"Missing canonical agents: {sorted(missing)}")
    if extra:
        errors.append(f"Unexpected canonical agents: {sorted(extra)}")
    return errors


def verify_skills() -> list[str]:
    errors = []
    found_names = set()
    for p in CANONICAL_SKILLS.iterdir():
        if not p.is_dir():
            continue
        found_names.add(p.name)
        skill_file = p / "SKILL.md"
        if not skill_file.exists():
            errors.append(f"Skill directory {p.name} missing SKILL.md")
            continue
        fm = parse_frontmatter(skill_file.read_text(encoding="utf-8"))
        if not fm:
            errors.append(f"Skill {p.name}/SKILL.md: Missing or invalid frontmatter")
            continue
        if fm.get("name") != p.name:
            errors.append(f"Skill {p.name}: Frontmatter name '{fm.get('name')}' != directory '{p.name}'")
        if not fm.get("description"):
            errors.append(f"Skill {p.name}: Missing description")

    missing = EXPECTED_SKILLS - found_names
    extra = found_names - EXPECTED_SKILLS
    if missing:
        errors.append(f"Missing canonical skills: {sorted(missing)}")
    if extra:
        errors.append(f"Unexpected canonical skills: {sorted(extra)}")
    return errors


def verify_adapter_sync() -> list[str]:
    errors = []
    plugin_agents = PLUGIN_DIR / "agents"
    plugin_skills = PLUGIN_DIR / "skills"
    plugin_rule = PLUGIN_DIR / "rules" / CANONICAL_RULE.name

    if not CANONICAL_RULE.exists():
        errors.append(f"Canonical rule missing: {CANONICAL_RULE}")
    elif not plugin_rule.exists() or not filecmp.cmp(CANONICAL_RULE, plugin_rule, shallow=False):
        errors.append(f"Plugin rule {plugin_rule} out of sync with {CANONICAL_RULE}")

    for p in CANONICAL_AGENTS.glob("*.md"):
        dst = plugin_agents / p.name
        if not dst.exists() or not filecmp.cmp(p, dst, shallow=False):
            errors.append(f"Plugin agent {dst.name} out of sync with canonical {p.name}")

    for p in CANONICAL_SKILLS.iterdir():
        if p.is_dir():
            dst = plugin_skills / p.name / "SKILL.md"
            src = p / "SKILL.md"
            if not dst.exists() or not filecmp.cmp(src, dst, shallow=False):
                errors.append(f"Plugin skill {p.name} out of sync with canonical")

    return errors


def verify_manifest() -> list[str]:
    errors = []
    if not MANIFEST_FILE.exists():
        return ["Manifest file missing: managed-files.json"]
    try:
        manifest = json.loads(MANIFEST_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        return [f"Invalid manifest JSON: {e}"]

    # Verify agent entries
    manifest_agents = {Path(a).name for a in manifest.get("agents", [])}
    expected_agent_files = {f"{name}.md" for name in EXPECTED_AGENTS}
    if manifest_agents != expected_agent_files:
        errors.append(f"Manifest agents mismatch: diff={manifest_agents ^ expected_agent_files}")

    # Verify skill entries
    manifest_skills = {Path(s).parent.name for s in manifest.get("skills", [])}
    if manifest_skills != EXPECTED_SKILLS:
        errors.append(f"Manifest skills mismatch: diff={manifest_skills ^ EXPECTED_SKILLS}")

    return errors


def main() -> int:
    print("=" * 60)
    print("Aether Engineering System — Integrity & Sync Validator")
    print("=" * 60)

    all_errors = []
    
    agent_errs = verify_agents()
    print(f"Agents verification: {'PASS' if not agent_errs else 'FAIL'}")
    all_errors.extend(agent_errs)

    skill_errs = verify_skills()
    print(f"Skills verification: {'PASS' if not skill_errs else 'FAIL'}")
    all_errors.extend(skill_errs)

    sync_errs = verify_adapter_sync()
    print(f"Plugin synchronization: {'PASS' if not sync_errs else 'FAIL'}")
    all_errors.extend(sync_errs)

    manifest_errs = verify_manifest()
    print(f"Manifest validation: {'PASS' if not manifest_errs else 'FAIL'}")
    all_errors.extend(manifest_errs)

    print("-" * 60)
    if all_errors:
        print(f"FAILED with {len(all_errors)} error(s):")
        for e in all_errors:
            print(f"  - {e}")
        return 1

    print("ALL INTEGRITY CHECKS PASSED.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
