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

# Run automated integrity and synchronization validator
try:
    import subprocess
    res = subprocess.run([sys.executable, str(ROOT/"scripts/verify_integrity.py")], capture_output=True, text=True)
    if res.returncode != 0:
        errors.append(f"Integrity check failed:\n{res.stdout}\n{res.stderr}")
    
    # Run Memory Engine test suite
    mem_res = subprocess.run([sys.executable, str(ROOT/"scripts/test_memory_engine.py")], capture_output=True, text=True)
    if mem_res.returncode != 0:
        errors.append(f"Memory Engine tests failed:\n{mem_res.stdout}\n{mem_res.stderr}")
    
    # Run Continuous Learning test suite
    learn_res = subprocess.run([sys.executable, str(ROOT/"scripts/test_learn.py")], capture_output=True, text=True)
    if learn_res.returncode != 0:
        errors.append(f"Continuous Learning tests failed:\n{learn_res.stdout}\n{learn_res.stderr}")
    
    # Run Quality Engine test suite
    qual_res = subprocess.run([sys.executable, str(ROOT/"scripts/test_quality_engine.py")], capture_output=True, text=True)
    if qual_res.returncode != 0:
        errors.append(f"Quality Engine tests failed:\n{qual_res.stdout}\n{qual_res.stderr}")
    
    # Run Safety Gate hook test suite
    gate_res = subprocess.run([sys.executable, str(ROOT/"scripts/test_safety_gate.py")], capture_output=True, text=True)
    if gate_res.returncode != 0:
        errors.append(f"Safety Gate tests failed:\n{gate_res.stdout}\n{gate_res.stderr}")
    
    # Run Security Scan regression test suite
    sec_res = subprocess.run([sys.executable, str(ROOT/"scripts/test_security_scan.py")], capture_output=True, text=True)
    if sec_res.returncode != 0:
        errors.append(f"Security Scan regression tests failed:\n{sec_res.stdout}\n{sec_res.stderr}")
    
    # Run Project Intelligence test suite
    intel_res = subprocess.run([sys.executable, str(ROOT/"scripts/test_project_intel.py")], capture_output=True, text=True)
    if intel_res.returncode != 0:
        errors.append(f"Project Intelligence tests failed:\n{intel_res.stdout}\n{intel_res.stderr}")
    
    # Run Context Router test suite
    router_res = subprocess.run([sys.executable, str(ROOT/"scripts/test_context_router.py")], capture_output=True, text=True)
    if router_res.returncode != 0:
        errors.append(f"Context Router tests failed:\n{router_res.stdout}\n{router_res.stderr}")
    
    # Run Evaluation Benchmark Suite
    eval_res = subprocess.run([sys.executable, str(ROOT/"scripts/run_eval.py")], capture_output=True, text=True)
    if eval_res.returncode != 0:
        errors.append(f"Evaluation benchmark failed:\n{eval_res.stdout}\n{eval_res.stderr}")
except Exception as e:
    errors.append(f"Could not execute sub-test suites: {e}")

if errors:
    print("SELF TEST FAILED")
    print("\n".join(errors))
    sys.exit(1)
print("SELF TEST PASSED")
print(f"Agents: {len(list((ROOT/'agents').glob('*.md')))}")
print(f"Skills: {len(list((ROOT/'skills').glob('*/SKILL.md')))}")
