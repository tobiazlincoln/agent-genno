#!/bin/bash
# PostToolUse hook on edit/write/apply_patch:
#  1) record the edited file into .devin/.state/pending-edits
#  2) inject a reminder that verification is now required

state_dir="$DEVIN_PROJECT_DIR/.devin/.state"
mkdir -p "$state_dir"
export STATE_DIR="$state_dir"

cat | python3 -c '
import sys, json, os
payload = json.load(sys.stdin)
ti = payload.get("tool_input", {})
path = ti.get("file_path") or ti.get("notebook_path") or "unknown"
if payload.get("tool_response", {}).get("success", True):
    with open(os.path.join(os.environ["STATE_DIR"], "pending-edits"), "a") as f:
        f.write(path + "\n")
'

cat <<'EOF'
{"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": "Edit recorded. Verification is now REQUIRED before you may finish: run the project checks (scripts/verify.sh or the test suite) and report actual output. Claiming completion without a passing verification violates AGENTS.md section 2."}}
EOF
exit 0
