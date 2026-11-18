#!/bin/bash
# Manage state/TASKSTATE.json — called by hooks and usable by the agent.
#   taskstate.sh init
#   taskstate.sh record-tool <tool_name> <ok> <summary>
#   taskstate.sh add-subtask <id> <desc>
#   taskstate.sh set-status <id> <status>
#   taskstate.sh verify <id>
#   taskstate.sh incomplete   -> prints unfinished subtask ids (exit 1 if none)

STATE="$DEVIN_PROJECT_DIR/state/TASKSTATE.json"
PY="${DEVIN_PROJECT_DIR}/pipeline/.venv/bin/python3"
[ -x "$PY" ] || PY=python3

mkdir -p "$DEVIN_PROJECT_DIR/state"
[ -f "$STATE" ] || printf '{"goal":"","subtasks":[],"attempts":[],"blockers":[],"verified":[]}' > "$STATE"

case "$1" in
  init)
    printf '{"goal":"","subtasks":[],"attempts":[],"blockers":[],"verified":[]}' > "$STATE"
    ;;
  record-tool)
    "$PY" - "$STATE" "$2" "$3" "$4" <<'EOF'
import json, sys
p, tool, ok, summ = sys.argv[1], sys.argv[2], sys.argv[3] == "true", sys.argv[4][:200]
s = json.load(open(p))
s["attempts"].append({"tool": tool, "ok": ok, "summary": summ})
s["attempts"] = s["attempts"][-200:]
json.dump(s, open(p, "w"), indent=1)
EOF
    ;;
  add-subtask)
    "$PY" - "$STATE" "$2" "$3" <<'EOF'
import json, sys
s = json.load(open(sys.argv[1]))
s["subtasks"].append({"id": sys.argv[2], "desc": sys.argv[3], "status": "pending"})
json.dump(s, open(sys.argv[1], "w"), indent=1)
EOF
    ;;
  set-status)
    "$PY" - "$STATE" "$2" "$3" <<'EOF'
import json, sys
s = json.load(open(sys.argv[1]))
for t in s["subtasks"]:
    if t["id"] == sys.argv[2]: t["status"] = sys.argv[3]
json.dump(s, open(sys.argv[1], "w"), indent=1)
EOF
    ;;
  verify)
    "$PY" - "$STATE" "$2" <<'EOF'
import json, sys
s = json.load(open(sys.argv[1]))
s["verified"].append(sys.argv[2])
for t in s["subtasks"]:
    if t["id"] == sys.argv[2]: t["status"] = "done"
json.dump(s, open(sys.argv[1], "w"), indent=1)
EOF
    ;;
  incomplete)
    "$PY" - "$STATE" <<'EOF'
import json, sys
s = json.load(open(sys.argv[1]))
inc = [t["id"] for t in s["subtasks"] if t["status"] != "done"]
print(",".join(inc))
sys.exit(0 if inc else 1)
EOF
    ;;
  *) echo "unknown command: $1" >&2; exit 1 ;;
esac
