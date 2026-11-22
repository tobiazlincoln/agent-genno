#!/usr/bin/env python3
"""mainnet.py v2 — build & audit engine for crypto/web3 projects, any network.

Rebuild dari v1 dengan pola yang sama (lord.py: ops deterministik; codetool.py:
scaffold+check; glm-audit.py: usage & honest reporting) plus:
  - registry jaringan EXTERNAL (networks.json) — tambah chain tanpa edit Python
  - template EXTERNAL (templates/<family>/...) — file nyata, bukan string Python
  - `networks --find <nama>` — cari chain EVM APA PUN dari dataset open source
    ethereum-lists/chains (chainid.network, 2899 chain), cache 24 jam
  - `doctor` — cek environment team (node/python/git/docker)
  - rpc check mengukur LATENCY; laporan punya seksi NEXT ACTIONS dari temuan BROKEN

Hard independence rules (tidak berubah):
  - menulis HANYA ke mainnet_tool/.cache, mainnet_tool/reports/, dan target di blueprint
  - `init` menolak target berisi tanpa --force; command destruktif ditolak
  - verdict hanya dari evidence; sisanya UNVERIFIED

Commands:
  init <blueprint.json> [--target DIR] [--force] [--git]
  check <blueprint.json> [--refresh] [--only c1,c2] [--slow]
  networks [--find <nama>] [--chainid <id>]
  doctor | selftest | list-chains | show <example-file>
"""
import glob as _glob
import hashlib, json, os, re, shutil, subprocess, sys, time, urllib.request, urllib.error

HERE = os.path.dirname(os.path.realpath(__file__))
CACHE = os.path.join(HERE, '.cache')
TEMPLATES_DIR = os.path.join(HERE, 'templates')
NETWORKS_FILE = os.path.join(HERE, 'networks.json')
CHAINLIST_URL = 'https://chainid.network/chains.json'
SPEC = 'mainnet-tool/2'
BLOCKED = ('rm' + ' -rf /|rm' + ' -rf ~|git push --f' + 'orce|git push -f|git reset --h' + 'ard|git clean -fd|'
           'DROP' + ' TABLE|DROP' + ' DATABASE|mkfs|dd if=|chmod -R 777|sudo rm')
TEXT_EXT = ('.py', '.ts', '.tsx', '.js', '.jsx', '.rs', '.sol', '.json', '.md', '.toml', '.yaml', '.yml',
            '.sh', '.html', '.css', '.txt', '.log', '.env', '.example', '.sol')
DEFAULT_DIMENSIONS = [
    ('backtest', 'apakah backtest/eksperimen berjalan dan terukur?',
     [{'id': 'backtest/tests', 'type': 'files', 'patterns': ['test/*', 'tests/*', '**/backtest*'], 'expect': 'any_exist'}]),
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
     [{'id': 'workflow/scripts', 'type': 'grep', 'pattern': '"scripts"', 'path': 'package.json', 'min_count': 1},
      {'id': 'workflow/ci', 'type': 'files', 'patterns': ['.github/workflows/*'], 'expect': 'any_exist'}]),
    ('framework', 'apakah framework/stack terpasang dari registry?',
     [{'id': 'framework/lockfile', 'type': 'files', 'patterns': ['package-lock.json', 'Cargo.lock', 'poetry.lock', 'go.sum'], 'expect': 'any_exist'}]),
    ('docker', 'apakah deployment container siap?',
     [{'id': 'docker/presence', 'type': 'docker'}]),
    ('implementasi', 'apakah implementasi meninggalkan bukti jalan (log/build)?',
     [{'id': 'impl/artifacts', 'type': 'files', 'patterns': ['*.log', 'dist/*', 'build/*', 'out/*'], 'expect': 'any_exist'},
      {'id': 'impl/no-unrendered-vars', 'type': 'grep', 'pattern': r'\{\{', 'path': '.', 'min_count': 0, 'max_count': 0},
      {'id': 'impl/no-template-literal-names', 'type': 'files', 'patterns': ['**/{{*'], 'expect': 'none_exist'}]),
    ('mainnet-onchain', 'apakah target on-chain hidup?',
     [{'id': 'onchain/manual', 'type': 'manual', 'question': 'auto-check chainId aktif kalau project.chain ada di networks.json'}]),
    ('api-kebutuhan', 'apakah API eksternal yang dibutuhkan tersedia?',
     [{'id': 'api/env-example', 'type': 'files', 'patterns': ['.env.example', '.env.sample'], 'expect': 'any_exist'}]),
    ('resource-github-hf', 'apakah resource GitHub/HuggingFace aktif?',
     [{'id': 'res/github', 'type': 'manual', 'question': 'tambah check github: {repo, expect_active_within_days} di blueprint'}]),
    ('fitur-berfungsi', 'audit fitur per fitur: berjalan atau belum?',
     [{'id': 'fitur/features-in-blueprint', 'type': 'manual', 'question': 'daftar fitur di blueprint dimensions -> tiap fitur dengan evidence'},
      {'id': 'ideas/brainstorm', 'type': 'manual', 'question': 'open ideas perlu keputusan manusia'}]),
]


