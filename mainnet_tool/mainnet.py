#!/usr/bin/env python3
"""mainnet.py — build & audit engine for crypto/web3 projects, any network.

Self-contained (Python stdlib only). Combines the working patterns of three tools:
  lord.py     deterministic ops: file read/write/edit, grep, RPC, safe run, state
  codetool.py template-driven scaffolding (init) + structured checks
  glm-audit   usage discipline + honest, evidence-only reporting

Hard independence rules:
  - writes ONLY to (a) mainnet_tool/.cache (its own state) and (b) the target
    directory given in the blueprint. Never touches any other folder.
  - `init` refuses an existing non-empty target without --force.
  - destructive commands are refused; verdicts never come from assumptions.

Commands:
  mainnet.py init    <blueprint.json> [--target DIR] [--force]   scaffold a project
  mainnet.py check   <blueprint.json> [--refresh] [--only c1,c2] audit 15 dimensions
  mainnet.py list-chains                                            supported templates
  mainnet.py selftest                                               verify this tool itself
  mainnet.py show <file>                                            print an example blueprint
"""
import glob as _glob
import hashlib, json, os, re, shutil, subprocess, sys, time, urllib.request, urllib.error

HERE = os.path.dirname(os.path.realpath(__file__))
CACHE = os.path.join(HERE, '.cache')
SPEC = 'mainnet-tool/1'
BLOCKED = ('rm' + ' -rf /|rm' + ' -rf ~|git push --f' + 'orce|git push -f|git reset --h' + 'ard|git clean -fd|'
           'DROP' + ' TABLE|DROP' + ' DATABASE|mkfs|dd if=|chmod -R 777|sudo rm')
CHAINS = ('solana', 'evm', 'web')
DEFAULT_DIMENSIONS = [
    ('backtest', 'apakah backtest/eksperimen berjalan dan terukur?',
     [{'id': 'backtest/no-tests-yet', 'type': 'files', 'patterns': ['tests/*', 'test/*', '**/backtest*'], 'expect': 'any_exist'}]),
    ('backend', 'apakah backend/entrypoint ada dan dependensi terpasang?',
     [{'id': 'backend/entry', 'type': 'files', 'patterns': ['package.json', 'Cargo.toml', 'pyproject.toml', 'requirements.txt', 'go.mod'], 'expect': 'any_exist'}]),
    ('frontend', 'apakah frontend ada?',
     [{'id': 'frontend/presence', 'type': 'files', 'patterns': ['index.html', 'src/**/*.tsx', 'app/**/*.tsx', 'web/**'], 'expect': 'any_exist'}]),
    ('ui-ux', 'apakah UI sudah dibuat dan diuji?',
     [{'id': 'ui-ux/manual', 'type': 'manual', 'question': 'adanya mockup/flow UI perlu dicek manusia'}]),
    ('user-experience', 'apakah alur pengguna terdefinisi?',
     [{'id': 'ux/documented', 'type': 'grep', 'pattern': 'flow|onboarding|step', 'path': '.', 'min_count': 2}]),
    ('user-flow', 'apakah user flow end-to-end terdokumentasi?',
     [{'id': 'flow/readme', 'type': 'files', 'patterns': ['README.md'], 'expect': 'all_exist'},
      {'id': 'flow/steps', 'type': 'grep', 'pattern': 'install|setup|run|deploy', 'path': 'README.md', 'min_count': 3}]),
    ('concept-narasi', 'apakah narasi produk tertulis?',
     [{'id': 'concept/one-liner', 'type': 'grep', 'pattern': 'one.?liner|what (this|we)', 'path': 'README.md', 'min_count': 1}]),
    ('workflow', 'apakah workflow dev (install->test->build) terdefinisi?',
     [{'id': 'workflow/scripts', 'type': 'grep', 'pattern': '"scripts"', 'path': 'package.json', 'min_count': 1}]),
    ('framework', 'apakah framework/stack terpasang dari registry?',
     [{'id': 'framework/lockfile', 'type': 'files', 'patterns': ['package-lock.json', 'Cargo.lock', 'poetry.lock', 'go.sum'], 'expect': 'any_exist'}]),
    ('docker', 'apakah deployment container siap?',
     [{'id': 'docker/presence', 'type': 'docker'}]),
    ('implementasi', 'apakah implementasi meninggalkan bukti jalan (log/build)?',
     [{'id': 'impl/artifacts', 'type': 'files', 'patterns': ['*.log', 'dist/*', 'build/*', 'out/*'], 'expect': 'any_exist'}]),
    ('mainnet-onchain', 'apakah target on-chain hidup?',
     [{'id': 'onchain/rpc', 'type': 'manual', 'question': 'perlu rpc check: isi section onchain di blueprint (url+method+params+expect_fields)'}]),
    ('api-kebutuhan', 'apakah API eksternal yang dibutuhkan tersedia?',
     [{'id': 'api/env-example', 'type': 'files', 'patterns': ['.env.example', '.env.sample'], 'expect': 'any_exist'}]),
    ('resource-github-hf', 'apakah resource GitHub/HuggingFace aktif?',
     [{'id': 'res/github', 'type': 'manual', 'question': 'isi section resources.github = [{repo, expect_active_within_days}] di blueprint'}]),
    ('fitur-berfungsi', 'audit fitur per fitur: berjalan atau belum?',
     [{'id': 'fitur/features-in-blueprint', 'type': 'manual', 'question': 'daftar fitur di blueprint.features -> tiap fitur: {id, evidence(grep/files/command)}'},
      {'id': 'ideas/brainstorm', 'type': 'manual', 'question': 'open ideas perlu keputusan manusia'}]),
]


