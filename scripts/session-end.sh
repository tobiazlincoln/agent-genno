#!/bin/bash
# SessionEnd hook: append a usage/activity record to storage/usage.log
log="$DEVIN_PROJECT_DIR/storage/usage.log"
mkdir -p "$DEVIN_PROJECT_DIR/storage"

payload=$(cat)
PAYLOAD="$payload" LOG="$log" python3 -c '
import json, sys, os, datetime
try:
    p = json.loads(os.environ.get("PAYLOAD", "{}"))
except Exception:
    p = {}
line = {
    "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "reason": p.get("reason", ""),
    "session_id": p.get("session_id", ""),
}
open(os.environ["LOG"], "a").write(json.dumps(line) + "\n")
'
exit 0