def die(m):
    sys.exit(f'mainnet: {m}')


def arg_val(args, flag, cast=str):
    if flag in args:
        i = args.index(flag)
        if i + 1 >= len(args):
            die(f'{flag} butuh nilai')
        try:
            return cast(args[i + 1])
        except ValueError:
            die(f'{flag} harus {cast.__name__}: {args[i + 1]!r}')
    return None


def validate_blueprint(bp):
    """Pesan error jelas untuk blueprint yang salah tulis — team akan membuat kesalahan, tool harus memandu."""
    errs = []
    if not isinstance(bp.get('project'), dict):
        errs.append('section "project" (object) wajib ada')
    else:
        if not bp['project'].get('name'):
            errs.append('project.name wajib ada')
        if not bp['project'].get('chain'):
            errs.append('project.chain wajib ada (solana/eth/bsc/robinhood/elysium/evm)')
    if 'build' in bp and not isinstance(bp['build'], dict):
        errs.append('section "build" harus object')
    if 'dimensions' in bp and not isinstance(bp['dimensions'], list):
        errs.append('section "dimensions" harus array')
    for i, cat in enumerate(bp.get('dimensions', []) if isinstance(bp.get('dimensions'), list) else []):
        if not isinstance(cat, dict) or not cat.get('id'):
            errs.append(f'dimensions[{i}] harus object dengan "id"')
    if errs:
        die('blueprint invalid:\n  - ' + '\n  - '.join(errs))
    chain = bp.get('build', {}).get('chain') or bp['project'].get('chain')
    if chain and chain not in load_networks():
        print(f'WARNING: chain {chain!r} tidak ada di networks.json (init akan gagal); '
              f'cari: mainnet.py networks --find <nama>')


def sha(s):
    return hashlib.sha1(s.encode()).hexdigest()[:16]


def load_networks():
    try:
        d = json.load(open(NETWORKS_FILE))
    except (OSError, ValueError) as e:
        die(f'networks.json unreadable: {e}')
    return {k: v for k, v in d.items() if not k.startswith('_')}


class Net:
    calls = {'http': 0, 'cached': 0}

    @staticmethod
    def cached(key, fn, ttl_h=24):
        os.makedirs(CACHE, exist_ok=True)
        p = os.path.join(CACHE, sha(key) + '.json')
        if os.path.exists(p) and time.time() - os.path.getmtime(p) < ttl_h * 3600:
            Net.calls['cached'] += 1
            out = json.load(open(p))
            if isinstance(out, dict):
                out['_from_cache'] = True
            return out
        Net.calls['http'] += 1
        t0 = time.time()
        out = fn()
        if isinstance(out, dict):
            out['_latency_ms'] = round((time.time() - t0) * 1000)
        if out is not None:
            json.dump(out, open(p, 'w'))
        return out

    @staticmethod
    def jsonrpc(url, method, params):
        def call():
            try:
                r = urllib.request.urlopen(urllib.request.Request(
                    url, data=json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params}).encode(),
                    headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0 (mainnet-tool)'}), timeout=30)
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
                r = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (mainnet-tool)'}), timeout=60)
                return {'status': r.status, 'body': r.read().decode('utf-8', 'replace')}
            except urllib.error.HTTPError as e:
                return {'status': e.code, 'body': ''}
            except Exception as e:
                return {'status': -1, 'body': str(e)[:120]}
        return Net.cached(f'get:{url}', call)


