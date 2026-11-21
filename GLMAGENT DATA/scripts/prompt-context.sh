#!/bin/bash
# UserPromptSubmit hook: inject a pointer to the relevant local cache (BRAIN/).
brain="$DEVIN_PROJECT_DIR/tools/brain.py"
[ -f "$brain" ] || exit 0
exec python3 "$brain" hook