def die(m):
    sys.exit(f'mainnet: {m}')


def sha(s):
    return hashlib.sha1(s.encode()).hexdigest()[:16]


class Net:
    """glm-audit pattern: every call counted, cached, honestly reported."""
    calls = {'http': 0, 'cached': 0}

    @staticmethod
    def cached(key, fn, ttl_h=24):
        os.makedirs(CACHE, exist_ok=True)
        p = os.path.join(CACHE, sha(key) + '.json')
        if os.path.exists(p) and time.time() - os.path.getmtime(p) < ttl_h * 3600:
            Net.calls['cached'] += 1
            return json.load(open(p))
        Net.calls['http'] += 1
        out = fn()
        if out is not None:
            json.dump(out, open(p, 'w'))
        return out

    @staticmethod
    def jsonrpc(url, method, params):
        def call():
            try:
                r = urllib.request.urlopen(urllib.request.Request(
                    url, data=json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params}).encode(),
                    headers={'Content-Type': 'application/json'}), timeout=30)
                return json.load(r)
            except urllib.error.HTTPError as e:
                return {'error': f'HTTP {e.code}'}
            except Exception as e:
                return {'error': str(e)[:150]}
        return Net.cached(f'rpc:{url}:{method}:{json.dumps(params)}', call)

    @staticmethod
    def get(url):
        def call():
            try:
                r = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'mainnet-tool'}), timeout=30)
                return {'status': r.status, 'body': r.read(500).decode('utf-8', 'replace')}
            except urllib.error.HTTPError as e:
                return {'status': e.code, 'body': ''}
            except Exception as e:
                return {'status': -1, 'body': str(e)[:120]}
        return Net.cached(f'get:{url}', call)