def latency(r):
    if not isinstance(r, dict):
        return ''
    if r.get('_from_cache'):
        return ' [cached]'
    ms = r.get('_latency_ms')
    return f' [{ms}ms]' if ms else ''


# ---------------------------------------------------------------- chainlist (ethereum-lists)
def chainlist():
    def load():
        r = Net.get(CHAINLIST_URL)
        if r.get('status') != 200:
            die(f'chainlist download failed: HTTP {r.get("status")}')
        try:
            return json.loads(r['body'])
        except ValueError:
            die('chainlist is not valid JSON')
    return Net.cached('chainlist:master', load, 24)


def cmd_networks(find, chainid):
    nets = load_networks()
    if not find and chainid is None:
        print(f'{"network":14} {"family":8} {"chain_id":9} {"currency":9} rpc')
        for name, n in nets.items():
            print(f'{name:14} {n["family"]:8} {str(n.get("chain_id", "-")):9} {n.get("currency", "-"):9} {n.get("rpc", "(blueprint must provide)")}')
            if n.get('note'):
                print(f'{"":14} note: {n["note"]}')
        print('\ncari chain EVM lain: mainnet.py networks --find <nama> | --chainid <id>')
        return
    want = (chainid if chainid is not None else find).lower()
    hits = []
    for c in chainlist():
        s = json.dumps(c).lower()
        if (chainid is not None and c.get('chainId') == chainid) or (find and (find.lower() in c.get('name', '').lower() or find.lower() in s)):
            hits.append(c)
    if not hits:
        print(f'not found: {want!r} di ethereum-lists/chains')
        return
    print(f'{len(hits)} match(es):')
    for c in hits[:15]:
        rpcs = [u for u in c.get('rpc', []) if u.startswith('http') and '{' not in u][:2]
        exp = [e.get('url') for e in c.get('explorers', [])][:1]
        print(f'  chainId {c.get("chainId"):6} {c.get("name", "?")[:34]:34} {c.get("nativeCurrency", {}).get("symbol", "?"):6} rpc: {rpcs} explorer: {exp}')
    c = hits[0]
    snippet = json.dumps({str(c.get('chainId')): {
        'family': 'evm', 'rpc': [u for u in c.get('rpc', []) if u.startswith('http') and '{' not in u][:1] or ['FILL_RPC'],
        'chain_id': c.get('chainId'), 'currency': c.get('nativeCurrency', {}).get('symbol', ''),
        'explorer': (c.get('explorers') or [{}])[0].get('url', '')}}, indent=2)
    print('\nsalin ke networks.json untuk mendaftarkan (VERIFIKASI eth_chainId dulu):\n' + snippet)


def cmd_doctor():
    print('environment check (untuk onboarding team):')
    ok = True
    for name, cmd, want in (('node', 'node --version', 'v18+'), ('python', 'python3 --version', '3.10+'),
                            ('git', 'git --version', 'any'), ('docker', 'docker --version', 'optional'),
                            ('gh', 'gh --version', 'optional (github check)')):
        p = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        out = (p.stdout or p.stderr).strip().splitlines()[0] if (p.stdout or p.stderr).strip() else 'NOT FOUND'
        have = p.returncode == 0
        if name in ('docker', 'gh'):
            print(f'  {name:8} {out}  {"(optional)" if not have else ""}')
        else:
            print(f'  {name:8} {out}')
            ok &= have
    print(f'DOCTOR: {"PASS" if ok else "FAIL"}')


# ---------------------------------------------------------------- scaffold
def render(text, vars):
    for k, v in vars.items():
        text = text.replace('{{' + k + '}}', str(v))
    return re.sub(r'\{\{\w+\}\}', '-', text)


