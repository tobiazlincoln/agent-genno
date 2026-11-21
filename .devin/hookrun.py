#!/usr/bin/env python3
"""Self-healing hook dispatcher.

hooks.v1.json calls:  python3 "$DEVIN_PROJECT_DIR/.devin/hookrun.py" <hook>
The hook scripts may live anywhere in the project; this file finds them, so
moving or renaming the scripts folder never produces "exit 127" again.

  hookrun.py <hook>         run a hook (stdin = event JSON)
  hookrun.py doctor         check wiring + smoke-test the guard (exit 1 on problems)
  hookrun.py doctor --fix   also rewrite hooks.v1.json and the compat symlink
"""
import json, os, re, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
STATE = os.path.join(ROOT, ".devin", ".state")
CACHE = os.path.join(STATE, "scripts-dir")
LOG = os.path.join(STATE, "hook-health.log")
HOOKS_FILE = os.path.join(ROOT, ".devin", "hooks.v1.json")
COMPAT = os.path.join(ROOT, "scripts")
MARKERS = ("check-command.sh", "taskstate.sh")
SKIP = {".git", "node_modules", ".venv", "lib", "out", "cache", "dist", "__pycache__", "storage"}
HOOKS = {
    "session-start": ("SessionStart", None, None),
    "session-end": ("SessionEnd", None, None),
    "prompt-context": ("UserPromptSubmit", None, 5),
    "check-command": ("PreToolUse", "exec", 10),
    "post-edit": ("PostToolUse", "^(edit|write|apply_patch|notebook_edit)$", 10),
    "post-exec": ("PostToolUse", "^exec$", 10),
    "stop-verify": ("Stop", None, 60),
}
BLOCKED = (r"rm -rf /|rm -rf ~|rm -rf \.|git push --force|git push -f|git reset --hard|git clean -fd|"
           r"DROP TABLE|DROP DATABASE|mkfs|dd if=|chmod -R 777|sudo rm|>\s*/dev/sd")
BLOCK_MSG = ("Blocked by policy: destructive or hard-to-reverse command. Ask the user for explicit "
             "confirmation and describe exactly what the command does before retrying.")


def log(msg):
    try:
        os.makedirs(STATE, exist_ok=True)
        with open(LOG, "a") as f:
            f.write(f"{time.strftime('%Y-%m-%dT%H:%M:%S')} {msg}\n")
    except OSError:
        pass


def valid(d):
    return bool(d) and all(os.path.isfile(os.path.join(d, m)) for m in MARKERS)


def find_scripts():
    cached = None
    try:
        cached = open(CACHE).read().strip()
    except OSError:
        pass
    for d in (os.environ.get("GLM_SCRIPTS_DIR"), cached,
              os.path.join(ROOT, "GLMAGENT DATA", "scripts"), COMPAT):
        if valid(d):
            return remember(d, cached)
    for cur, dirs, files in os.walk(ROOT):
        depth = cur[len(ROOT):].count(os.sep)
        dirs[:] = [] if depth >= 3 else [x for x in dirs if x not in SKIP]
        if all(m in files for m in MARKERS):
            log(f"relocated scripts dir -> {cur}")
            return remember(cur, cached)
    return None


def remember(d, cached):
    d = os.path.realpath(d)
    if d != cached:
        try:
            os.makedirs(STATE, exist_ok=True)
            open(CACHE, "w").write(d)
        except OSError:
            pass
    return d


def builtin_guard(payload):
    try:
        cmd = (json.loads(payload or b"{}").get("tool_input") or {}).get("command", "")
    except ValueError:
        cmd = ""
    if re.search(BLOCKED, cmd, re.I):
        print(json.dumps({"decision": "block", "reason": BLOCK_MSG}))
        return 2
    return 0


