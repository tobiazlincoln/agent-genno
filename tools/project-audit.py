#!/usr/bin/env python3
"""project-audit — deterministic, evidence-first project investigator (any project, any stack).

Driven by a JSON config (spec project-audit/1). For every dimension the config asks about,
the tool runs concrete checks (files, grep, shell commands, HTTP, JSON-RPC/onchain, GitHub,
HuggingFace, package registries, Docker) and writes a report with a verdict per feature:

    WORKS      every check passed, evidence captured
    BROKEN     a check failed (evidence shows why)
    UNVERIFIED no executable check exists / check skipped / manual-only judgment
    N/A        expected artefact not present in this project

Absolute mode rules (not negotiable):
  - a verdict NEVER comes from assumption; it comes from captured output
  - anything not checkable is UNVERIFIED, never "probably fine"
  - raw evidence is cached to disk (TTL per config) so re-runs cost nothing
  - destructive commands are refused

Usage:
  python3 tools/project-audit.py <config.json> [--refresh] [--only cat1,cat2] [--slow]
Exit code 1 if any non-advisory category has a BROKEN verdict.
"""
import glob, hashlib, json, os, re, shutil, subprocess, sys, time, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
BLOCKED = (r"rm -rf /|rm -rf ~|git push --force|git push -f|git reset --hard|git clean -fd|"
           r"DROP TABLE|DROP DATABASE|mkfs|dd if=|chmod -R 777|sudo rm")

SPEC = 'project-audit/1'
CHECK_TYPES = ('files', 'grep', 'command', 'http', 'rpc', 'github', 'huggingface', 'registry', 'docker', 'manual')


def sha(s):
    return hashlib.sha1(s.encode()).hexdigest()[:16]


def die(msg):
    sys.exit(f'project-audit: {msg}')


