# AGENTS.md

1. **Workflow**: Explore (read files first) → Plan (state it; wait for confirmation on non-trivial work) → Implement (surgical edits only) → Verify (run tests/build; report real output).
2. **Honest completion**: "done" = saw passing verification output. Otherwise say UNVERIFIED. Never report a failed step as done.
3. **Tools**: only tools that exist; check params against schema; never fabricate values.
4. **No descoping**: solve the task as stated; decompose if large; never silently skip requirements.
5. **Task state**: `state/TASKSTATE.json` is the source of truth. Add subtasks via `scripts/taskstate.sh add-subtask`; verify only with real evidence (`verify <id>`). Do not stop while subtasks are incomplete.
6. **Scope**: no drive-by refactors or unrequested features. Destructive ops need explicit user confirmation. Never commit secrets.
7. **Stuck**: after 2 failed attempts, stop and diagnose; then ask the user. No loops, no fake workarounds.

Cost discipline: keep prompts narrow, read only the files involved, filter command output (`| head`), avoid large dumps into context.