def run(hook, payload):
    sdir = find_scripts()
    script = os.path.join(sdir, hook + ".sh") if sdir else None
    if not script or not os.path.isfile(script):
        log(f"DEGRADED {hook}: script not found (scripts dir: {sdir})")
        if hook == "session-start":
            print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext":
                  "WARNING: hook scripts were not found; only the built-in destructive-command guard is "
                  "active. Run: python3 .devin/hookrun.py doctor --fix"}}))
        return builtin_guard(payload) if hook == "check-command" else 0
    try:
        p = subprocess.run(["/bin/bash", script], input=payload, stdout=subprocess.PIPE,
                           env={**os.environ, "DEVIN_PROJECT_DIR": ROOT})
    except OSError as e:
        log(f"DEGRADED {hook}: {e}")
        return builtin_guard(payload) if hook == "check-command" else 0
    sys.stdout.buffer.write(p.stdout)
    if p.returncode in (0, 2):
        return p.returncode
    log(f"DEGRADED {hook}: script exited {p.returncode}")
    return builtin_guard(payload) if hook == "check-command" else 0


def wanted_config():
    cfg = {}
    for hook, (event, matcher, timeout) in HOOKS.items():
        h = {"type": "command", "command": f'python3 "$DEVIN_PROJECT_DIR/.devin/hookrun.py" {hook}'}
        if timeout:
            h["timeout"] = timeout
        entry = {"hooks": [h]}
        if matcher:
            entry = {"matcher": matcher, **entry}
        cfg.setdefault(event, []).append(entry)
    return cfg


def doctor(fix):
    problems = []
    sdir = find_scripts()
    print(f"project root : {ROOT}\nscripts dir  : {sdir or 'NOT FOUND'}")
    for hook in HOOKS:
        ok = bool(sdir) and os.path.isfile(os.path.join(sdir, hook + ".sh"))
        print(f"  {'ok     ' if ok else 'MISSING'} {hook}.sh")
        if not ok:
            problems.append(f"missing script {hook}.sh")

    try:
        current = json.load(open(HOOKS_FILE))
    except (OSError, ValueError) as e:
        current = None
        print(f"hooks.v1.json: unreadable ({e})")
    if current != wanted_config():
        if fix:
            json.dump(wanted_config(), open(HOOKS_FILE, "w"), indent=2)
            open(HOOKS_FILE, "a").write("\n")
            print("hooks.v1.json: REWRITTEN to dispatcher form")
        else:
            problems.append("hooks.v1.json does not match the dispatcher wiring")
    else:
        print("hooks.v1.json: ok")

    # Sessions started before a move keep calling $DEVIN_PROJECT_DIR/scripts/*.sh
    if sdir and os.path.realpath(COMPAT) != sdir:
        if fix and (os.path.islink(COMPAT) or not os.path.lexists(COMPAT)):
            if os.path.islink(COMPAT):
                os.remove(COMPAT)
            os.symlink(os.path.relpath(sdir, ROOT), COMPAT)
            print(f"compat link  : CREATED scripts -> {os.path.relpath(sdir, ROOT)}")
        else:
            problems.append("legacy path scripts/ does not reach the scripts dir (old sessions will fail)")
    elif sdir:
        print("compat link  : ok")

    me = [sys.executable, os.path.realpath(__file__), "check-command"]
    for label, cmd, want in (("benign", "ls -la", 0), ("destructive", "rm -rf /", 2)):
        rc = subprocess.run(me, input=json.dumps({"tool_input": {"command": cmd}}).encode(),
                            stdout=subprocess.DEVNULL).returncode
        print(f"guard {label:11}: exit {rc} (want {want})")
        if rc != want:
            problems.append(f"guard smoke test failed for {label} command")

    for p in problems:
        print("PROBLEM:", p)
    print("RESULT:", "FAIL" if problems else "HEALTHY")
    return 1 if problems else 0


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else ""
    if arg == "doctor":
        sys.exit(doctor("--fix" in sys.argv))
    if arg not in HOOKS:
        sys.exit(f"usage: hookrun.py <{'|'.join(HOOKS)}|doctor [--fix]>")
    payload = b"" if sys.stdin.isatty() else sys.stdin.buffer.read()
    try:
        sys.exit(run(arg, payload))
    except Exception as e:  # a hook must never die with a stray exit code
        log(f"DEGRADED {arg}: dispatcher error {e!r}")
        sys.exit(builtin_guard(payload) if arg == "check-command" else 0)