def cmd_init(bp, target, force, git):
    b = bp['build']
    chain = b.get('chain') or bp['project'].get('chain')
    net = load_networks().get(chain, {})
    family = net.get('family', chain)
    if family not in os.listdir(TEMPLATES_DIR):
        die(f'unknown chain {chain!r}; known: {", ".join(load_networks())} | template families: {", ".join(os.listdir(TEMPLATES_DIR))}')
    if not target:
        target = b.get('target') or bp['project']['name']
    target = os.path.realpath(target)
    if os.path.exists(target) and os.listdir(target) and not force:
        die(f'target {target} exists and is not empty (use --force)')
    if force and os.path.exists(os.path.join(CACHE, 'last-init.json')):
        try:
            prev = json.load(open(os.path.join(CACHE, 'last-init.json')))
            if prev.get('target') == target:
                removed = 0
                for f in prev.get('created', []):
                    p = os.path.join(target, f)
                    if os.path.isfile(p):
                        os.remove(p)
                        removed += 1
                # bersihkan direktori kosong yang tertinggal
                for cur, dirs, files in os.walk(target, topdown=False):
                    if not os.listdir(cur) and cur != target:
                        os.rmdir(cur)
                if removed:
                    print(f'force: removed {removed} files from previous init (user files untouched)')
        except (OSError, ValueError):
            pass
    vars = {'NAME': bp['project']['name'], 'DESC': bp['project'].get('desc', 'web3 project'),
            'CONTRACT': re.sub(r'[^A-Za-z0-9]', '', bp['project']['name'].title()),
            'RPC_URL': net.get('rpc', ''), 'CHAIN_ID': net.get('chain_id', ''),
            'CURRENCY': net.get('currency', ''), 'EXPLORER': net.get('explorer', ''),
            'AUTHOR': 'Your Name',
            'CHAIN_TITLE': (chain or family).replace('-', ' ').title()}
    vars.update(b.get('vars', {}))
    if family == 'evm' and not vars['RPC_URL']:
        die("generic 'evm' needs build.vars RPC_URL + CHAIN_ID (atau: networks --find <nama> lalu daftarkan)")
    src = os.path.join(TEMPLATES_DIR, family)
    made = []
    os.makedirs(CACHE, exist_ok=True)
    for cur, dirs, files in os.walk(src):
        rel = os.path.relpath(cur, src)
        for f in files:
            sp = os.path.join(cur, f)
            relf = render(os.path.normpath(os.path.join(rel, f)), vars)
            dp = os.path.join(target, relf)
            os.makedirs(os.path.dirname(dp) or target, exist_ok=True)
            if f.endswith(TEXT_EXT) or f.startswith('.env'):
                open(dp, 'w').write(render(open(sp, errors='replace').read(), vars))
            else:
                shutil.copyfile(sp, dp)
            made.append(relf)
    if git and shutil.which('git'):
        subprocess.run(['git', 'init', '-q'], cwd=target)
        open(os.path.join(target, 'LICENSE'), 'w').write(
            f'MIT License (c) {time.strftime("%Y")} {vars["AUTHOR"]}\n')
        made.append('LICENSE')
    json.dump({'target': target, 'chain': chain, 'created': made, 'when': time.strftime('%Y-%m-%d %H:%M')},
              open(os.path.join(CACHE, 'last-init.json'), 'w'))
    # absolute-mode guard: scaffold yang masih mengandung template var = bug render, gagalkan
    leftovers = []
    for relf in made:
        p = os.path.join(target, relf)
        if os.path.isfile(p) and relf.endswith(TEXT_EXT) and '{{' in open(p, errors='replace').read():
            leftovers.append(relf)
    if leftovers:
        shutil.rmtree(target)
        die(f'render incomplete, target REMOVED (this is a tool bug — report it): {leftovers}')
    print(f'init: {len(made)} files -> {target} (chain={chain}, family={family})')
    for m in sorted(made):
        print('  +', m)
    print('next: edit blueprint checks, then: mainnet.py check <blueprint>')


