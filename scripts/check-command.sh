#!/bin/bash
# PreToolUse hook on `exec`: block destructive commands.
# stdin: JSON with tool_input.command. Exit 2 = block.

cmd=$(python3 -c 'import sys,json; ti=json.load(sys.stdin).get("tool_input") or {}; print(ti.get("command",""))' 2>/dev/null)

blocked='rm -rf /|rm -rf ~|rm -rf \.|git push --force|git push -f|git reset --hard|git clean -fd|DROP TABLE|DROP DATABASE|mkfs|dd if=|chmod -R 777|sudo rm|>\s*/dev/sd'

if echo "$cmd" | grep -qEi "$blocked"; then
  python3 -c 'import json; print(json.dumps({"decision":"block","reason":"Blocked by policy: destructive or hard-to-reverse command. Ask the user for explicit confirmation and describe exactly what the command does before retrying."}))'
  exit 2
fi
exit 0
