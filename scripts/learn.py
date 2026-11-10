#!/usr/bin/env python3
"""Controlled Continuous Learning Engine for Aether.

Implements human-gated candidate lesson extraction, injection filtering,
duplicate detection, and promotion/rollback lifecycle. Standard library only.
"""
from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

from memory_engine import (  # noqa: E402
    CATEGORIES,
    INJECTION_PATTERN,
    MemoryEngine,
    sanitize_text,
)


class LearningPipeline:
    def __init__(self, memory_engine: Optional[MemoryEngine] = None):
        self.engine = memory_engine or MemoryEngine()

    def propose_candidate(
        self,
        title: str,
        lesson: str,
        category: str,
        evidence: str,
        project_id: str = "default",
        confidence: str = "high",
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Propose a candidate lesson. Must be explicitly approved before promotion."""
        if category not in CATEGORIES:
            raise ValueError(f"Category '{category}' must be one of {sorted(CATEGORIES)}")

        clean_title = sanitize_text(title.strip())
        clean_lesson = sanitize_text(lesson.strip())
        clean_evidence = sanitize_text(evidence.strip())

        # Adversarial check: reject prompt injections immediately
        if INJECTION_PATTERN.search(clean_title) or INJECTION_PATTERN.search(clean_lesson):
            return {
                "status": "REJECTED_IMMEDIATELY",
                "reason": "Security Alert: Candidate contains prompt-injection instruction patterns.",
                "title": clean_title,
            }

        if not clean_evidence:
            return {
                "status": "REJECTED_IMMEDIATELY",
                "reason": "Candidate rejected: Concrete supporting evidence (files, symbols, tests) is mandatory.",
                "title": clean_title,
            }

        # Store as candidate in project memory with proposed status
        entry = self.engine.add(
            title=clean_title,
            content=clean_lesson,
            category=category,
            scope="project",
            project_id=project_id,
            confidence=confidence,
            tags=tags or [],
            evidence=clean_evidence,
            trust_status="proposed",
        )
        return {
            "status": "PROPOSED",
            "id": entry["id"],
            "title": entry["title"],
            "category": entry["category"],
            "requires_human_approval": True,
        }

    def list_candidates(self, project_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all candidate lessons awaiting human approval."""
        entries = self.engine._read_all(project_id=project_id)
        return [e for e in entries if e.get("trust_status") == "proposed"]

    def approve_candidate(self, mem_id: str, reviewer: str = "human", promote_to_global: bool = False) -> Dict[str, Any]:
        """Approve a candidate lesson. Moves trust_status to 'trusted'."""
        entry = self.engine.get(mem_id)
        if not entry:
            return {"success": False, "error": f"Entry not found: {mem_id}"}

        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        updates = {
            "trust_status": "trusted",
            "reviewed_by": reviewer,
            "approved_at": now,
        }
        updated = self.engine.update(mem_id, updates)
        if promote_to_global and updated:
            self.engine.promote(mem_id, target_scope="global")

        return {
            "success": True,
            "id": mem_id,
            "trust_status": "trusted",
            "promoted_to_global": promote_to_global,
        }

    def reject_candidate(self, mem_id: str, reason: str = "Rejected by human reviewer") -> Dict[str, Any]:
        """Reject a candidate lesson."""
        entry = self.engine.get(mem_id)
        if not entry:
            return {"success": False, "error": f"Entry not found: {mem_id}"}

        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        updates = {
            "trust_status": "rejected",
            "rejection_reason": reason,
            "rejected_at": now,
        }
        self.engine.update(mem_id, updates)
        return {"success": True, "id": mem_id, "trust_status": "rejected", "reason": reason}

    def rollback(self, mem_id: str) -> Dict[str, Any]:
        """Roll back an approved lesson to stale/rejected."""
        entry = self.engine.get(mem_id)
        if not entry:
            return {"success": False, "error": f"Entry not found: {mem_id}"}

        self.engine.update(mem_id, {"trust_status": "stale"})
        return {"success": True, "id": mem_id, "trust_status": "stale"}


def main() -> int:
    ap = argparse.ArgumentParser(description="Aether Continuous Learning Pipeline CLI")
    sub = ap.add_subparsers(dest="cmd", required=True)

    prop = sub.add_parser("propose", help="Propose a candidate lesson from completed work")
    prop.add_argument("title", help="Short pattern title")
    prop.add_argument("lesson", help="Reusable lesson content")
    prop.add_argument("--category", required=True, choices=sorted(CATEGORIES))
    prop.add_argument("--evidence", required=True, help="Mandatory file/test/symbol evidence")
    prop.add_argument("--project", default="default")
    prop.add_argument("--confidence", default="high", choices=["high", "medium", "low"])
    prop.add_argument("--tags", default="", help="Comma-separated tags")

    sub.add_parser("list", help="List candidate lessons pending approval")

    appr = sub.add_parser("approve", help="Approve a candidate lesson")
    appr.add_argument("id", help="Memory entry ID")
    appr.add_argument("--reviewer", default="human")
    appr.add_argument("--global", dest="to_global", action="store_true", help="Promote to global memory")

    rej = sub.add_parser("reject", help="Reject a candidate lesson")
    rej.add_argument("id", help="Memory entry ID")
    rej.add_argument("--reason", default="Rejected by human review")

    rb = sub.add_parser("rollback", help="Roll back a previously approved lesson")
    rb.add_argument("id", help="Memory entry ID")

    args = ap.parse_args()
    pipeline = LearningPipeline()

    if args.cmd == "propose":
        tags = [t.strip() for t in args.tags.split(",") if t.strip()]
        res = pipeline.propose_candidate(
            title=args.title,
            lesson=args.lesson,
            category=args.category,
            evidence=args.evidence,
            project_id=args.project,
            confidence=args.confidence,
            tags=tags,
        )
        print(json.dumps(res, indent=2))
    elif args.cmd == "list":
        candidates = pipeline.list_candidates()
        print(f"Pending Candidate Lessons: {len(candidates)}")
        for c in candidates:
            print(f"- [{c['id']}] {c['title']} ({c['category']})")
            print(f"    Evidence: {c.get('evidence')}")
            print(f"    Lesson:   {c['content'][:120]}...")
    elif args.cmd == "approve":
        res = pipeline.approve_candidate(args.id, reviewer=args.reviewer, promote_to_global=args.to_global)
        print(json.dumps(res, indent=2))
    elif args.cmd == "reject":
        res = pipeline.reject_candidate(args.id, reason=args.reason)
        print(json.dumps(res, indent=2))
    elif args.cmd == "rollback":
        res = pipeline.rollback(args.id)
        print(json.dumps(res, indent=2))

    return 0


if __name__ == "__main__":
    sys.exit(main())
