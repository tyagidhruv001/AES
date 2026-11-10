#!/usr/bin/env python3
"""Aether Project Intelligence Scanner.

Read-only repository discovery and architectural analysis.
Distinguishes directly detected facts, inferred facts, and unknown information.
Standard library only; does not execute project code or read secrets.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

# Ignored directories
EXCLUDED_DIRS = {
    ".git", ".hg", ".svn", "node_modules", "vendor", "dist", "build",
    ".next", ".nuxt", ".venv", "venv", "__pycache__", ".idea", ".vscode",
    "coverage", "target", "bin", "obj", "codedump", ".aether"
}

SECRET_NAMES = {
    ".env", ".env.local", ".env.production", "id_rsa", "id_ed25519",
    "credentials.json", "service-account.json"
}

MANIFEST_FILES = {
    "package.json", "pyproject.toml", "requirements.txt", "Pipfile",
    "poetry.lock", "pom.xml", "build.gradle", "build.gradle.kts",
    "Cargo.toml", "go.mod", "composer.json", "Gemfile", "pubspec.yaml",
    "Dockerfile", "docker-compose.yml", "compose.yaml", "firebase.json",
    "vercel.json", "wrangler.toml", "Makefile", "justfile", "schema.prisma"
}

ENTRYPOINT_NAMES = {
    "main.py", "app.py", "server.py", "manage.py", "wsgi.py", "asgi.py",
    "index.js", "server.js", "main.js", "app.js", "index.ts", "main.ts",
    "server.ts", "App.jsx", "App.tsx", "main.jsx", "main.tsx",
    "Program.cs", "Startup.cs", "Main.java", "main.go", "src/main.rs", "src/lib.rs"
}


def safe_read(path: Path, max_bytes: int = 120_000) -> Optional[str]:
    """Read file content safely with size limit and secret avoidance."""
    try:
        if path.name.lower() in SECRET_NAMES or path.name.lower().startswith(".env"):
            return None
        data = path.read_bytes()[:max_bytes]
        return data.decode("utf-8", errors="replace")
    except (OSError, PermissionError):
        return None


def walk_repo(root: Path, max_files: int = 5000) -> List[Path]:
    """Walk repository respecting ignore rules and size limits."""
    collected: List[Path] = []
    for current, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in EXCLUDED_DIRS and not d.startswith(".aether"))
        base = Path(current)
        for name in sorted(files):
            p = base / name
            if p.name.lower() in SECRET_NAMES or p.name.lower().startswith(".env"):
                continue
            collected.append(p)
            if len(collected) >= max_files:
                return collected
    return collected


def scan_project(root: Path, max_files: int = 5000) -> Dict[str, Any]:
    """Analyze repository and return structured project intelligence."""
    paths = walk_repo(root, max_files=max_files)
    rels = [p.relative_to(root).as_posix() for p in paths]
    names = {p.name for p in paths}
    names_lower = {n.lower() for n in names}

    detected_facts: Dict[str, Any] = {
        "manifests_present": [],
        "entrypoints_present": [],
        "configuration_files": [],
        "package_managers": [],
        "test_frameworks": [],
        "build_tools": [],
    }

    inferred_facts: Dict[str, Any] = {
        "languages": [],
        "frameworks": [],
        "database_technologies": [],
        "api_architecture": [],
        "authentication": [],
        "deployment": [],
    }

    unknowns: List[str] = []

    # 1. Package Managers & Manifests
    all_dep_text = ""
    for p in paths:
        if p.name in MANIFEST_FILES:
            content = safe_read(p) or ""
            all_dep_text += " " + content.lower()
            detected_facts["manifests_present"].append(p.relative_to(root).as_posix())

    if "package.json" in names:
        if "pnpm-lock.yaml" in names:
            detected_facts["package_managers"].append("pnpm")
        elif "yarn.lock" in names:
            detected_facts["package_managers"].append("yarn")
        else:
            detected_facts["package_managers"].append("npm")
    if "poetry.lock" in names:
        detected_facts["package_managers"].append("poetry")
    elif "pipfile" in names_lower:
        detected_facts["package_managers"].append("pipenv")
    elif "requirements.txt" in names or "pyproject.toml" in names:
        detected_facts["package_managers"].append("pip")
    if "cargo.toml" in names_lower:
        detected_facts["package_managers"].append("cargo")
    if "pom.xml" in names:
        detected_facts["package_managers"].append("maven")
    if "build.gradle" in names or "build.gradle.kts" in names:
        detected_facts["package_managers"].append("gradle")
    if "go.mod" in names:
        detected_facts["package_managers"].append("go modules")

    # 2. Languages
    extensions = {p.suffix.lower() for p in paths}
    lang_map = {
        ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript",
        ".jsx": "React (JSX)", ".tsx": "React (TSX)", ".java": "Java",
        ".rs": "Rust", ".go": "Go", ".cs": "C# / .NET", ".php": "PHP",
        ".rb": "Ruby", ".kt": "Kotlin", ".dart": "Dart"
    }
    for ext, lang in lang_map.items():
        if ext in extensions:
            inferred_facts["languages"].append(lang)

    # 3. Frameworks
    if "next.config.js" in names or "next.config.ts" in names or "next.config.mjs" in names or "next" in all_dep_text:
        inferred_facts["frameworks"].append("Next.js")
    elif "vite.config.js" in names or "vite.config.ts" in names or "vite" in all_dep_text:
        inferred_facts["frameworks"].append("Vite")
    if "react" in all_dep_text:
        inferred_facts["frameworks"].append("React")
    if "fastapi" in all_dep_text:
        inferred_facts["frameworks"].append("FastAPI")
    if "flask" in all_dep_text:
        inferred_facts["frameworks"].append("Flask")
    if "django" in all_dep_text:
        inferred_facts["frameworks"].append("Django")
    if "express" in all_dep_text:
        inferred_facts["frameworks"].append("Express")
    if "spring-boot" in all_dep_text or "org.springframework.boot" in all_dep_text:
        inferred_facts["frameworks"].append("Spring Boot")

    # 4. Database Technologies
    if "prisma" in all_dep_text or "schema.prisma" in names:
        inferred_facts["database_technologies"].append("Prisma ORM")
    if "pg" in all_dep_text or "psycopg" in all_dep_text or "postgresql" in all_dep_text or "asyncpg" in all_dep_text:
        inferred_facts["database_technologies"].append("PostgreSQL")
    if "mysql" in all_dep_text or "mysql2" in all_dep_text:
        inferred_facts["database_technologies"].append("MySQL")
    if "sqlite" in all_dep_text or "sqlite3" in all_dep_text:
        inferred_facts["database_technologies"].append("SQLite")
    if "mongodb" in all_dep_text or "mongoose" in all_dep_text or "pymongo" in all_dep_text:
        inferred_facts["database_technologies"].append("MongoDB")
    if "redis" in all_dep_text or "ioredis" in all_dep_text:
        inferred_facts["database_technologies"].append("Redis")
    if "sqlalchemy" in all_dep_text:
        inferred_facts["database_technologies"].append("SQLAlchemy")

    # 5. API Architecture
    if "graphql" in all_dep_text or any(".graphql" in r for r in rels):
        inferred_facts["api_architecture"].append("GraphQL")
    if "grpc" in all_dep_text or any(".proto" in r for r in rels):
        inferred_facts["api_architecture"].append("gRPC")
    if "socket.io" in all_dep_text or "websocket" in all_dep_text:
        inferred_facts["api_architecture"].append("WebSockets")
    if any(f in inferred_facts["frameworks"] for f in ["FastAPI", "Express", "Flask", "Django", "Next.js"]):
        inferred_facts["api_architecture"].append("REST")

    # 6. Authentication
    if "jsonwebtoken" in all_dep_text or "pyjwt" in all_dep_text or "jose" in all_dep_text:
        inferred_facts["authentication"].append("JWT (JSON Web Tokens)")
    if "next-auth" in all_dep_text or "@auth/" in all_dep_text:
        inferred_facts["authentication"].append("NextAuth.js")
    if "passport" in all_dep_text:
        inferred_facts["authentication"].append("Passport.js")
    if "firebase-auth" in all_dep_text or "firebase/auth" in all_dep_text:
        inferred_facts["authentication"].append("Firebase Auth")

    # 7. Testing Frameworks
    if "jest" in all_dep_text:
        detected_facts["test_frameworks"].append("Jest")
    if "vitest" in all_dep_text:
        detected_facts["test_frameworks"].append("Vitest")
    if "pytest" in all_dep_text or "pytest.ini" in names:
        detected_facts["test_frameworks"].append("Pytest")
    if "playwright" in all_dep_text:
        detected_facts["test_frameworks"].append("Playwright")
    if any("unittest" in (safe_read(p) or "") for p in paths if p.suffix == ".py"):
        detected_facts["test_frameworks"].append("unittest")

    # 8. Deployment
    if "dockerfile" in names_lower or "docker-compose.yml" in names_lower:
        inferred_facts["deployment"].append("Docker")
    if "k8s" in names_lower or any("k8s" in r or "kubernetes" in r for r in rels):
        inferred_facts["deployment"].append("Kubernetes")
    if "terraform" in all_dep_text or any(".tf" in r for r in rels):
        inferred_facts["deployment"].append("Terraform")
    if "vercel.json" in names:
        inferred_facts["deployment"].append("Vercel")
    if "wrangler.toml" in names:
        inferred_facts["deployment"].append("Cloudflare Workers")

    # 9. Entry points
    for r in rels:
        p_name = Path(r).name
        if p_name in ENTRYPOINT_NAMES or r in ENTRYPOINT_NAMES:
            detected_facts["entrypoints_present"].append(r)

    # 10. Record Unknowns
    if not inferred_facts["database_technologies"]:
        unknowns.append("Database technology: Not detected in dependencies/manifests (may be stateless or external).")
    if not inferred_facts["authentication"]:
        unknowns.append("Authentication mechanism: Not detected in manifests.")
    if not inferred_facts["deployment"]:
        unknowns.append("Deployment configuration: No container or IaC manifests identified.")
    if not detected_facts["test_frameworks"]:
        unknowns.append("Test framework: No standard test dependencies or test config files detected.")

    return {
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "root": str(root),
        "total_files_scanned": len(paths),
        "detected_facts": detected_facts,
        "inferred_facts": inferred_facts,
        "unknowns": unknowns,
        "notes": [
            "Read-only heuristic analysis; no code was executed.",
            "Codedump and build/dependency caches were strictly excluded.",
            "Secrets and credentials were not inspected.",
        ]
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Aether Project Intelligence Scanner")
    sub = ap.add_subparsers(dest="cmd", required=True)

    scan_p = sub.add_parser("scan", help="Scan repository and output structured intelligence report")
    scan_p.add_argument("path", nargs="?", default=".", help="Root path of target repository")
    scan_p.add_argument("--max-files", type=int, default=5000, help="Maximum files to scan")
    scan_p.add_argument("--out", help="Output file path (JSON)")

    args = ap.parse_args()
    root = Path(args.path).resolve()
    if not root.is_dir():
        print(f"Error: {root} is not a directory.", file=sys.stderr)
        return 1

    report = scan_project(root, max_files=args.max_files)
    output = json.dumps(report, indent=2, ensure_ascii=False)

    if args.out:
        out_p = Path(args.out)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(output + "\n", encoding="utf-8")
        print(f"Project intelligence report saved to: {out_p}")
    else:
        print(output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