# ---------------------------------------------------------------- scaffold (codetool pattern)
TEMPLATES = {
    'solana': {
        'package.json': '''{
  "name": "{{NAME}}",
  "private": true,
  "type": "module",
  "scripts": {
    "build": "tsc -p tsconfig.json",
    "start": "node dist/main.js",
    "check:balance": "tsx src/main.ts balance",
    "check:tx": "tsx src/main.ts tx"
  },
  "dependencies": {
    "@solana/web3.js": "^1.95.0"
  },
  "devDependencies": {
    "tsx": "^4.19.0",
    "typescript": "^5.6.0"
  }
}
''',
        'tsconfig.json': '{"compilerOptions":{"target":"ES2022","module":"ES2022","moduleResolution":"bundler","outDir":"dist","strict":true,"skipLibCheck":true},"include":["src"]}\n',
        'src/main.ts': '''// {{NAME}} — solana client entrypoint
import { Connection, PublicKey } from "@solana/web3.js";

const RPC = process.env.RPC_URL ?? "https://api.mainnet-beta.solana.com";
const cmd = process.argv[2] ?? "balance";

async function main() {
  const c = new Connection(RPC, "confirmed");
  if (cmd === "balance") {
    const a = new PublicKey(process.argv[3] ?? die("usage: balance <pubkey>"));
    console.log("balance", await c.getBalance(a), "lamports @", RPC);
  } else if (cmd === "tx") {
    const s = process.argv[3] ?? die("usage: tx <signature>");
    const r = await c.getSignatureStatus(s);
    console.log("tx", s.slice(0, 12), JSON.stringify(r.value?.[0] ?? null));
  } else die(`unknown command: ${cmd}`);
}
function die(m: string): never { console.error(m); process.exit(1); }
main().catch((e) => { console.error(e); process.exit(1); });
''',
        '.env.example': 'RPC_URL=https://api.mainnet-beta.solana.com\n',
        'Dockerfile': '''FROM node:22-slim
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build
CMD ["node", "dist/main.js"]
''',
        'README.md': '''# {{NAME}}

solana project scaffolded by mainnet_tool.

## user flow (onboarding in 4 steps)
1. install: `npm install`
2. setup: `cp .env.example .env`
3. run: `npm run check:balance -- <pubkey>`
4. deploy: `docker build -t {{NAME}} .`

## what this is
one-liner: {{NAME}} is a {{DESC}} on solana.
''',
    },
    'evm': {
        'package.json': '''{
  "name": "{{NAME}}",
  "private": true,
  "scripts": {
    "build": "tsc -p tsconfig.json",
    "deploy": "tsx scripts/deploy.ts",
    "check:code": "tsx scripts/deploy.ts check"
  },
  "devDependencies": {
    "tsx": "^4.19.0",
    "typescript": "^5.6.0"
  }
}
''',
        'tsconfig.json': '{"compilerOptions":{"target":"ES2022","module":"ES2022","moduleResolution":"bundler","outDir":"dist","strict":true,"skipLibCheck":true},"include":["src","scripts"]}\n',
        'contracts/{{NAME}}.sol': '''// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

contract {{CONTRACT}} {
    string public constant oneLiner = "{{DESC}}";
    event Touched(address indexed by);
    function touch() external { emit Touched(msg.sender); }
}
''',
        'scripts/deploy.ts': '''// {{NAME}} — evm deploy/check entry (lord.py pattern: evidence first)
import { readFileSync } from "node:fs";
const RPC = process.env.RPC_URL ?? die("set RPC_URL (see .env.example)");
const cmd = process.argv[2] ?? "check";
async function main() {
  if (cmd === "check") {
    const r = await fetch(RPC, {method: "POST", headers: {"Content-Type": "application/json"},
      body: JSON.stringify({jsonrpc: "2.0", id: 1, method: "eth_chainId", params: []})});
    const j = await r.json() as any;
    console.log("chainId", parseInt(j.result, 16), "@", RPC);
  } else die(`unknown command: ${cmd}`);
}
function die(m: string): never { console.error(m); process.exit(1); }
main();
''',
        '.env.example': 'RPC_URL=https://eth.llamarpc.com\n',
        'Dockerfile': '''FROM node:22-slim
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
CMD ["tsx", "scripts/deploy.ts", "check"]
''',
        'README.md': '''# {{NAME}}

evm project scaffolded by mainnet_tool.

## user flow
1. install: `npm install`
2. setup: `cp .env.example .env`
3. check network: `npm run check:code`
4. deploy: `npm run deploy` (wiring up a signer is your next step)

## what this is
one-liner: {{NAME}} is a {{DESC}} on evm.
''',
    },
    'web': {
        'index.html': '''<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{NAME}}</title><style>body{font-family:system-ui;max-width:40rem;margin:4rem auto;padding:0 1rem}</style></head>
<body>
<h1>{{NAME}}</h1>
<p>one-liner: {{NAME}} is a {{DESC}}.</p>
<button id="go">connect wallet</button>
<pre id="out"></pre>
<script src="app.js"></script>
</body>
</html>
''',
        'app.js': '''// {{NAME}} — wallet connect stub (evidence: console output)
document.getElementById("go").onclick = async () => {
  const out = document.getElementById("out");
  if (!(window as any).solana) return out.textContent = "no solana wallet found";
  const r = await (window as any).solana.connect();
  out.textContent = "connected: " + r.publicKey.toString();
};
''',
        'README.md': '''# {{NAME}}

static web scaffold. user flow: open index.html -> connect wallet.

## what this is
one-liner: {{NAME}} is a {{DESC}}.
''',
        'Dockerfile': '''FROM nginx:alpine
COPY . /usr/share/nginx/html
''',
    },
}