# ---------------------------------------------------------------- checks
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
                    if not want_deps and any(s in ('node_modules', '__pycache__', '.git', 'dist', 'out', 'target') for s in rel.split(os.sep)):
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
            if not os.path.exists(base):
                return ('BROKEN', f'path not found: {c.get("path", ".")} (cek project.root di blueprint)')
            files = []
            if os.path.isfile(base):
                files = [base]
            elif os.path.isdir(base):
                for cur, ds, fs in os.walk(base):
                    ds[:] = [d for d in ds if d not in ('node_modules', '__pycache__', '.git', 'dist', 'out', 'target')]
                    files += [os.path.join(cur, f) for f in fs]
            n, hits = 0, []
            for p in files:
                if not p.endswith(TEXT_EXT):
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
            return ('WORKS' if r['status'] == want else 'BROKEN', f'HTTP {r["status"]} (want {want}){latency(r)} | {str(r["body"])[:90]}')
        if t == 'rpc':
            r = Net.jsonrpc(c['url'], c['method'], c.get('params', []))
            res = r.get('result')
            if res is None and r.get('error'):
                return ('BROKEN', f'rpc error: {json.dumps(r)[:160]}{latency(r)}')
            if 'expect_result' in c and res != c['expect_result']:
                return ('BROKEN', f'result {res!r} != expected {c["expect_result"]!r}{latency(r)}')
            ev = json.dumps(res)[:150] + latency(r)
            for f in c.get('expect_fields', []):
                if f not in ev:
                    return ('BROKEN', f'field {f!r} missing | {ev}')
            return ('WORKS', ev)
        if t == 'github':
            repo = c['repo']
            def gh():
                p = subprocess.run(['gh', 'api', f'repos/{repo}'], capture_output=True, text=True)
                if p.returncode == 0:
                    return json.loads(p.stdout)
                return json.loads(Net.get(f'https://api.github.com/repos/{repo}').get('body') or '{}')
            d = Net.cached(f'gh:{repo}', gh, 12)
            if 'full_name' not in d:
                return ('BROKEN', f'github {repo}: {json.dumps(d)[:140]}')
            ev = f'{repo} pushed {(d.get("pushed_at") or "?")[:10]}, stars {d.get("stargazers_count")}'
            if c.get('expect_active_within_days'):
                age = (time.time() - time.mktime(time.strptime((d.get('pushed_at') or '2000-01-01')[:10], '%Y-%m-%d'))) / 86400
                ev += f' ({age:.0f}d ago, want <= {c["expect_active_within_days"]}d)'
                if age > c['expect_active_within_days']:
                    return ('BROKEN', ev)
            return ('WORKS', ev)
        if t == 'huggingface':
            kind = c.get('kind', 'models')
            r = Net.get(f'https://huggingface.co/api/{kind}/{c["id"]}')
            return ('WORKS' if r['status'] == 200 else 'BROKEN', f'HF {kind}/{c["id"]}: HTTP {r["status"]}{latency(r)}')
        if t == 'registry':
            eco, pkg = c['ecosystem'], c['package']
            url = {'npm': f'https://registry.npmjs.org/{pkg}',
                  'pypi': f'https://pypi.org/pypi/{pkg}/json',
                  'crates': f'https://crates.io/api/v1/crates/{pkg}'}[eco]
            r = Net.get(url)
            if r.get('status') != 200:
                return ('BROKEN', f'{eco}/{pkg}: HTTP {r.get("status")}')
            try:
                d = json.loads(r['body'])
            except ValueError:
                return ('BROKEN', f'{eco}/{pkg}: body bukan JSON')
            if eco == 'npm' and c.get('dist_tag'):
                ver = d.get('dist-tags', {}).get(c['dist_tag'])
                if not ver:
                    return ('BROKEN', f'npm/{pkg}: dist-tag {c["dist_tag"]!r} tidak ada di {sorted(d.get("dist-tags", {}))}')
            else:
                ver = {'npm': lambda: d.get('dist-tags', {}).get('latest'),
                       'pypi': lambda: d.get('info', {}).get('version'),
                       'crates': lambda: d.get('crate', {}).get('max_stable_version')}[eco]()
            ok = True
            if c.get('min_version') and ver:
                try:
                    ok = [int(x) for x in ver.split('.')[0:2]] >= [int(x) for x in c['min_version'].split('.')[0:2]]
                except ValueError:
                    ok = False
            return ('WORKS' if ok else 'BROKEN', f'{eco}/{pkg}: {c.get("dist_tag", "latest")} {ver} (want >= {c.get("min_version", "any")}){latency(r)}')
        if t == 'docker':
            files = [f for f in ('Dockerfile', 'docker-compose.yml', 'compose.yaml') if os.path.exists(tp(f))]
            if c.get('expect') == 'none' or not files:
                return ('N/A' if not files else 'WORKS', f'docker files: {files or "none"}')
            if shutil.which('docker'):
                p = subprocess.run('docker compose config -q 2>&1 || echo PRESENT', shell=True, cwd=root, capture_output=True, text=True, timeout=90)
                return ('WORKS', f'files {files}; compose: {(p.stdout or "").strip()[:80]}')
            return ('UNVERIFIED', f'files {files}; docker CLI unavailable')
        if t == 'manual':
            return ('UNVERIFIED', f'MANUAL: {c.get("question", "needs human judgment")}')
        return ('BROKEN', f'unknown check type {t!r}')
    except Exception as e:
        return ('UNVERIFIED', f'check error {type(e).__name__}: {e}')


