"""Narrow opt-in Antigravity PreToolUse gate. Reads hook JSON from stdin."""
import json
import re
import sys

BLOCK_PATTERNS = [
    r"(?i)\bformat\s+[a-z]:",
    r"(?i)\bdiskpart\b",
    r"(?i)\bshutdown\s+/[sr]",
    r"(?i)\bRemove-Item\b.*-Recurse.*-Force",
    r"(?i)\bdel\s+/[sq]",
    r"(?i)\brmdir\s+/[sq]",
    r"(?i)\brm\s+-rf\s+/(?:\s|$)",
    r"(?i)\bdrop\s+database\b",
    r"(?i)\bterraform\s+destroy\b",
    r"(?i)\bkubectl\s+delete\s+(?:namespace|ns)\b",
]

def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        print(json.dumps({"decision": "ask", "reason": "Aether safety gate could not parse hook input; require manual review."}))
        return
    call = payload.get("toolCall") or {}
    args = call.get("args") or {}
    command = str(args.get("CommandLine") or args.get("command") or "")
    for pattern in BLOCK_PATTERNS:
        if re.search(pattern, command):
            print(json.dumps({
                "decision": "deny",
                "reason": "Aether safety gate blocked a known destructive command pattern. Review the operation and obtain explicit human authorization through a safer, controlled process."
            }))
            return
    print(json.dumps({"decision": "allow"}))

if __name__ == "__main__":
    main()