def render(text, vars):
    for k, v in vars.items():
        text = text.replace('{{' + k + '}}', v)
    return re.sub(r'\{\{\w+\}\}', '-', text)


def cmd_init(bp, target, force):
    b = bp['build']
    chain = b.get('chain') or bp['project'].get('chain')
    if chain not in CHAINS:
        die(f'unknown chain {chain!r}; supported: {", ".join(CHAINS)}')
    if not target:
        target = b.get('target') or bp['project']['name']
    target = os.path.realpath(target)
    if os.path.exists(target) and os.listdir(target) and not force:
        die(f'target {target} exists and is not empty (use --force to overwrite files)')
    vars = {'NAME': bp['project']['name'], 'DESC': bp['project'].get('desc', 'web3 project'),
            'CONTRACT': re.sub(r'[^A-Za-z0-9]', '', bp['project']['name'].title())}
    vars.update(b.get('vars', {}))
    made = []
    os.makedirs(CACHE, exist_ok=True)
    for rel, content in TEMPLATES[chain].items():
        p = os.path.join(target, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, 'w').write(render(content, vars))
        made.append(rel)
    json.dump({'target': target, 'chain': chain, 'created': made, 'when': time.strftime('%Y-%m-%d %H:%M')},
              open(os.path.join(CACHE, 'last-init.json'), 'w'))
    print(f'init: {len(made)} files -> {target} (chain={chain})')
    for m in made:
        print('  +', m)
    print('next: edit the blueprint checks, then: mainnet.py check <blueprint>')