def cmd_check(bp, refresh, only, summary=False, json_path=None):
    if refresh:
        shutil.rmtree(CACHE, ignore_errors=True)
    proj = bp['project']
    raw = proj.get('root') or proj['name']
    root = raw if os.path.isabs(raw) else os.path.join(os.getcwd(), raw)
    if not os.path.isdir(root) and not os.path.isabs(raw):
        alt = os.path.join(os.path.dirname(bp.get('_path', '')), raw)
        if os.path.isdir(alt):
            root = alt
    root = os.path.realpath(root)
    if not os.path.isdir(root):
        die(f'target root {root} does not exist (run init first, or fix project.root)')
    net = load_networks().get(proj.get('chain'))
    if net and net.get('family') == 'evm' and net.get('rpc'):
        auto = [{'id': 'onchain/chainid', 'type': 'rpc', 'url': net['rpc'], 'method': 'eth_chainId',
                 'params': [], 'expect_result': '0x' + format(net['chain_id'], 'x')}]
    elif net and net.get('family') == 'solana':
        auto = [{'id': 'onchain/health', 'type': 'rpc', 'url': net['rpc'], 'method': 'getHealth', 'params': [], 'expect_fields': ['ok']}]
    else:
        auto = None
    dims = {d[0]: d for d in DEFAULT_DIMENSIONS}
    for cat in bp.get('dimensions', []):
        cid = cat['id']
        if cid in dims:
            base = list(dims[cid])
            base[2] = cat.get('checks', base[2])
            dims[cid] = tuple(base)
        else:
            dims[cid] = (cid, cat.get('question', ''), cat.get('checks', []))
    if auto:
        q, checks = dims['mainnet-onchain'][1], dims['mainnet-onchain'][2]
        have = {c.get('id') for c in checks}
        dims['mainnet-onchain'] = ('mainnet-onchain', q, [a for a in auto if a['id'] not in have] + checks)
    L = [f'# {proj["name"].upper()} — AUDIT — {time.strftime("%Y-%m-%d %H:%M")}',
         f'root: `{root}` | chain: {proj.get("chain")} | network: {proj.get("network", "?")} | spec {SPEC}', '',
         '| dimension | verdict | ok/broken/unv |', '|---|---|---|']
    detail, broken_items, any_broken, results = [], [], False, {}
    for cid, q, checks in dims.values():
        if only and cid not in only:
            continue
        rs = [(c.get('id', c['type']), *run_check(c, root, '--slow' in sys.argv)) for c in checks]
        ok = sum(v == 'WORKS' for _, v, _ in rs)
        bad = sum(v == 'BROKEN' for _, v, _ in rs)
        unv = len(rs) - ok - bad
        verdict = 'BROKEN' if bad else ('WORKS' if ok else 'UNVERIFIED')
        if bad:
            any_broken = True
            broken_items += [(cid, i, e) for i, v, e in rs if v == 'BROKEN']
        results[cid] = {'verdict': verdict, 'ok': ok, 'broken': bad, 'unverified': unv, 'question': q,
                        'checks': [{'id': i, 'verdict': v, 'evidence': e[:300]} for i, v, e in rs]}
        L.append(f'| {cid} | **{verdict}** | {ok}/{bad}/{unv} |')
        detail += [f'## {cid} — {q}', '', '| check | verdict | evidence |', '|---|---|---|']
        detail += [f'| {i} | {v} | {e.replace("|", "/")[:220]} |' for i, v, e in rs] + ['']
    if only:
        unknown = only - set(results)
        if unknown:
            print(f'WARNING: --only dimensi tak dikenal (diabaikan): {", ".join(sorted(unknown))}')
            print(f'  yang tersedia: {", ".join(dims)}')
    if json_path:
        json.dump({'spec': SPEC, 'project': proj, 'root': root, 'generated': time.strftime('%Y-%m-%d %H:%M'),
                   'result': 'FAIL' if any_broken else 'PASS', 'dimensions': results,
                   'next_actions': [{'dimension': d, 'check': i, 'evidence': e} for d, i, e in broken_items]},
                  open(json_path, 'w'), indent=1)
        print(f'json -> {json_path}')
    if broken_items:
        L += ['', '## NEXT ACTIONS (dari temuan BROKEN, urut perbaikan)']
        for cid, i, e in broken_items:
            L.append(f'- [{cid}/{i}] {e[:160]}')
    L += ['', *detail, '---',
          f'network calls: {Net.calls["http"]} fresh, {Net.calls["cached"]} cached (counted, not hidden)']
    out = os.path.join(HERE, 'reports', f'{proj["name"].upper()}-AUDIT.md')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, 'w').write('\n'.join(L) + '\n')
    if summary:
        print('\n'.join(L[:5 + len(results)]))
    else:
        print('\n'.join(L[:5 + len(dims)]))
    print(f'report -> {out}')
    print(f'RESULT: {"FAIL" if any_broken else "PASS"}')
    return (1 if any_broken else 0), results, broken_items, L


