#!/usr/bin/env python3
"""OSS audit pipeline: seed targets -> fetch -> scan -> store -> triage-ready findings.

Usage:
  audit.py seed-gh "topic:llm stars:>100" --limit 10
  audit.py seed-hf --limit 10
  audit.py scan [--limit N]
  audit.py status
  audit.py findings [--target ID]
"""

import argparse, json, os, re, shutil, sqlite3, subprocess, sys, tempfile, urllib.parse, urllib.request
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, "storage", "audit.db")
WORK = os.path.join(ROOT, "storage", "workdir")
VENV = os.path.join(ROOT, "pipeline", ".venv", "bin")
HF_MAX_FILE_BYTES = 50 * 1024 * 1024  # skip model blobs > 50MB

SCHEMA = """
CREATE TABLE IF NOT EXISTS targets (
  id INTEGER PRIMARY KEY, source TEXT NOT NULL, ref TEXT UNIQUE NOT NULL,
  url TEXT, name TEXT, meta TEXT, status TEXT DEFAULT 'pending',
  created_at TEXT DEFAULT (datetime('now')));
CREATE TABLE IF NOT EXISTS scans (
  id INTEGER PRIMARY KEY, target_id INTEGER REFERENCES targets(id),
  scanner TEXT, started TEXT, finished TEXT, ok INTEGER, raw TEXT);
CREATE TABLE IF NOT EXISTS findings (
  id INTEGER PRIMARY KEY, target_id INTEGER REFERENCES targets(id),
  scanner TEXT, severity TEXT, title TEXT, detail TEXT, location TEXT);
"""

def db():
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    c = sqlite3.connect(DB); c.executescript(SCHEMA); return c

def sh(cmd, cwd=None, timeout=600):
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    return p.returncode, p.stdout, p.stderr

def add_target(source, ref, url, name, meta):
    c = db()
    c.execute("INSERT OR IGNORE INTO targets (source, ref, url, name, meta) VALUES (?,?,?,?,?)",
              (source, ref, url, name, json.dumps(meta)))
    c.commit()

def seed_gh(query, limit):
    rc, out, err = sh(["gh", "api", f"search/repositories?q={urllib.parse.quote(query)}&per_page={limit}"])
    if rc: sys.exit(f"gh api failed: {err}")
    for r in json.loads(out).get("items", []):
        add_target("github", f"gh:{r['full_name']}", r["html_url"], r["full_name"],
                   {"stars": r["stargazers_count"], "lang": r["language"],
                    "archived": r["archived"], "pushed_at": r["pushed_at"],
                    "license": (r.get("license") or {}).get("spdx_id")})
    print(f"seeded {json.loads(out)['total_count']} candidates, queued {limit}")

def seed_hf(limit):
    url = f"https://huggingface.co/api/models?sort=downloads&direction=-1&limit={limit}"
    for m in json.loads(urllib.request.urlopen(url, timeout=30).read()):
        mid = m["id"]
        add_target("hf", f"hf:{mid}", f"https://huggingface.co/{mid}", mid,
                   {"downloads": m.get("downloads"), "likes": m.get("likes"),
                    "pipeline_tag": m.get("pipeline_tag"), "tags": m.get("tags", [])[:10]})
    print(f"seeded {limit} hf models")

def fetch_github(ref, dest):
    return sh(["gh", "repo", "clone", ref[3:], dest, "--", "--depth", "1"])[0] == 0

def fetch_hf(ref, dest):
    from huggingface_hub import HfApi, hf_hub_download
    api = HfApi()
    repo_id = ref[3:]
    files = api.list_repo_files(repo_id)
    picked = [f for f in files if re.search(r"\.(pkl|pickle|pt|bin|ckpt|joblib|npy|json|txt|md)$", f, re.I)][:20]
    try:
        info = api.repo_info(repo_id, files_metadata=True)
        sizes = {s.rfilename: (s.size or 0) for s in info.siblings}
    except Exception:
        sizes = {}
    got = []
    for f in picked:
        try:
            size = sizes.get(f, 0)
            if size and size > HF_MAX_FILE_BYTES:
                continue
            p = hf_hub_download(ref[3:], f, local_dir=dest)
            got.append(p)
        except Exception:
            pass
    return bool(got) or True  # metadata-only scan still useful

SCANNERS = [
    ("bandit",     lambda d: [os.path.join(VENV, "bandit"), "-r", d, "-f", "json", "-q"]),
    ("pip-audit",  lambda d: [os.path.join(VENV, "pip-audit"), "-r", "requirements.txt", "-f", "json"]
                             if os.path.exists(os.path.join(d, "requirements.txt")) else None),
    ("picklescan", lambda d: [os.path.join(VENV, "picklescan"), "-p", d] if has_model_files(d) else None),
    ("osv-scanner",lambda d: ["osv-scanner", "-r", "--format", "json", d] if shutil.which("osv-scanner") else None),
    ("gitleaks",   lambda d: ["gitleaks", "detect", "-s", d, "--no-git", "-f", "json"] if shutil.which("gitleaks") else None),
]

