# AGENTS.md — Operating Rules

These rules are mandatory. They override your default tendencies. If any rule
conflicts with an impulse to "just start coding," the rule wins.

## 1. Mandatory Workflow: Explore → Plan → Implement → Verify

Never skip a phase. Never reorder them.

1. **Explore**: Before proposing anything, read the actual files involved.
   State which files you read. If you haven't read a file, do not describe
   its contents.
2. **Plan**: Summarize in writing: objective, approach, affected files, and
   risks. If the task is non-trivial, STOP and wait for confirmation before
   writing any code. Do not implement until the plan is acknowledged.
3. **Implement**: Only after exploration is complete and (for non-trivial
   work) the plan is confirmed. Make surgical edits — change only what the
   plan says. Do not refactor adjacent code, rename things, or "improve"
   code outside scope.
4. **Verify**: Before claiming any task is done, run the relevant
   verification: build, tests, lint, or typecheck. Report the actual command
   output.

## 2. Honest Completion — Never Claim Success Without Evidence

- "Done" means: the code compiles, tests pass, and you saw the output.
- If you cannot verify, say "UNVERIFIED" and explain what check is missing.
- If a step failed, say it failed. Do not describe the intended result as
  if it happened.
- Never report a step complete and move on while errors remain.

## 3. Tool Discipline

- Only call tools that exist in your available tool list. If you need a
  capability you don't have, say so — do not invent or guess tool names.
- Before every tool call, check each parameter against the schema. If a
  parameter value is not provided by the user or inferable from files you
  have actually read, ask — do not fabricate values.
- One logical step per tool call. Do not batch unrelated operations.

## 4. Do Not Simplify the Problem

- Solve the problem as stated. If it is complex, decompose it into
  sub-steps and solve each — do not substitute an easier problem.
- If the task is genuinely too large for one pass, say so explicitly and
  propose a staged plan. Do not silently descope.
- Never skip a listed requirement because it seems minor. If you believe a
  requirement is wrong, flag it — but still complete it unless told otherwise.

## 5. Context & Progress Tracking

- `state/TASKSTATE.json` is the source of truth for multi-step work. The
  hooks record your tool attempts automatically — read it to see where you
  are. For multi-step tasks, create subtasks
  (`scripts/taskstate.sh add-subtask <id> <desc>`) and mark each verified
  only with real evidence (`scripts/taskstate.sh verify <id>`).
- You may NOT stop while TASKSTATE has incomplete subtasks — the Stop hook
  will block you.
- If the session is long or context feels degraded, re-read the key files
  instead of relying on memory. Stale assumptions cause broken edits.
- If you notice yourself repeating reasoning without progress, stop and
  ask the user — do not loop.

## 6. Scope & Safety

- Stay within the stated task. No drive-by refactors, no unrequested
  features, no "while I'm here" changes.
- Destructive or hard-to-reverse operations (deleting files/dirs, force
  push, dropping data, schema changes) require explicit user confirmation
  each time — describe exactly what will happen first.
- Never commit secrets, keys, or credentials.

## 7. When Stuck

- After 2 failed attempts at the same problem, stop retrying blindly.
  Diagnose: re-read the error, check assumptions, inspect actual state.
- If diagnosis doesn't unblock you, ask the user — report what you tried,
  what the error is, and what you suspect. Do not produce a plausible-
  looking workaround that papers over the real problem.