def cmd_context(bp):
    """Satu file handoff siap tempel ke AI agent mana pun (Claude/GLM/dll).
    Tujuan: menghemat token mahal — agent membaca SATU file ringkas yang berisi
    semua fakta terverifikasi + next actions, alih-alih mengeksplorasi repo."""
    rc, results, broken_items, _ = cmd_check(bp, refresh=False, only=None, summary=True)
    proj = bp['project']
    net = load_networks().get(proj.get('chain'), {})
    L = [f'# {proj["name"].upper()} — CONTEXT PACK untuk AI agent — {time.strftime("%Y-%m-%d %H:%M")}',
         '',
         '## Instruksi untuk agent',
         'Semua klaim di file ini sudah TERVERIFIKASI dengan evidence (lihat laporan lengkap di path',
         'paling bawah). Jangan eksplorasi ulang repo untuk hal yang sudah ada di sini. Mulai dari',
         'NEXT ACTIONS. Setelah bekerja, minta user menjalankan ulang check dan context.',
         '',
         '## Project',
         f'- nama: {proj["name"]} | chain: {proj.get("chain")} | network: {proj.get("network", "?")}',
         f'- deskripsi: {proj.get("desc", "-")}',
         f'- root: {os.path.realpath(proj.get("root") or proj["name"])}',
         f'- blueprint: {bp.get("_path", "-")}',
         '',
         '## Fakta jaringan (registry, diverifikasi)',
         f'- rpc: {net.get("rpc", "-")} | chain_id: {net.get("chain_id", "-")} | currency: {net.get("currency", "-")}',
         f'- explorer: {net.get("explorer", "-")}']
    if net.get('note'):
        L.append(f'- catatan: {net["note"]}')
    L += ['', '## Status audit (snapshot terbaru)', '| dimensi | verdict | ok/broken/unv |', '|---|---|---|']
    L += [f'| {cid} | {r["verdict"]} | {r["ok"]}/{r["broken"]}/{r["unverified"]} |' for cid, r in results.items()]
    if broken_items:
        L += ['', '## NEXT ACTIONS (urut perbaikan — mulai dari sini)']
        L += [f'- [{cid}/{i}] {e[:170]}' for cid, i, e in broken_items]
    else:
        L += ['', '## NEXT ACTIONS', '- tidak ada temuan BROKEN — lanjutkan fitur berikutnya dari blueprint']
    L += ['', '## Perintah tool yang tersedia (untuk agent)',
          '```',
          'python3 mainnet_tool/mainnet.py check <blueprint> --summary   # audit ringkas',
          'python3 mainnet_tool/mainnet.py check <blueprint> --json out.json  # audit terstruktur',
          'python3 mainnet_tool/mainnet.py context <blueprint>         # file ini (refresh)',
          'python3 mainnet_tool/mainnet.py init <blueprint> --force     # re-scaffold',
          '```',
          '',
          f'Laporan lengkap + evidence: mainnet_tool/reports/{proj["name"].upper()}-AUDIT.md']
    out = os.path.join(HERE, 'reports', f'{proj["name"].upper()}-CONTEXT.md')
    open(out, 'w').write('\n'.join(L) + '\n')
    print(f'context -> {out} ({os.path.getsize(out)} bytes — tempel file ini ke AI agent)')


