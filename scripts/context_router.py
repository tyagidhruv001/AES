#!/usr/bin/env python3
"""Aether Context Router & Dynamic Bundle Optimizer.

Selects the minimal necessary subset of agents and skills for a given task,
generating compact, token-efficient delegation envelopes. Standard library only.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]

# Archetype mapping
ROUTING_TABLE: Dict[str, Dict[str, Any]] = {
    "SIMPLE_CODING": {
        "description": "Direct, surgical implementation without multi-agent ceremony",
        "agents": ["senior-developer"],
        "skills": ["feature-development"],
        "workflow": "workflows/feature-delivery.md",
        "keywords": ["fix typo", "update readme", "minor change", "rename variable", "simple fix", "quick edit"],
    },
    "BUG_FIX": {
        "description": "Reproduction, root-cause isolation, and regression verification",
        "agents": ["debugging-engineer", "senior-developer", "qa-engineer", "independent-reviewer"],
        "skills": ["debugging", "testing", "code-review"],
        "workflow": "workflows/incident-debugging.md",
        "keywords": ["bug", "error", "exception", "crash", "fails", "traceback", "reproduce", "regression", "500", "broken"],
    },
    "SECURITY": {
        "description": "Threat modeling, vulnerability triage, and secure remediation",
        "agents": ["security-engineer", "principal-architect", "senior-developer", "independent-reviewer"],
        "skills": ["security-audit", "architecture-review", "code-review"],
        "workflow": "workflows/security-review.md",
        "keywords": ["security", "vulnerability", "cwe", "cve", "injection", "secret", "token", "auth", "xss", "csrf", "sqli", "sanitize"],
    },
    "ARCHITECTURE": {
        "description": "System boundaries, component data flows, and contract refactoring",
        "agents": ["principal-architect", "project-planner", "independent-reviewer"],
        "skills": ["architecture-review", "code-review"],
        "workflow": "workflows/refactoring.md",
        "keywords": ["architecture", "redesign", "decouple", "data flow", "boundary", "refactor", "migration", "modularize", "system design"],
    },
    "COMPLEX_FEATURE": {
        "description": "Multi-stage scoped feature planning, implementation, and QA",
        "agents": ["project-planner", "principal-architect", "senior-developer", "qa-engineer", "independent-reviewer"],
        "skills": ["feature-development", "testing", "code-review"],
        "workflow": "workflows/feature-delivery.md",
        "keywords": ["feature", "implement", "add support", "new endpoint", "build", "create", "enhance", "pipeline"],
    },
    "UI_UX": {
        "description": "Frontend usability, responsive states, and accessibility",
        "agents": ["senior-developer", "independent-reviewer"],
        "skills": ["ui-ux-review", "feature-development"],
        "workflow": "workflows/feature-delivery.md",
        "keywords": ["ui", "ux", "frontend", "css", "layout", "responsive", "accessibility", "aria", "contrast", "theme", "modal"],
    },
    "RESEARCH": {
        "description": "Investigating unfamiliar technologies, APIs, and libraries",
        "agents": ["principal-architect"],
        "skills": ["research-first", "project-intake"],
        "workflow": "workflows/new-project.md",
        "keywords": ["research", "investigate", "explore", "evaluate library", "documentation", "compare tools", "feasibility"],
    },
}


def classify_task(prompt: str) -> str:
    """Classify user task prompt into an optimal routing archetype."""
    prompt_lower = prompt.lower()

    # Score each archetype based on keyword frequency
    scores: Dict[str, int] = {}
    for archetype, meta in ROUTING_TABLE.items():
        score = 0
        for kw in meta["keywords"]:
            if re.search(r"\b" + re.escape(kw) + r"\b", prompt_lower):
                score += 2
            elif kw in prompt_lower:
                score += 1
        scores[archetype] = score

    # Check for simple coding tasks explicitly
    if scores.get("SIMPLE_CODING", 0) > 0 and len(prompt.split()) < 20:
        return "SIMPLE_CODING"

    best_match = max(scores, key=scores.get)
    if scores[best_match] > 0:
        return best_match

    # Default to COMPLEX_FEATURE for general coding or BUG_FIX if error-like
    return "COMPLEX_FEATURE"


def build_context_envelope(
    prompt: str,
    target_files: Optional[List[str]] = None,
    constraints: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Generate a compact, token-efficient task envelope with only necessary agents and skills."""
    archetype = classify_task(prompt)
    meta = ROUTING_TABLE[archetype]

    # Calculate token savings vs loading all 9 agents + 10 skills
    total_system_roles = 9
    total_system_skills = 10
    selected_roles = len(meta["agents"])
    selected_skills = len(meta["skills"])

    reduction_pct = round(
        (1.0 - (selected_roles + selected_skills) / (total_system_roles + total_system_skills)) * 100, 1
    )

    return {
        "archetype": archetype,
        "description": meta["description"],
        "selected_agents": meta["agents"],
        "selected_skills": meta["skills"],
        "workflow": meta["workflow"],
        "target_files": target_files or [],
        "constraints": constraints or [
            "Follow single-writer discipline (senior-developer only).",
            "Keep diff under 200 lines.",
            "Run automated tests and capture evidence.",
        ],
        "context_efficiency": {
            "agents_included": f"{selected_roles} / {total_system_roles}",
            "skills_included": f"{selected_skills} / {total_system_skills}",
            "estimated_token_reduction": f"{reduction_pct}%",
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Aether Context Router CLI")
    ap.add_argument("prompt", help="Task prompt or description")
    ap.add_argument("--files", default="", help="Comma-separated target files")
    ap.add_argument("--json", action="store_true", help="Output raw JSON")

    args = ap.parse_args()
    targets = [f.strip() for f in args.files.split(",") if f.strip()]
    envelope = build_context_envelope(args.prompt, target_files=targets)

    if args.json:
        print(json.dumps(envelope, indent=2))
    else:
        print("=" * 60)
        print(f"Task Archetype: {envelope['archetype']}")
        print(f"Description:    {envelope['description']}")
        print(f"Workflow:       {envelope['workflow']}")
        print(f"Active Agents:  {', '.join(envelope['selected_agents'])}")
        print(f"Active Skills:  {', '.join(envelope['selected_skills'])}")
        print(f"Efficiency:     {envelope['context_efficiency']['estimated_token_reduction']} token reduction")
        print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())

