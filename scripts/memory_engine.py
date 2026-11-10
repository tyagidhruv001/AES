#!/usr/bin/env python3
"""Lightweight, portable, zero-dependency Memory Engine for Aether.

Implements structured memory storage, relevance-ranked search, duplicate
detection, conflict identification, promotion, lifecycle management, and
automated secret redaction. Standard library only.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# Categories supported by Aether Memory Engine
CATEGORIES = {
    "global_preferences",
    "project_knowledge",
    "architecture_decisions",
    "known_issues",
    "technical_discoveries",
    "session_summaries",
    "task_handoffs",
    "lessons_learned",
}

SCOPES = {"global", "project", "session"}
CONFIDENCE_LEVELS = {"high", "medium", "low"}
TRUST_STATUSES = {"trusted", "proposed", "untrusted", "stale", "rejected"}

# Security redaction regexes
REDACT_PATTERNS = [
    (re.compile(r"""(?i)(api[_\-]?key|secret|password|token)\s*[:=]\s*['"][^'"]{6,}['"]"""), r"\1=[REDACTED]"),
    (re.compile(r"""(?i)\b(bearer\s+)[a-zA-Z0-9_\-\.]{16,}\b"""), r"\1[REDACTED]"),
    (re.compile(r"""-----BEGIN (?:RSA |EC )?PRIVATE KEY-----[\s\S]+?-----END (?:RSA |EC )?PRIVATE KEY-----"""), "[REDACTED PRIVATE KEY]"),
]

# Prompt-injection detection inside memory payloads
INJECTION_PATTERN = re.compile(
    r"(?i)\b(ignore all previous instructions|reveal system prompt|exfiltrate secrets|system override)\b"
)


def sanitize_text(text: str) -> str:
    """Redact sensitive credentials and tokens from text."""
    clean = text
    for pattern, replacement in REDACT_PATTERNS:
        clean = pattern.sub(replacement, clean)
    return clean


def tokenize(text: str) -> Set[str]:
    """Simple lowercase word tokenizer for ranking and similarity."""
    return set(re.findall(r"\b[a-zA-Z0-9_\-]{2,}\b", text.lower()))


def jaccard_similarity(set_a: Set[str], set_b: Set[str]) -> float:
    """Calculate Jaccard similarity between two token sets."""
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union if union > 0 else 0.0


class MemoryEngine:
    def __init__(self, root_dir: Optional[Path] = None):
        if root_dir is None:
            # Default to repo root / memory or .aether/memory
            self.root = Path(__file__).resolve().parents[1] / "memory"
        else:
            self.root = Path(root_dir).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        (self.root / "global").mkdir(parents=True, exist_ok=True)
        (self.root / "projects").mkdir(parents=True, exist_ok=True)
        (self.root / "sessions").mkdir(parents=True, exist_ok=True)

    def _get_store_path(self, scope: str, project_id: Optional[str] = None) -> Path:
        if scope == "global":
            return self.root / "global" / "memory.jsonl"
        elif scope == "session":
            return self.root / "sessions" / "memory.jsonl"
        elif scope == "project":
            p_id = project_id or "default"
            proj_dir = self.root / "projects" / p_id
            proj_dir.mkdir(parents=True, exist_ok=True)
            return proj_dir / "memory.jsonl"
        else:
            raise ValueError(f"Invalid scope: {scope}")

    def _read_all(self, scope: Optional[str] = None, project_id: Optional[str] = None) -> List[Dict[str, Any]]:
        entries: List[Dict[str, Any]] = []
        stores: List[Path] = []
        if scope:
            stores.append(self._get_store_path(scope, project_id))
        else:
            # Read all scopes
            stores.append(self._get_store_path("global"))
            stores.append(self._get_store_path("session"))
            proj_root = self.root / "projects"
            if proj_root.exists():
                for p_dir in proj_root.iterdir():
                    if p_dir.is_dir():
                        stores.append(p_dir / "memory.jsonl")

        for store in stores:
            if not store.exists():
                continue
            try:
                for line in store.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if line:
                        entries.append(json.loads(line))
            except (OSError, json.JSONDecodeError):
                continue
        return entries

    def _write_store(self, store_path: Path, entries: List[Dict[str, Any]]) -> None:
        store_path.parent.mkdir(parents=True, exist_ok=True)
        lines = [json.dumps(e, ensure_ascii=False) for e in entries]
        store_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")

    def add(
        self,
        title: str,
        content: str,
        category: str,
        scope: str = "project",
        project_id: str = "default",
        source: str = "user",
        confidence: str = "high",
        tags: Optional[List[str]] = None,
        evidence: str = "",
        expires_days: Optional[int] = None,
        trust_status: str = "trusted",
    ) -> Dict[str, Any]:
        """Create a sanitized, validated memory entry."""
        if category not in CATEGORIES:
            raise ValueError(f"Invalid category: {category}. Must be one of {sorted(CATEGORIES)}")
        if scope not in SCOPES:
            raise ValueError(f"Invalid scope: {scope}. Must be one of {sorted(SCOPES)}")
        if confidence not in CONFIDENCE_LEVELS:
            raise ValueError(f"Invalid confidence: {confidence}. Must be one of {sorted(CONFIDENCE_LEVELS)}")

        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        clean_title = sanitize_text(title.strip())
        clean_content = sanitize_text(content.strip())
        clean_evidence = sanitize_text(evidence.strip())

        # Check for prompt injection in memory content
        if INJECTION_PATTERN.search(clean_content) or INJECTION_PATTERN.search(clean_title):
            trust_status = "untrusted"
            clean_content = f"[SECURITY NOTICE: Flagged for suspicious instruction pattern]\n{clean_content}"

        # Generate unique ID
        hash_digest = hashlib.sha256(f"{clean_title}:{clean_content}:{now}".encode("utf-8")).hexdigest()[:10]
        mem_id = f"mem_{datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d')}_{hash_digest}"

        expires_at = None
        if expires_days:
            exp_date = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=expires_days)
            expires_at = exp_date.isoformat()

        entry: Dict[str, Any] = {
            "id": mem_id,
            "created_at": now,
            "updated_at": now,
            "title": clean_title,
            "content": clean_content,
            "category": category,
            "scope": scope,
            "project_id": project_id if scope == "project" else ("global" if scope == "global" else "session"),
            "source": sanitize_text(source),
            "confidence": confidence,
            "trust_status": trust_status,
            "tags": [sanitize_text(t.strip().lower()) for t in (tags or []) if t.strip()],
            "evidence": clean_evidence,
            "expires_at": expires_at,
        }

        # Check for duplicates before appending
        existing = self._read_all(scope, project_id)
        tokens_new = tokenize(clean_title + " " + clean_content)
        for old in existing:
            tokens_old = tokenize(old["title"] + " " + old["content"])
            if jaccard_similarity(tokens_new, tokens_old) > 0.85:
                entry["duplicate_of"] = old["id"]
                entry["trust_status"] = "stale"
                break

        existing.append(entry)
        store_path = self._get_store_path(scope, project_id)
        self._write_store(store_path, existing)
        return entry

    def get(self, mem_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a single memory entry by ID."""
        for e in self._read_all():
            if e["id"] == mem_id:
                return e
        return None

    def search(
        self,
        query: str,
        scope: Optional[str] = None,
        project_id: Optional[str] = None,
        category: Optional[str] = None,
        min_confidence: Optional[str] = None,
        limit: int = 10,
    ) -> List[Tuple[Dict[str, Any], float]]:
        """Relevance-ranked keyword search across memory stores."""
        entries = self._read_all(scope, project_id)
        q_tokens = tokenize(query)
        if not q_tokens:
            return [(e, 1.0) for e in entries[:limit]]

        confidence_weights = {"high": 1.2, "medium": 1.0, "low": 0.7}
        status_penalties = {"trusted": 1.0, "proposed": 0.8, "stale": 0.4, "untrusted": 0.1, "rejected": 0.0}

        ranked: List[Tuple[Dict[str, Any], float]] = []
        for e in entries:
            if category and e.get("category") != category:
                continue
            if min_confidence:
                order = ["low", "medium", "high"]
                if order.index(e.get("confidence", "low")) < order.index(min_confidence):
                    continue

            # Calculate token match score
            e_tokens = tokenize(e["title"] + " " + e["content"] + " " + " ".join(e.get("tags", [])))
            title_tokens = tokenize(e["title"])
            
            overlap = q_tokens & e_tokens
            if not overlap:
                continue

            # Scoring: title matches weighted higher
            score = len(overlap) / len(q_tokens)
            title_overlap = q_tokens & title_tokens
            if title_overlap:
                score += (len(title_overlap) / len(q_tokens)) * 0.5

            # Apply confidence and trust weights
            conf_w = confidence_weights.get(e.get("confidence", "medium"), 1.0)
            stat_w = status_penalties.get(e.get("trust_status", "trusted"), 1.0)
            final_score = score * conf_w * stat_w

            if final_score > 0.0:
                ranked.append((e, round(final_score, 4)))

        ranked.sort(key=lambda x: x[1], reverse=True)
        return ranked[:limit]

    def update(self, mem_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update fields of an existing memory entry."""
        for scope in SCOPES:
            if scope == "project":
                proj_root = self.root / "projects"
                if proj_root.exists():
                    for p_dir in proj_root.iterdir():
                        if p_dir.is_dir():
                            updated = self._update_in_store(p_dir / "memory.jsonl", mem_id, updates)
                            if updated:
                                return updated
            else:
                updated = self._update_in_store(self._get_store_path(scope), mem_id, updates)
                if updated:
                    return updated
        return None

    def _update_in_store(self, store_path: Path, mem_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not store_path.exists():
            return None
        entries = []
        target = None
        for line in store_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            e = json.loads(line)
            if e["id"] == mem_id:
                for k, v in updates.items():
                    if k in {"title", "content", "evidence", "rejection_reason"}:
                        e[k] = sanitize_text(str(v))
                    elif k in {"confidence", "trust_status", "category", "tags", "expires_at", "reviewed_by", "approved_at", "rejected_at"}:
                        e[k] = v
                e["updated_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
                target = e
            entries.append(e)
        if target:
            self._write_store(store_path, entries)
            return target
        return None

    def delete(self, mem_id: str) -> bool:
        """Delete an entry by ID across all stores."""
        deleted = False
        stores = [self._get_store_path("global"), self._get_store_path("session")]
        proj_root = self.root / "projects"
        if proj_root.exists():
            for p_dir in proj_root.iterdir():
                if p_dir.is_dir():
                    stores.append(p_dir / "memory.jsonl")

        for store in stores:
            if not store.exists():
                continue
            entries = []
            found = False
            for line in store.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                e = json.loads(line)
                if e["id"] == mem_id:
                    found = True
                    deleted = True
                else:
                    entries.append(e)
            if found:
                self._write_store(store, entries)
        return deleted

    def promote(self, mem_id: str, target_scope: str = "global") -> Optional[Dict[str, Any]]:
        """Promote an entry to global scope after validation."""
        entry = self.get(mem_id)
        if not entry:
            return None
        if target_scope not in {"global", "project"}:
            raise ValueError(f"Cannot promote to scope: {target_scope}")

        # Delete from old location
        self.delete(mem_id)

        # Add to new scope
        entry["scope"] = target_scope
        entry["trust_status"] = "trusted"
        entry["updated_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        dest_store = self._get_store_path(target_scope, entry.get("project_id", "default"))
        existing = self._read_all(target_scope, entry.get("project_id", "default"))
        existing.append(entry)
        self._write_store(dest_store, existing)
        return entry

    def expire_stale(self) -> int:
        """Scan and mark expired entries as stale."""
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        count = 0
        for e in self._read_all():
            exp = e.get("expires_at")
            if exp and exp < now and e.get("trust_status") != "stale":
                self.update(e["id"], {"trust_status": "stale"})
                count += 1
        return count

    def detect_conflicts(self, title: str, category: str, project_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Detect entries in the same category/project with overlapping terms but conflicting status."""
        tokens = tokenize(title)
        entries = self._read_all(project_id=project_id)
        conflicts = []
        for e in entries:
            if e.get("category") == category:
                e_tokens = tokenize(e["title"])
                overlap = tokens & e_tokens
                if len(overlap) >= 2 and e.get("trust_status") in {"rejected", "untrusted"}:
                    conflicts.append(e)
        return conflicts


def main() -> int:
    ap = argparse.ArgumentParser(description="Aether Memory Engine CLI")
    sub = ap.add_subparsers(dest="cmd", required=True)

    add_p = sub.add_parser("add", help="Add a memory entry")
    add_p.add_argument("title", help="Memory title")
    add_p.add_argument("content", help="Memory fact/content")
    add_p.add_argument("--category", required=True, choices=sorted(CATEGORIES))
    add_p.add_argument("--scope", default="project", choices=sorted(SCOPES))
    add_p.add_argument("--project", default="default")
    add_p.add_argument("--confidence", default="high", choices=sorted(CONFIDENCE_LEVELS))
    add_p.add_argument("--tags", default="", help="Comma-separated tags")
    add_p.add_argument("--evidence", default="", help="Sanitized evidence reference")

    search_p = sub.add_parser("search", help="Search memory")
    search_p.add_argument("query", help="Keywords to search")
    search_p.add_argument("--category", choices=sorted(CATEGORIES))
    search_p.add_argument("--scope", choices=sorted(SCOPES))
    search_p.add_argument("--project", default="default")
    search_p.add_argument("--limit", type=int, default=5)

    list_p = sub.add_parser("list", help="List memories")
    list_p.add_argument("--scope", choices=sorted(SCOPES))
    list_p.add_argument("--project", default="default")

    del_p = sub.add_parser("delete", help="Delete a memory entry")
    del_p.add_argument("id", help="Memory ID")

    promote_p = sub.add_parser("promote", help="Promote memory to global")
    promote_p.add_argument("id", help="Memory ID")

    expire_p = sub.add_parser("expire", help="Run stale expiration sweep")

    args = ap.parse_args()
    engine = MemoryEngine()

    if args.cmd == "add":
        tags = [t.strip() for t in args.tags.split(",") if t.strip()]
        res = engine.add(
            title=args.title,
            content=args.content,
            category=args.category,
            scope=args.scope,
            project_id=args.project,
            confidence=args.confidence,
            tags=tags,
            evidence=args.evidence,
        )
        print(json.dumps(res, indent=2))
    elif args.cmd == "search":
        results = engine.search(
            query=args.query,
            category=args.category,
            scope=args.scope,
            project_id=args.project,
            limit=args.limit,
        )
        print(f"Found {len(results)} match(es):")
        for entry, score in results:
            print(f"[{score:.2f}] ({entry['id']}) {entry['title']} - {entry['trust_status']}")
            print(f"     Content: {entry['content'][:120]}...")
    elif args.cmd == "list":
        entries = engine._read_all(args.scope, args.project)
        print(f"Total entries: {len(entries)}")
        for e in entries:
            print(f"- [{e['id']}] [{e['category']}] ({e['scope']}) {e['title']} ({e['trust_status']})")
    elif args.cmd == "delete":
        ok = engine.delete(args.id)
        print(f"Deleted {args.id}: {ok}")
    elif args.cmd == "promote":
        promoted = engine.promote(args.id)
        print(f"Promoted {args.id}: {promoted is not None}")
    elif args.cmd == "expire":
        n = engine.expire_stale()
        print(f"Expired {n} stale entry(ies)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
