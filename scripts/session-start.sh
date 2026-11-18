#!/bin/bash
# SessionStart hook: reset per-session verification state and task state.
rm -f "$DEVIN_PROJECT_DIR/.devin/.state/pending-edits" \
      "$DEVIN_PROJECT_DIR/.devin/.state/stop-blocks" \
      "$DEVIN_PROJECT_DIR/.devin/.state/last-verify.out" \
      "$DEVIN_PROJECT_DIR/.devin/.state/fail-streak"
"$DEVIN_PROJECT_DIR/scripts/taskstate.sh" init
exit 0