class Audit:
    def __init__(self, cfg_path, refresh, slow):
        self.cfg_path = os.path.realpath(cfg_path)
        try:
            self.cfg = json.load(open(self.cfg_path))
        except ValueError as e:
            die(f'config is not valid JSON: {e}')
        if self.cfg.get('spec') != SPEC:
            die(f'unsupported spec {self.cfg.get("spec")!r}; expected {SPEC!r}')
        t = self.cfg['target']
        self.name = t['name']
        self.root = os.path.normpath(os.path.join(os.path.dirname(self.cfg_path), t.get('root', '.')))
        self.chain = t.get('chain')
        self.report_dir = os.path.normpath(os.path.join(ROOT, t.get('report_dir', 'BRAIN/research/audit')))
        am = self.cfg.get('absolute_mode', {})
        self.ttl = am.get('cache_ttl_hours', 24)
        self.timeout = am.get('max_command_timeout', 120)
        self.marker = am.get('unverified_marker', 'UNVERIFIED')
        self.refresh = refresh
        self.slow = slow
        self.cache_dir = os.path.join(self.report_dir, '.cache')
        os.makedirs(self.cache_dir, exist_ok=True)
        self.verdicts = []

    # ---------- evidence plumbing ----------
    def cached(self, key, fn):
        path = os.path.join(self.cache_dir, sha(key) + '.json')
        if not self.refresh and os.path.exists(path) and time.time() - os.path.getmtime(path) < self.ttl * 3600:
            return json.load(open(path))
        out = fn()
        if out is not None:
            json.dump(out, open(path, 'w'))
        return out

    def target_path(self, p):
        return os.path.normpath(os.path.join(self.root, p))

    # ---------- checks; each returns (verdict, evidence) ----------
    def c_files(self, c):
        pats, mode = c['patterns'], c.get('expect', 'all_exist')
        found = []
        for pat in pats:
            wants_deps = 'node_modules' in pat
            for p in glob.glob(self.target_path(pat), recursive=True):
                rel = os.path.relpath(p, self.root)
                if not wants_deps and any(seg in ('node_modules', '.git', '__pycache__', 'target', 'dist', 'out') for seg in rel.split(os.sep)):
                    continue
                found.append(rel)
        if mode == 'none_exist':
            return ('WORKS' if not found else 'BROKEN', f'{len(found)} matches (want 0): {found[:5]}')
        if mode == 'any_exist':
            return ('WORKS' if found else 'BROKEN', f'{len(found)} matches (want >=1): {found[:5]}')
        missing = [p for p in pats if not glob.glob(self.target_path(p), recursive=True)]
        return ('WORKS' if not missing else 'BROKEN', f'exists: {sorted(set(found))[:6]}; missing: {missing[:6]}')

    def c_grep(self, c):
        try:
            rx = re.compile(c['pattern'], re.I if c.get('ignore_case', True) else 0)
        except re.error as e:
            return ('BROKEN', f'invalid regex: {e}')
        base = self.target_path(c.get('path', '.'))
        candidates = [base] if os.path.isfile(base) else []
        if os.path.isdir(base):
            for cur, dirs, files in os.walk(base):
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ('node_modules', 'target', 'out', 'dist', '__pycache__')]
                candidates += [os.path.join(cur, f) for f in files]
        n, hits = 0, []
        for p in candidates:
            if not p.endswith(('.py', '.ts', '.tsx', '.js', '.jsx', '.rs', '.json', '.md', '.toml', '.yaml', '.yml', '.env', '.sh', '.html', '.css', '.txt', '.log')):
                continue
            try:
                for i, line in enumerate(open(p, errors='replace'), 1):
                    if rx.search(line):
                        n += 1
                        if len(hits) < 5:
                            hits.append(f'{os.path.relpath(p, self.root)}:{i}: {line.strip()[:110]}')
            except OSError:
                pass
        want_min, want_max = c.get('min_count', 1), c.get('max_count', float('inf'))
        ok = want_min <= n <= want_max
        ev = f'{n} matches (want {want_min}..{want_max})' + ('' if hits else ' — none')
        return ('WORKS' if ok else 'BROKEN', ev + (' | ' + ' | '.join(hits) if hits else ''))

    def c_command(self, c):
        if c.get('slow') and not self.slow:
            return ('UNVERIFIED', 'slow check skipped (run with --slow)')
        cmd = c['command']
        if re.search(BLOCKED, cmd, re.I):
            return ('BROKEN', 'refused: blocked pattern')
        want = c.get('expect_exit', 0)
        cwd = self.target_path(c.get('cwd', '.'))
        if not os.path.isdir(cwd):
            cwd = self.root

        def run():
            p = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True, timeout=self.timeout)
            return {'rc': p.returncode, 'out': (p.stdout or '')[-4000:], 'err': (p.stderr or '')[-2000:]}
        try:
            r = self.cached(f'{self.name}:cmd:{cmd}@{cwd}', run if c.get('cacheable') else (lambda: None)) \
                if c.get('cacheable') else run()
        except subprocess.TimeoutExpired:
            return ('BROKEN', f'timed out after {self.timeout}s')
        if r is None:
            die('unreachable')
        ok = r['rc'] == want
        tail = (r['out'] or r['err']).strip().splitlines()
        return ('WORKS' if ok else 'BROKEN', f'exit {r["rc"]} (want {want}) | ' + ' / '.join(tail[-3:])[:300])

    def c_http(self, c):
        def run():
            try:
                req = urllib.request.Request(c['url'], method=c.get('method', 'GET'),
                                             data=json.dumps(c['body']).encode() if c.get('body') else None,
                                             headers={'User-Agent': 'project-audit', 'Content-Type': 'application/json'})
                r = urllib.request.urlopen(req, timeout=c.get('timeout', 30))
                return {'status': r.status, 'snippet': r.read(600).decode('utf-8', 'replace')}
            except urllib.error.HTTPError as e:
                return {'status': e.code, 'snippet': ''}
            except Exception as e:
                return {'status': -1, 'snippet': str(e)[:120]}
        r = self.cached(f'{self.name}:http:{c["url"]}{c.get("method", "GET")}', run)
        want = c.get('expect_status', 200)
        return ('WORKS' if r['status'] == want else 'BROKEN', f'HTTP {r["status"]} (want {want}) | {r["snippet"][:150]}')

    def c_rpc(self, c):
        def run():
            try:
                body = json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': c['method'], 'params': c.get('params', [])}).encode()
                r = urllib.request.urlopen(urllib.request.Request(c['url'], data=body,
                                                headers={'Content-Type': 'application/json'}), timeout=30)
                return json.load(r)
            except Exception as e:
                return {'error': str(e)[:150]}
        r = self.cached(f'{self.name}:rpc:{c["url"]}:{c["method"]}:{json.dumps(c.get("params", []))}', run)
        if 'error' in r and not r.get('result'):
            return ('BROKEN', f'rpc error: {json.dumps(r)[:200]}')
        res = r.get('result')
        ev = json.dumps(res)[:180]
        for f in c.get('expect_fields', []):
            if res is None or f not in json.dumps(res):
                return ('BROKEN', f'field {f!r} not in result | {ev}')
        return ('WORKS', ev)

    def c_github(self, c):
        repo = c['repo']
        def run():
            p = subprocess.run(['gh', 'api', f'repos/{repo}'], capture_output=True, text=True)
            if p.returncode == 0:
                return json.loads(p.stdout)
            try:
                return json.load(urllib.request.urlopen(f'https://api.github.com/repos/{repo}', timeout=20))
            except Exception as e:
                return {'error': str(e)[:120]}
        d = self.cached(f'github:{repo}', run)
        if 'error' in d or 'full_name' not in d:
            return ('BROKEN', f'github: {json.dumps(d)[:150]}')
        ev = [f'{repo} pushed {d.get("pushed_at", "?")[:10]}, stars {d.get("stargazers_count")}, archived={d.get("archived")}']
        if c.get('tree_contains'):
            p = subprocess.run(['gh', 'api', f'repos/{repo}/git/trees/HEAD?recursive=1'], capture_output=True, text=True)
            paths = [t['path'] for t in json.loads(p.stdout).get('tree', [])] if p.returncode == 0 else []
            miss = [w for w in c['tree_contains'] if not any(w in p_ for p_ in paths)]
            ev.append(f'tree {len(paths)} paths; contains-missing: {miss or "none"}')
            if miss:
                return ('BROKEN', '; '.join(ev))
        if c.get('expect_active_within_days'):
            pushed = d.get('pushed_at') or ''
            age = (time.time() - time.mktime(time.strptime(pushed[:10], '%Y-%m-%d'))) / 86400
            ev.append(f'last push {age:.0f}d ago (want <= {c["expect_active_within_days"]})')
            if age > c['expect_active_within_days']:
                return ('BROKEN', '; '.join(ev))
        return ('WORKS', '; '.join(ev))

    def c_huggingface(self, c):
        kind = c.get('kind', 'models')
        def run():
            try:
                r = urllib.request.urlopen(f'https://huggingface.co/api/{kind}/{c["id"]}', timeout=20)
                return {'status': r.status, 'data': json.load(r)}
            except urllib.error.HTTPError as e:
                return {'status': e.code}
            except Exception as e:
                return {'status': -1, 'err': str(e)[:100]}
        r = self.cached(f'hf:{kind}:{c["id"]}', run)
        ok = r.get('status') == 200
        extra = ''
        if ok and c.get('expect_downloads_min'):
            dl = r['data'].get('downloads', 0)
            extra = f', downloads {dl} (want >= {c["expect_downloads_min"]})'
            ok = dl >= c['expect_downloads_min']
        return ('WORKS' if ok else 'BROKEN', f'HF {kind}/{c["id"]}: HTTP {r.get("status")}{extra}')

    def c_registry(self, c):
        eco, pkg = c['ecosystem'], c['package']
        url = {'npm': f'https://registry.npmjs.org/{pkg}',
               'pypi': f'https://pypi.org/pypi/{pkg}/json',
               'crates': f'https://crates.io/api/v1/crates/{pkg}'}[eco]
        def run():
            try:
                r = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'project-audit'}), timeout=20)
                return {'status': r.status, 'data': json.load(r)}
            except urllib.error.HTTPError as e:
                return {'status': e.code}
            except Exception as e:
                return {'status': -1, 'err': str(e)[:100]}
        r = self.cached(f'reg:{eco}:{pkg}', run)
        if r.get('status') != 200:
            return ('BROKEN', f'{eco}/{pkg}: HTTP {r.get("status")} {r.get("err", "")}')
        d = r['data']
        if eco == 'npm' and c.get('dist_tag'):
            tags = d.get('dist-tags', {})
            ver = tags.get(c['dist_tag'])
            if not ver:
                return ('BROKEN', f'npm/{pkg}: dist-tag {c["dist_tag"]!r} not found in {sorted(tags)}')
        else:
            ver = {'npm': lambda: d.get('dist-tags', {}).get('latest'),
                   'pypi': lambda: d.get('info', {}).get('version'),
                   'crates': lambda: d.get('crate', {}).get('max_stable_version')}[eco]()
        ok = True
        if c.get('min_version') and ver:
            ok = [int(x) for x in ver.split('.')[0:2]] >= [int(x) for x in c['min_version'].split('.')[0:2]]
        return ('WORKS' if ok else 'BROKEN', f'{eco}/{pkg}: latest {ver} (want >= {c.get("min_version", "any")})')

    def c_docker(self, c):
        files = [f for f in ('Dockerfile', 'docker-compose.yml', 'docker-compose.yaml', 'compose.yml', 'compose.yaml')
                 if os.path.exists(self.target_path(f))]
        if c.get('expect') == 'none':
            return ('WORKS' if not files else 'BROKEN', f'docker files found: {files or "none"}')
        if not files:
            return ('N/A', 'no docker/compose file in target')
        ev = [f'files: {files}']
        if shutil.which('docker'):
            compose = next((f for f in files if 'compose' in f), None)
            if compose:
                p = subprocess.run(f'docker compose -f {compose} config --services', shell=True,
                                   cwd=self.root, capture_output=True, text=True, timeout=60)
                if p.returncode == 0:
                    ev.append(f'compose valid, services: {p.stdout.split()}')
                    return ('WORKS', '; '.join(ev))
                ev.append(f'compose config FAILED: {p.stderr.strip()[:150]}')
                return ('BROKEN', '; '.join(ev))
        ev.append('docker CLI unavailable — file presence only')
        return ('UNVERIFIED', '; '.join(ev))

    def c_manual(self, c):
        return (self.marker, f"MANUAL: {c.get('question', 'human judgment required')}")

    def run_check(self, c):
        t = c.get('type')
        if t not in CHECK_TYPES:
            return ('BROKEN', f'unknown check type {t!r}')
        try:
            fn = getattr(self, 'c_' + t)
            return fn(c)
        except Exception as e:
            return (self.marker, f'check error ({type(e).__name__}: {e}) — treated as {self.marker}, never assumed')

    # ---------- orchestration ----------
    def run(self):
        only = None
        if '--only' in sys.argv:
            only = set(sys.argv[sys.argv.index('--only') + 1].split(','))
        L = [f'# PROJECT AUDIT — {self.name} — {time.strftime("%Y-%m-%d %H:%M")}',
             f'target root: `{os.path.relpath(self.root, ROOT)}` | spec {SPEC} | config: `{os.path.relpath(self.cfg_path, ROOT)}`',
             f'absolute mode: verdicts only from captured evidence; everything else is {self.marker}.', '',
             '## Summary', '| category | verdict | checks ok/broken/unverified |', '|---|---|---|']
        rows, any_broken = [], False
        for cat in self.cfg.get('categories', []):
            if only and cat['id'] not in only:
                continue
            checks = []
            for f in cat.get('features', [{'id': cat['id'], 'checks': cat.get('checks', [])}]):
                for c in f.get('checks', []):
                    v, ev = self.run_check(c)
                    checks.append((f"{f['id']}/{c.get('id', c['type'])}", v, ev))
            if not checks:
                checks = [(cat['id'] + '/none', self.marker, 'no checks defined')]
            ok = sum(1 for _, v, _ in checks if v == 'WORKS')
            bad = sum(1 for _, v, _ in checks if v == 'BROKEN')
            unv = sum(1 for _, v, _ in checks if v not in ('WORKS', 'BROKEN'))
            verdict = 'BROKEN' if bad else ('WORKS' if ok else self.marker)
            if bad and not cat.get('advisory'):
                any_broken = True
            L.append(f"| {cat['id']} | **{verdict}** | {ok}/{bad}/{unv} |")
            rows.append((cat, checks))
        L.append('')
        for cat, checks in rows:
            L += [f"## {cat['id']} — {cat.get('question', '')}",
                  f"verdict: **{('BROKEN' if any(v == 'BROKEN' for _, v, _ in checks) else ('WORKS' if all(v == 'WORKS' for _, v, _ in checks) else self.marker))}**", '',
                  '| check | verdict | evidence |', '|---|---|---|']
            L += [f'| {cid} | {v} | {ev.replace("|", "/")[:240]} |' for cid, v, ev in checks]
            L.append('')
        L += ['---', f'generated by tools/project-audit.py | exit {"1 (BROKEN present)" if any_broken else "0"}']
        path = os.path.join(self.report_dir, f'{self.name.upper()}-AUDIT.md')
        os.makedirs(self.report_dir, exist_ok=True)
        open(path, 'w').write('\n'.join(L) + '\n')
        print('\n'.join(L[5:6 + len(self.cfg.get("categories", []))]))
        print(f'report -> {os.path.relpath(path, ROOT)}')
        print(f'RESULT: {"FAIL" if any_broken else "PASS"}')
        return 1 if any_broken else 0


if __name__ == '__main__':
    args = sys.argv[1:]
    cfgs = [a for a in args if not a.startswith('--')]
    if not cfgs:
        die('usage: project-audit.py <config.json> [--refresh] [--only c1,c2] [--slow]')
    sys.exit(Audit(cfgs[0], '--refresh' in args, '--slow' in args).run())