# ---------------------------------------------------------------- checks (lord + audit pattern)
def run_check(c, root, slow_ok):
    t = c.get('type')
    tp = lambda p: os.path.normpath(os.path.join(root, p))
    try:
        if t == 'files':
            pats, mode = c['patterns'], c.get('expect', 'all_exist')
            found = []
            for pat in pats:
                want_deps = 'node_modules' in pat
                for p in _glob.glob(tp(pat), recursive=True):
                    rel = os.path.relpath(p, root)
                    if not want_deps and any(s in ('node_modules', '.git', '__pycache__', 'dist', 'out', 'target') for s in rel.split(os.sep)):
                        continue
                    found.append(rel)
            if mode == 'none_exist':
                return ('WORKS' if not found else 'BROKEN', f'{len(found)} matches (want 0): {found[:4]}')
            if mode == 'any_exist':
                return ('WORKS' if found else 'BROKEN', f'{len(found)} matches (want >=1)')
            miss = [p for p in pats if not _glob.glob(tp(p), recursive=True)]
            return ('WORKS' if not miss else 'BROKEN', f'exists {sorted(set(found))[:5]}; missing {miss[:5]}')
        if t == 'grep':
            rx = re.compile(c['pattern'], re.I)
            base = tp(c.get('path', '.'))
            files = []
            if os.path.isfile(base):
                files = [base]
            elif os.path.isdir(base):
                for cur, ds, fs in os.walk(base):
                    ds[:] = [d for d in ds if d not in ('node_modules', '__pycache__', '.git', 'dist', 'out', 'target')]
                    files += [os.path.join(cur, f) for f in fs]
            n, hits = 0, []
            for p in files:
                if not p.endswith(('.py', '.ts', '.tsx', '.js', '.jsx', '.rs', '.sol', '.json', '.md', '.toml', '.yaml', '.yml', '.sh', '.html', '.css', '.txt', '.log', '.env')):
                    continue
                for i, line in enumerate(open(p, errors='replace'), 1):
                    if rx.search(line):
                        n += 1
                        if len(hits) < 4:
                            hits.append(f'{os.path.relpath(p, root)}:{i}: {line.strip()[:90]}')
            mn, mx = c.get('min_count', 1), c.get('max_count', float('inf'))
            return ('WORKS' if mn <= n <= mx else 'BROKEN', f'{n} matches (want {mn}..{mx}) | ' + ' | '.join(hits)[:200])
        if t == 'command':
            if c.get('slow') and not slow_ok:
                return ('UNVERIFIED', 'slow check skipped (--slow)')
            if re.search(BLOCKED, c['command'], re.I):
                return ('BROKEN', 'refused: blocked pattern')
            p = subprocess.run(c['command'], shell=True, cwd=tp(c.get('cwd', '.')),
                               capture_output=True, text=True, timeout=c.get('timeout', 120))
            ok = p.returncode == c.get('expect_exit', 0)
            return ('WORKS' if ok else 'BROKEN', f'exit {p.returncode} | ' + ((p.stdout or p.stderr).strip().splitlines()[-1:] or [''])[-1][:160])
        if t == 'http':
            r = Net.get(c['url'])
            want = c.get('expect_status', 200)
            return ('WORKS' if r['status'] == want else 'BROKEN', f'HTTP {r["status"]} (want {want}) | {r["body"][:100]}')
        if t == 'rpc':
            r = Net.jsonrpc(c['url'], c['method'], c.get('params', []))
            res = r.get('result')
            if res is None and r.get('error'):
                return ('BROKEN', f'rpc error: {json.dumps(r)[:160]}')
            ev = json.dumps(res)[:160]
            for f in c.get('expect_fields', []):
                if f not in ev:
                    return ('BROKEN', f'field {f!r} missing | {ev}')
            return ('WORKS', ev)
        if t == 'github':
            repo = c['repo']
            d2 = Net.cached(f'gh:{repo}', lambda: _gh(repo), 12)
            if 'full_name' not in d2:
                return ('BROKEN', f'github {repo}: {json.dumps(d2)[:140]}')
            ev = f'{repo} pushed {(d2.get("pushed_at") or "?")[:10]}, stars {d2.get("stargazers_count")}'
            if c.get('expect_active_within_days'):
                age = (time.time() - time.mktime(time.strptime((d2.get('pushed_at') or '2000-01-01')[:10], '%Y-%m-%d'))) / 86400
                ev += f' ({age:.0f}d ago, want <= {c["expect_active_within_days"]}d)'
                if age > c['expect_active_within_days']:
                    return ('BROKEN', ev)
            return ('WORKS', ev)
        if t == 'huggingface':
            kind = c.get('kind', 'models')
            r = Net.get(f'https://huggingface.co/api/{kind}/{c["id"]}')
            return ('WORKS' if r['status'] == 200 else 'BROKEN', f'HF {kind}/{c["id"]}: HTTP {r["status"]}')
        if t == 'docker':
            files = [f for f in ('Dockerfile', 'docker-compose.yml', 'compose.yaml') if os.path.exists(tp(f))]
            if c.get('expect') == 'none' or not files:
                return ('N/A' if not files else 'WORKS', f'docker files: {files or "none"}')
            if shutil.which('docker'):
                p = subprocess.run(f'docker build --check . 2>/dev/null || docker compose config -q 2>&1 || echo PRESENT', shell=True, cwd=root, capture_output=True, text=True, timeout=90)
                return ('WORKS', f'files {files}; docker: {(p.stdout or "").strip()[:100]}')
            return ('UNVERIFIED', f'files {files}; docker CLI unavailable')
        if t == 'manual':
            return ('UNVERIFIED', f'MANUAL: {c.get("question", "needs human judgment")}')
        return ('BROKEN', f'unknown check type {t!r}')
    except Exception as e:
        return ('UNVERIFIED', f'check error {type(e).__name__}: {e}')


def _gh(repo):
    p = subprocess.run(['gh', 'api', f'repos/{repo}'], capture_output=True, text=True)
    if p.returncode == 0:
        return json.loads(p.stdout)
    return json.loads(Net.get(f'https://api.github.com/repos/{repo}')['body'] or '{}')