def has_model_files(d):
    for _, _, fs in os.walk(d):
        if any(re.search(r"\.(pkl|pickle|pt|bin|ckpt|joblib)$", f, re.I) for f in fs):
            return True
    return False

def norm_findings(scanner, rc, out, err):
    """Normalize scanner output -> [(severity, title, detail, location)]"""
    f = []
    if scanner == "bandit" and out.strip():
        try:
            for r in json.loads(out).get("results", []):
                f.append((r["issue_severity"], r["issue_text"], r["test_name"],
                          f"{r['filename']}:{r['line_number']}"))
        except Exception:
            f.append(("INFO", "bandit-unparsed", out[:500], ""))
    elif scanner == "pip-audit" and out.strip():
        try:
            for dep in json.loads(out).get("dependencies", []):
                for v in dep.get("vulns", []):
                    f.append(("HIGH", v["id"], v.get("description", "")[:300], dep["name"]))
        except Exception:
            f.append(("INFO", "pip-audit-unparsed", out[:500], ""))
    elif scanner == "picklescan":
        if "dangerous" in (out + err).lower() or rc != 0:
            f.append(("CRITICAL", "picklescan-dangerous", (out + err)[:500], ""))
    elif scanner in ("osv-scanner", "gitleaks") and out.strip():
        f.append(("MEDIUM", f"{scanner}-findings", out[:500], ""))
    return f

def scan(limit):
    c = db()
    rows = c.execute("SELECT id, ref, name FROM targets WHERE status='pending' LIMIT ?", (limit,)).fetchall()
    os.makedirs(WORK, exist_ok=True)
    for tid, ref, name in rows:
        dest = os.path.join(WORK, re.sub(r"[^\w.-]", "_", ref))
        shutil.rmtree(dest, ignore_errors=True); os.makedirs(dest, exist_ok=True)
        print(f"[scan] {ref}")
        ok = fetch_github(ref, dest) if ref.startswith("gh:") else fetch_hf(ref, dest)
        if not ok:
            c.execute("UPDATE targets SET status='fetch-failed' WHERE id=?", (tid,)); c.commit(); continue
        n = 0
        for scanner, cmdfn in SCANNERS:
            cmd = cmdfn(dest)
            if not cmd: continue
            t0 = datetime.now(timezone.utc).isoformat()
            try:
                rc, out, err = sh(cmd, timeout=300)
            except Exception as e:
                rc, out, err = 1, "", str(e)
            c.execute("INSERT INTO scans (target_id, scanner, started, finished, ok, raw) VALUES (?,?,?,?,?,?)",
                      (tid, scanner, t0, datetime.now(timezone.utc).isoformat(),
                       1 if rc == 0 else 0, (out + err)[:20000]))
            for sev, title, det, loc in norm_findings(scanner, rc, out, err):
                c.execute("INSERT INTO findings (target_id, scanner, severity, title, detail, location) VALUES (?,?,?,?,?,?)",
                          (tid, scanner, sev, title, det, loc)); n += 1
            c.commit()
        c.execute("UPDATE targets SET status='scanned' WHERE id=?", (tid,)); c.commit()
        shutil.rmtree(dest, ignore_errors=True)
        print(f"  -> {n} findings")

def status():
    c = db()
    for row in c.execute("SELECT status, COUNT(*) FROM targets GROUP BY status"):
        print(f"targets {row[0]:12} {row[1]}")
    for row in c.execute("SELECT severity, COUNT(*) FROM findings GROUP BY severity ORDER BY 2 DESC"):
        print(f"findings {row[0]:10} {row[1]}")

def findings(target=None):
    c = db()
    q = """SELECT t.ref, f.severity, f.scanner, f.title, f.detail, f.location
           FROM findings f JOIN targets t ON t.id=f.target_id"""
    rows = c.execute(q + (" WHERE t.id=?" if target else ""), (target,) if target else ()).fetchall()
    for r in rows: print(f"{r[0]:40} [{r[1]:8}] {r[2]}: {r[3]} | {r[5]}\n     {r[4][:120]}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("seed-gh"); p.add_argument("query"); p.add_argument("--limit", type=int, default=10)
    p = sp.add_parser("seed-hf"); p.add_argument("--limit", type=int, default=10)
    p = sp.add_parser("scan"); p.add_argument("--limit", type=int, default=5)
    sp.add_parser("status")
    p = sp.add_parser("findings"); p.add_argument("--target", type=int)
    a = ap.parse_args()
    {"seed-gh": lambda: seed_gh(a.query, a.limit), "seed-hf": lambda: seed_hf(a.limit),
     "scan": lambda: scan(a.limit), "status": status, "findings": lambda: findings(a.target)}[a.cmd]()
