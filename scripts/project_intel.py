#!/usr/bin/env python3
"""Read-only repository inventory. Standard library only; does not read secret values."""
from pathlib import Path
import argparse, json, os, re, datetime

EXCLUDED_DIRS = {
    ".git", ".hg", ".svn", "node_modules", "vendor", "dist", "build",
    ".next", ".nuxt", ".venv", "venv", "__pycache__", ".idea", ".vscode",
    "coverage", "target", "bin", "obj"
}
SECRET_NAMES = {
    ".env", ".env.local", ".env.production", "id_rsa", "id_ed25519",
    "credentials.json", "service-account.json"
}
MANIFESTS = [
    "package.json", "pyproject.toml", "requirements.txt", "Pipfile",
    "pom.xml", "build.gradle", "build.gradle.kts", "Cargo.toml",
    "go.mod", "composer.json", "Gemfile", "pubspec.yaml",
    "Dockerfile", "docker-compose.yml", "compose.yaml",
    "firebase.json", "vercel.json", "wrangler.toml"
]
ENTRY_NAMES = {
    "main.py", "app.py", "server.py", "index.js", "server.js", "main.js",
    "main.ts", "index.ts", "App.jsx", "App.tsx", "main.jsx", "main.tsx",
    "Program.cs", "Main.java", "main.go", "src/main.rs"
}
TEST_HINTS = ("test", "spec", "__tests__")
SCRIPT_HINTS = ("package.json", "pyproject.toml", "Makefile", "justfile")

def safe_read(path, max_bytes=120_000):
    try:
        if path.name.lower() in SECRET_NAMES or path.name.lower().startswith(".env"):
            return None
        data = path.read_bytes()[:max_bytes]
        return data.decode("utf-8", errors="replace")
    except (OSError, PermissionError):
        return None

def walk(root):
    for current, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in EXCLUDED_DIRS and not d.startswith(".aether"))
        base = Path(current)
        for name in sorted(files):
            p = base / name
            if p.name.lower() in SECRET_NAMES or p.name.lower().startswith(".env"):
                continue
            yield p

def classify(root, paths):
    names = {p.name for p in paths}
    rels = [p.relative_to(root).as_posix() for p in paths]
    stack = []
    checks = [
        ("Node.js", {"package.json"}), ("Python", {"pyproject.toml","requirements.txt","Pipfile"}),
        ("Java/Maven", {"pom.xml"}), ("Java/Gradle", {"build.gradle","build.gradle.kts"}),
        ("Go", {"go.mod"}), ("Rust", {"Cargo.toml"}), ("PHP", {"composer.json"}),
        ("Flutter/Dart", {"pubspec.yaml"})
    ]
    for label, markers in checks:
        if names & markers: stack.append(label)
    if "vite.config.js" in names or "vite.config.ts" in names: stack.append("Vite")
    if any(n in names for n in ("next.config.js","next.config.ts","next.config.mjs")): stack.append("Next.js")
    if "firebase.json" in names: stack.append("Firebase")
    if any(n in names for n in ("Dockerfile","docker-compose.yml","compose.yaml")): stack.append("Docker")
    return stack or ["Unknown / inspect manually"]

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="command", required=True)
    scan = sub.add_parser("scan", help="Create a read-only repository inventory")
    scan.add_argument("path", type=Path)
    scan.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()
    root = args.path.resolve()
    if not root.is_dir():
        raise SystemExit(f"Not a directory: {root}")
    paths = list(walk(root))
    rels = [p.relative_to(root).as_posix() for p in paths]
    manifests = []
    for p in paths:
        if p.name in MANIFESTS:
            content = safe_read(p)
            item = {"path": p.relative_to(root).as_posix()}
            if p.name == "package.json" and content:
                try:
                    data = json.loads(content)
                    item["name"] = data.get("name")
                    item["scripts"] = data.get("scripts", {})
                    item["dependencies"] = sorted((data.get("dependencies") or {}).keys())
                    item["devDependencies"] = sorted((data.get("devDependencies") or {}).keys())
                except Exception:
                    item["note"] = "Could not parse package.json"
            elif p.name == "pyproject.toml" and content:
                item["project_metadata_excerpt"] = "\n".join(content.splitlines()[:80])
            else:
                item["present"] = True
            manifests.append(item)
    entrypoints = [r for r in rels if Path(r).name in ENTRY_NAMES]
    tests = [r for r in rels if any(h in r.lower() for h in TEST_HINTS) and Path(r).suffix.lower() in {".py",".js",".jsx",".ts",".tsx",".java",".go",".rs"}]
    top_level = sorted(p.name for p in root.iterdir() if p.name not in EXCLUDED_DIRS and not p.name.startswith(".env"))
    report = {
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "root": str(root),
        "file_count": len(paths),
        "top_level": top_level,
        "likely_stack": classify(root, paths),
        "manifests": manifests,
        "entrypoint_candidates": entrypoints[:100],
        "test_file_candidates": tests[:300],
        "directories": sorted({str(Path(r).parent) for r in rels if "/" in r})[:500],
        "notes": [
            "Read-only heuristic inventory; not a full architecture analysis.",
            "Common secret files and dependency/build directories were excluded.",
            "No .env values, private keys, or arbitrary source contents were intentionally read."
        ]
    }
    output = json.dumps(report, indent=2, ensure_ascii=False)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(output + "\n", encoding="utf-8")
        print(f"Report written to: {args.out.resolve()}")
    else:
        print(output)

if __name__ == "__main__":
    main()