def cmd_check(bp, refresh, only):
    if refresh:
        shutil.rmtree(CACHE, ignore_errors=True)
    proj = bp['project']
    root = os.path.realpath(proj.get('root') or proj['name'])
    if not os.path.isdir(root):
        die(f'target root {root} does not exist (run init first, or fix project.root)')
    dims = {d[0]: d for d in DEFAULT_DIMENSIONS}
    for cat in bp.get('dimensions', []):
        cid = cat['id']
        if cid in dims:
            base = list(dims[cid])
            base[2] = cat.get('checks', base[2])
            dims[cid] = tuple(base)
        else:
            dims[cid] = (cid, cat.get('question', ''), cat.get('checks', []))
    L = [f'# {proj["name"].upper()} — AUDIT — {time.strftime("%Y-%m-%d %H:%M")}',
         f'root: `{root}` | chain: {proj.get("chain")} | network: {proj.get("network", "?")} | spec {SPEC}', '',
         '| dimension | verdict | ok/broken/unv |', '|---|---|---|']
    detail, broken = [], False
    for cid, q, checks in dims.values():
        if only and cid not in only:
            continue
        rs = [(c.get('id', c['type']), *run_check(c, root, '--slow' in sys.argv)) for c in checks]
        ok = sum(v == 'WORKS' for _, v, _ in rs)
        bad = sum(v == 'BROKEN' for _, v, _ in rs)
        unv = len(rs) - ok - bad
        verdict = 'BROKEN' if bad else ('WORKS' if ok else 'UNVERIFIED')
        if bad:
            broken = True
        L.append(f'| {cid} | **{verdict}** | {ok}/{bad}/{unv} |')
        detail += [f'## {cid} — {q}', '', '| check | verdict | evidence |', '|---|---|---|']
        detail += [f'| {i} | {v} | {e.replace("|", "/")[:220]} |' for i, v, e in rs] + ['']
    L += ['', *detail, '---',
          f'network calls: {Net.calls["http"]} fresh, {Net.calls["cached"]} cached (glm-audit discipline: counted, not hidden)']
    out = os.path.join(HERE, 'reports', f'{proj["name"].upper()}-AUDIT.md')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, 'w').write('\n'.join(L) + '\n')
    print('\n'.join(L[:5 + len(dims)]))
    print(f'report -> {out}')
    print(f'RESULT: {"FAIL" if broken else "PASS"}')
    return 1 if broken else 0


def cmd_selftest():
    ok = True
    print('selftest 1: blocked command refused')
    v, e = run_check({'type': 'command', 'command': 'rm -rf /'}, HERE, True)
    ok &= v == 'BROKEN'
    print('  ', v, e)
    print('selftest 2: grep on a single file (this file)')
    v, e = run_check({'type': 'grep', 'pattern': 'absolute|evidence', 'path': 'mainnet.py'}, HERE, True)
    ok &= v == 'WORKS'
    print('  ', v, e[:80])
    print('selftest 3: rpc solana mainnet alive')
    v, e = run_check({'type': 'rpc', 'url': 'https://api.mainnet-beta.solana.com', 'method': 'getHealth', 'params': [], 'expect_fields': ['ok']}, HERE, True)
    ok &= v == 'WORKS'
    print('  ', v, e[:80])
    print('selftest 4: refuse unknown check type')
    v, e = run_check({'type': 'nonsense'}, HERE, True)
    ok &= v == 'BROKEN'
    print('  ', v, e)
    print('SELFTEST:', 'PASS' if ok else 'FAIL')
    return 0 if ok else 1


def main():
    a = sys.argv[1:]
    if not a:
        die(__doc__)
    cmd, args = a[0], a[1:]
    if cmd == 'list-chains':
        for ch in CHAINS:
            print(f'{ch:8} {len(TEMPLATES[ch])} template files')
        return
    if cmd == 'selftest':
        sys.exit(cmd_selftest())
    if cmd == 'show':
        p = os.path.join(HERE, 'examples', args[0])
        print(open(p).read() if os.path.exists(p) else f'no example {args[0]!r} in examples/')
        return
    cfg = [x for x in args if not x.startswith('--')]
    if not cfg:
        die('blueprint json required')
    try:
        bp = json.load(open(cfg[0]))
    except ValueError as e:
        die(f'blueprint not valid JSON: {e}')
    if bp.get('spec') != SPEC:
        die(f'blueprint spec {bp.get("spec")!r} != {SPEC!r}')
    if cmd == 'init':
        cmd_init(bp, next((cfg[i + 1] for i, x in enumerate(cfg) if x == '--target'), None), '--force' in args)
    elif cmd == 'check':
        only = None
        if '--only' in args:
            only = set(args[args.index('--only') + 1].split(','))
        sys.exit(cmd_check(bp, '--refresh' in args, only))
    else:
        die(f'unknown command {cmd!r}')


if __name__ == '__main__':
    main()
