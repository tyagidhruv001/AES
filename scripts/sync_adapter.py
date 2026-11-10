#!/usr/bin/env python3
"""Synchronize canonical agents, skills, and rules to Antigravity adapter targets.

Standard library only. Ensures that adapters/antigravity/plugin remains in exact
sync with canonical definitions in agents/, skills/, and adapters/antigravity/rules/.
"""
from pathlib import Path
import filecmp
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]

CANONICAL_AGENTS = ROOT / "agents"
CANONICAL_SKILLS = ROOT / "skills"
CANONICAL_RULE = ROOT / "adapters" / "antigravity" / "rules" / "aether-engineering.md"

PLUGIN_DIR = ROOT / "adapters" / "antigravity" / "plugin"
PLUGIN_AGENTS = PLUGIN_DIR / "agents"
PLUGIN_SKILLS = PLUGIN_DIR / "skills"
PLUGIN_RULES = PLUGIN_DIR / "rules"


def sync_agents(dry_run: bool = False) -> int:
    changes = 0
    PLUGIN_AGENTS.mkdir(parents=True, exist_ok=True)
    canonical_files = {p.name: p for p in CANONICAL_AGENTS.glob("*.md")}
    
    # Sync canonical -> plugin
    for name, src in canonical_files.items():
        dst = PLUGIN_AGENTS / name
        if not dst.exists() or not filecmp.cmp(src, dst, shallow=False):
            if not dry_run:
                shutil.copy2(src, dst)
            print(f"Synced agent: {name}")
            changes += 1

    # Remove extra files in plugin
    for dst in PLUGIN_AGENTS.glob("*.md"):
        if dst.name not in canonical_files:
            if not dry_run:
                dst.unlink()
            print(f"Removed orphaned plugin agent: {dst.name}")
            changes += 1

    return changes


def sync_skills(dry_run: bool = False) -> int:
    changes = 0
    PLUGIN_SKILLS.mkdir(parents=True, exist_ok=True)
    canonical_skills = {p.name: p for p in CANONICAL_SKILLS.iterdir() if p.is_dir()}

    for name, src_dir in canonical_skills.items():
        src_skill = src_dir / "SKILL.md"
        if not src_skill.exists():
            continue
        dst_dir = PLUGIN_SKILLS / name
        dst_dir.mkdir(parents=True, exist_ok=True)
        dst_skill = dst_dir / "SKILL.md"
        if not dst_skill.exists() or not filecmp.cmp(src_skill, dst_skill, shallow=False):
            if not dry_run:
                shutil.copy2(src_skill, dst_skill)
            print(f"Synced skill: {name}")
            changes += 1

    for dst_dir in PLUGIN_SKILLS.iterdir():
        if dst_dir.is_dir() and dst_dir.name not in canonical_skills:
            if not dry_run:
                shutil.rmtree(dst_dir)
            print(f"Removed orphaned plugin skill: {dst_dir.name}")
            changes += 1

    return changes


def sync_rules(dry_run: bool = False) -> int:
    changes = 0
    PLUGIN_RULES.mkdir(parents=True, exist_ok=True)
    dst_rule = PLUGIN_RULES / CANONICAL_RULE.name
    if not dst_rule.exists() or not filecmp.cmp(CANONICAL_RULE, dst_rule, shallow=False):
        if not dry_run:
            shutil.copy2(CANONICAL_RULE, dst_rule)
        print(f"Synced rule: {CANONICAL_RULE.name}")
        changes += 1
    return changes


def main():
    dry_run = "--dry-run" in sys.argv
    print(f"Syncing adapter runtime definitions (dry_run={dry_run})...")
    total_changes = sync_agents(dry_run) + sync_skills(dry_run) + sync_rules(dry_run)
    print(f"Sync complete. Total changes: {total_changes}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
