#!/bin/bash
# Stop hook: agent may not stop while
#   a) there are unverified edits (run verify.sh), or
#   b) TASKSTATE has incomplete subtasks.
# Blocks up to 3x, then allows (safety valve).

state_dir="$DEVIN_PROJECT_DIR/.devin/.state"
pending="$state_dir/pending-edits"
counter="$state_dir/stop-blocks"
ts="$DEVIN_PROJECT_DIR/scripts/taskstate.sh"

cat > /dev/null  # drain stdin

incomplete=$("$ts" incomplete 2>/dev/null)
has_incomplete=$?

# nothing pending -> allow
if [ ! -s "$pending" ] && [ "$has_incomplete" -ne 0 ]; then
  exit 0
fi

# safety valve: never block more than 3 times
n=$(cat "$counter" 2>/dev/null || echo 0)
if [ "$n" -ge 3 ]; then
  exit 0
fi

reason=""

if [ "$has_incomplete" -eq 0 ]; then
  reason="Task state shows INCOMPLETE subtasks: $incomplete. Finish them (or explicitly mark them blocked and explain why to the user) before stopping."
fi

if [ -s "$pending" ]; then
  if "$DEVIN_PROJECT_DIR/scripts/verify.sh" > "$state_dir/last-verify.out" 2>&1; then
    rm -f "$pending"
    # git checkpoint on verified edits — makes rollback cheap
    if git -C "$DEVIN_PROJECT_DIR" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
      git -C "$DEVIN_PROJECT_DIR" add -A >/dev/null 2>&1
      git -C "$DEVIN_PROJECT_DIR" commit -q -m "checkpoint: verified edits" >/dev/null 2>&1
    fi
  else
    vfail=$(tail -c 1500 "$state_dir/last-verify.out")
    reason="${reason:+$reason\n\n}Verification FAILED — fix the failures, re-run checks, then finish.\n\n$vfail"
  fi
fi

if [ -z "$reason" ]; then
  rm -f "$counter"
  exit 0
fi

echo $((n + 1)) > "$counter"
printf '%s' "$reason" | python3 -c '
import sys, json
print(json.dumps({"decision": "block", "reason": sys.stdin.read()}))
'
exit 0
