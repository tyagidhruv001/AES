# Aether Security Architecture Specification

**Version:** 1.1.0  
**Status:** Canonical Security Specification  
**Governing Standard:** Aether Constitution, Threat Model & Agent Tool Matrix  

---

## 1. Security Principles & Threat Philosophy

AI engineering systems operate with privileged access to source code, execution environments, and developer tools. Without strict defense-in-depth, AI agents are susceptible to prompt injection, supply chain compromise, accidental data destruction, and credential exfiltration.

The Aether Engineering System (AES) enforces a **zero-implicit-trust security model**:
1. **Untrusted Inputs:** All repository files, prompt injections, issues, pull requests, dependencies, and memory records are treated as untrusted data until verified.
2. **Deterministic Sandbox Isolation:** Subagents execute under `commandExecutionPolicy: sandbox` by default.
3. **Least-Privilege Tool Assignment:** 8 of 9 agents have zero file-write tools. Write access is restricted exclusively to `senior-developer`.
4. **PreToolUse Destructive Command Gate:** Opt-in safety gate intercepts shell commands and denies known catastrophic operations.
5. **Redaction by Default:** Secrets, credentials, private keys, and tokens are redacted before display in diffs, logs, or reports.

---

## 2. Threat Matrix & Defense-in-Depth Mitigations

| Threat Vector | Attack Scenario | Aether Defense Layer | Mitigation Mechanism |
|---|---|---|---|
| **Prompt Injection** | Malicious comment in source code instructing agent to ignore rules and exfiltrate files | Multi-layered parsing (`security_scan.py`, `memory_engine.py`, `learn.py`) | Injection patterns detected; flagged as untrusted; execution refused |
| **Credential Leakage** | Hardcoded API keys or credentials committed to repository or logged in reports | Pre-commit scanning & output sanitization | Regex & AST-based secret scanning; automatic `[REDACTED]` masking on output |
| **Destructive Command** | Agent generating `rm -rf /`, formatting disks, or dropping databases | PreToolUse Safety Hook (`safety_gate.py`) | Regex blocklist triggers immediate `deny` or `ask` decision before tool execution |
| **Confused Deputy** | Over-permissioned read-only agent tricked into modifying configuration | Mechanical Tool Boundaries | Read-only roles lack `write_to_file` and `replace_file_content` tools entirely |
| **Memory Poisoning** | Malicious memory entries injected to alter future agent behavior | Supervised Learning Pipeline | Human approval gate mandatory; all memory queries treated as data, never instructions |
| **Scope Creep / Race Condition** | Concurrent subagents editing overlapping files | Single-Writer Discipline & Diff Audit | Exactly one writer permitted per file scope; diff audit rejects unassigned file edits |

---

## 3. PreToolUse Safety Gate Hook Specification

The Aether Safety Gate hook (`adapters/antigravity/hooks/safety_gate.py`) intercepts every `run_command` invocation before execution:

### Blocklist Patterns:
- Disk formatting: `format [a-z]:`, `diskpart`
- OS shutdowns: `shutdown /[sr]`
- Destructive file deletion: `Remove-Item.*-Recurse.*-Force`, `del /[sq]`, `rmdir /[sq]`, `rm -rf /`
- Database destruction: `drop database`
- Cloud destruction: `terraform destroy`, `kubectl delete (namespace|ns)`

### Decision Outcomes:
- **`allow`:** Command passed validation. Proceed with execution.
- **`deny`:** Command matched destructive pattern. Execution blocked immediately.
- **`ask`:** Input unparseable or ambiguous. Require explicit human confirmation.

---

## 4. Multi-Layered Security Scanner Specification

The Aether Security Scanner (`scripts/security_scan.py`) provides heuristic detection:

| Rule Category | Scope | Severity | Detection Heuristic |
|---|---|---|---|
| **Prompt Injection** | Agent files, prompts, YAML/JSON configs (`.md`, `.json`, `.yaml`, `.yml`, `.toml`) | **HIGH** | Instruction override phrases targeting previous instructions, system prompts, or secret exfiltration |
| **Credential Literals** | All text files (`.py`, `.js`, `.ts`, `.env`, `.json`, `.yaml`, etc.) | **HIGH** | `(api_key\|secret\|password\|token) = "..."` (values masked with `[REDACTED]`) |
| **Unsafe Policies** | Agent YAML frontmatter | **MEDIUM** | Unrestricted command execution policies (`yolo` or `unrestricted`) |
| **Unsafe Write Tools** | Agent YAML frontmatter | **MEDIUM** | Write tools enabled on non-developer roles |
| **Permission Overrides** | Config & hook files | **MEDIUM** | Direct permission bypass hooks (`auto-approve` or unconditional grants) |
| **Secret-like Files** | File names on disk | **HIGH** | `.env`, `.env.*`, `id_rsa`, `id_ed25519` (presence flagged, contents NOT read) |

### Self-Exclusion & False-Positive Elimination:
The scanner resolves `Path(__file__).resolve()` and skips its own implementation code. Python source code is excluded from prompt-injection and permission-override rules, preserving broad credential scanning while preventing self-referential false positives.
