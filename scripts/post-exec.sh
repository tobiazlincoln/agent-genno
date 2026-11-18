#!/bin/bash
# PostToolUse hook on `exec`:
#  1) record the attempt into TASKSTATE
#  2) failure-streak policy: 2 fails -> inject diagnose hint; 3+ -> escalate

state_dir="$DEVIN_PROJECT_DIR/.devin/.state"
mkdir -p "$state_dir"
export STATE_DIR="$state_dir"

payload=$(cat)
echo "$payload" | STATE_DIR="$state_dir" PDIR="$DEVIN_PROJECT_DIR" python3 -c '
import sys, json, os, subprocess
p = json.load(sys.stdin)
ok = p.get("tool_response", {}).get("success", True)
cmd = p.get("tool_input", {}).get("command", "")[:200]
err = (p.get("tool_response", {}).get("error") or "")[:150]

subprocess.run([os.path.join(os.environ["PDIR"], "scripts/taskstate.sh"),
                "record-tool", "exec", "true" if ok else "false",
                cmd + (" | " + err if err else "")])

streak_f = os.path.join(os.environ["STATE_DIR"], "fail-streak")
try:
    prev = int(open(streak_f).read().strip() or 0)
except Exception:
    prev = 0
n = 0 if ok else prev + 1
open(streak_f, "w").write(str(n))

if not ok and n == 2:
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse",
      "additionalContext": "This command has now failed TWICE. Do not retry blindly. Diagnose first: re-read the full error, check your assumptions about paths/state, inspect the actual environment before your next attempt."}}))
elif not ok and n >= 3:
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse",
      "additionalContext": "THREE consecutive failures. Per AGENTS.md section 7: stop retrying. Report to the user what you tried, the error, and your hypothesis — or decompose the task differently."}}))
'
exit 0
