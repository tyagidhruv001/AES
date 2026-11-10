#!/usr/bin/env python3
"""Heuristic scanner for Aether configuration and repository hygiene.

Design notes
------------
* File-type-aware rules: prompt-injection and permission-override patterns
  are intentionally scoped to agent-instruction and configuration file types
  (Markdown, JSON, YAML, TOML).  Applying them to Python source would cause
  self-detection false positives because this scanner's own detection patterns
  contain the phrases they look for.
* Self-exclusion: ``security_scan.py`` itself is explicitly skipped for
  content scanning.  Its presence on disk is benign and expected.
* Credential detection applies broadly (all supported text files) because
  secrets can appear in any file type, including Python.
* Standard library only — no third-party dependencies.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Skip-list: directories that are never descended into
# ---------------------------------------------------------------------------
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "dist", "build", "__pycache__"}

# Files whose names are inherently secret-like (checked before content scan)
SECRET_FILE_NAMES = {".env", ".env.local", "id_rsa", "id_ed25519"}

# ---------------------------------------------------------------------------
# File-type groups
# ---------------------------------------------------------------------------
# Config / agent-instruction files: Markdown, JSON, YAML, TOML
_AGENT_CONFIG_SUFFIXES: frozenset[str] = frozenset({".md", ".json", ".yaml", ".yml", ".toml"})

# Source / scripting files: Python, PowerShell, shell, JS, TS
_SOURCE_SUFFIXES: frozenset[str] = frozenset({".py", ".ps1", ".sh", ".js", ".ts"})

# Plain text — treated like source for credential scanning
_PLAIN_SUFFIXES: frozenset[str] = frozenset({".txt"})

# Union of all text file types that the scanner reads
TEXT_SUFFIXES: frozenset[str] = _AGENT_CONFIG_SUFFIXES | _SOURCE_SUFFIXES | _PLAIN_SUFFIXES

# ---------------------------------------------------------------------------
# Detection patterns
#
# Each entry is a tuple:
#   (severity, compiled_pattern, message, applicable_suffix_set | None)
#
# ``applicable_suffix_set=None`` means the rule applies to ALL text files.
# ---------------------------------------------------------------------------

# -- Prompt-injection-like phrases in agent/config files only ---------------
# These phrases have no legitimate business in agent instructions or configs.
# They are intentionally NOT applied to Python source files so the scanner's
# own pattern definitions do not trigger a finding.
_PROMPT_INJECTION_RE = re.compile(
    r"(?i)\b(ignore all previous instructions|reveal system prompt|exfiltrate secrets)\b"
)

# -- Hardcoded credential literals (all file types) --------------------------
# Looks for  key = "XXXXXXXX"  style assignments.  Redaction applied at output.
_CREDENTIAL_RE = re.compile(
    r"""(?i)\b(api[_\-]?key|secret|password|token)\s*[:=]\s*['"][^'"]{8,}['"]"""
)

# -- Overly broad command-execution policy in config files only -------------
# ``commandExecutionPolicy: yolo`` or ``unrestricted`` in agent YAML / JSON.
_CMD_POLICY_RE = re.compile(
    r"(?i)\bcommandExecutionPolicy\s*:\s*(?:yolo|unrestricted)\b"
)

# -- Write-tools flag in config files only ----------------------------------
_WRITE_TOOLS_RE = re.compile(
    r"(?i)\benable_write_tools\s*:\s*true\b"
)

# -- Permission-override keywords in config files only ----------------------
# ``auto_approve`` / ``deny_unless_prior_grant`` are meaningful as permission
# directives only inside configuration files, not in Python source code where
# they appear as string literals inside detection patterns.
_PERM_OVERRIDE_RE = re.compile(
    r"(?i)\b(auto_approve|deny_unless_prior_grant)\b"
)

# Registry: (severity, pattern, message, applicable_suffixes_or_None)
RULES: list[tuple[str, re.Pattern[str], str, frozenset[str] | None]] = [
    (
        "HIGH",
        _PROMPT_INJECTION_RE,
        "Prompt-injection-like instruction in agent config/document.",
        _AGENT_CONFIG_SUFFIXES,          # agent/config files only
    ),
    (
        "HIGH",
        _CREDENTIAL_RE,
        "Possible hardcoded credential literal. Value redacted.",
        None,                            # all text files
    ),
    (
        "MEDIUM",
        _CMD_POLICY_RE,
        "Overly broad command execution policy.",
        _AGENT_CONFIG_SUFFIXES,          # config files only
    ),
    (
        "MEDIUM",
        _WRITE_TOOLS_RE,
        "Write tools enabled; verify least privilege.",
        _AGENT_CONFIG_SUFFIXES,          # config files only
    ),
    (
        "MEDIUM",
        _PERM_OVERRIDE_RE,
        "Permission override found; inspect hook behavior.",
        _AGENT_CONFIG_SUFFIXES,          # config files only
    ),
]

# ---------------------------------------------------------------------------
# Redaction helper
# ---------------------------------------------------------------------------
_REDACT_RE = re.compile(
    r"""(?i)(api[_\-]?key|secret|password|token)(\s*[:=]\s*)['"][^'"]+['"]"""
)


def _redact(line: str) -> str:
    """Replace credential values with [REDACTED] before including in output."""
    return _REDACT_RE.sub(r"\1\2[REDACTED]", line)


# ---------------------------------------------------------------------------
# Scanner
# ---------------------------------------------------------------------------

def _should_skip_path(path: Path, root: Path) -> bool:
    """Return True if *path* should be skipped entirely (not content-scanned)."""
    # Skip any path whose parts include a blocked directory name
    relative_parts = path.relative_to(root).parts
    if any(part in SKIP_DIRS for part in relative_parts):
        return True
    # Skip this scanner's own source file to avoid self-detection
    if path.resolve() == Path(__file__).resolve():
        return True
    return False


def scan(root: Path) -> list[dict]:
    findings: list[dict] = []

    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if _should_skip_path(p, root):
            continue

        rel = str(p.relative_to(root))

        # --- Secret-like file names (checked before reading content) --------
        if p.name in SECRET_FILE_NAMES or p.name.startswith(".env"):
            findings.append({
                "severity": "HIGH",
                "path": rel,
                "line": None,
                "message": "Secret-like file present. Do not stage or print its contents.",
            })
            continue

        suffix = p.suffix.lower()
        if suffix not in TEXT_SUFFIXES:
            continue

        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        for lineno, line in enumerate(text.splitlines(), 1):
            for severity, pattern, message, applicable in RULES:
                # Skip rules that don't apply to this file type
                if applicable is not None and suffix not in applicable:
                    continue
                if pattern.search(line):
                    findings.append({
                        "severity": severity,
                        "path": rel,
                        "line": lineno,
                        "message": message,
                        "evidence_redacted": _redact(line.strip())[:240],
                    })

    return findings


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(
        description="Heuristic security scanner for Aether configuration files."
    )
    ap.add_argument("path", nargs="?", default=".",
                    help="Root directory to scan (default: current directory).")
    args = ap.parse_args()

    root = Path(args.path).resolve()
    findings = scan(root)

    counts = {
        s: sum(1 for f in findings if f["severity"] == s)
        for s in ("HIGH", "MEDIUM", "LOW")
    }

    output = {
        "root": str(root),
        "counts": counts,
        "findings": findings,
        "limitations": [
            "Heuristic only; false positives and false negatives are expected.",
            "Prompt-injection and permission-override rules apply to agent/config"
            " files only (.md, .json, .yaml, .yml, .toml); Python source is"
            " excluded from those rules to prevent self-detection.",
            "Does not read contents of secret-like files.",
            "Not a substitute for dependency scanning, secret scanning, or a"
            " full security audit.",
        ],
    }

    # Never print actual secret values — redaction is applied above.
    print(json.dumps(output, indent=2))
    return 1 if counts["HIGH"] else 0


if __name__ == "__main__":
    sys.exit(main())