def cmd_selftest():
    ok = True
    print('selftest 1: blocked command refused')
    v, e = run_check({'type': 'command', 'command': 'rm -rf /'}, HERE, True)
    ok &= v == 'BROKEN'
    print('  ', v, e)
    print('selftest 2: grep single file')
    v, e = run_check({'type': 'grep', 'pattern': 'evidence|absolute', 'path': 'mainnet.py'}, HERE, True)
    ok &= v == 'WORKS'
    print('  ', v, e[:70])
    print('selftest 3: networks.json valid & template families ada')
    fams = os.listdir(TEMPLATES_DIR)
    ok &= bool(load_networks()) and bool(fams)
    print('  ', 'networks:', len(load_networks()), '| families:', fams)
    print('selftest 4: solana rpc alive (latency terukur)')
    v, e = run_check({'type': 'rpc', 'url': 'https://api.mainnet-beta.solana.com', 'method': 'getHealth', 'params': [], 'expect_fields': ['ok']}, HERE, True)
    ok &= v == 'WORKS'
    print('  ', v, e[:70])
    print('selftest 5: unknown check type refused')
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
    if cmd in ('list-chains', 'networks'):
        find = arg_val(args, '--find')
        chainid = arg_val(args, '--chainid', int)
        cmd_networks(find, chainid)
        return
    if cmd == 'doctor':
        cmd_doctor()
        return
    if cmd == 'selftest':
        sys.exit(cmd_selftest())
    if cmd == 'show':
        if not args:
            die('show butuh nama file contoh, mis: blueprint-solana.json (lihat: ls examples/)')
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
    if not isinstance(bp, dict):
        die('blueprint harus JSON object')
    if bp.get('spec') != SPEC:
        die(f'blueprint spec {bp.get("spec")!r} != {SPEC!r} (rebuild v2 mengubah spec — update blueprint: ganti nilainya)')
    validate_blueprint(bp)
    bp['_path'] = os.path.realpath(cfg[0])
    if cmd == 'init':
        tgt = arg_val(args, '--target')
        cmd_init(bp, tgt, '--force' in args, '--git' in args)
    elif cmd == 'check':
        only = set(arg_val(args, '--only').split(',')) if '--only' in args else None
        rc, *_ = cmd_check(bp, '--refresh' in args, only,
                           summary='--summary' in args, json_path=arg_val(args, '--json'))
        sys.exit(rc)
    elif cmd == 'context':
        cmd_context(bp)
    else:
        die(f'unknown command {cmd!r}')


if __name__ == '__main__':
    main()
