#!/usr/bin/env python3
"""Novelty falsifier: try to KILL an idea by finding prior work. Cached, deterministic.

  novelty-check.py builders        every public GitHub repo that uses the Privacy Rings SDK/program
  novelty-check.py ideas [file]    search prior work for each candidate in candidates.json
  (add --refresh to ignore the 24h cache)

An idea that returns hits is not novel. An idea with zero hits is only "not found in
these sources" — never proof that nobody is building it.
Needs `gh` logged in (GitHub search API).
"""
import json, os, subprocess, sys, time, urllib.parse, urllib.request, hashlib

ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
OUT = os.path.join(ROOT, 'BRAIN', 'research', 'novelty')
RAW = os.path.join(OUT, 'raw')
os.makedirs(RAW, exist_ok=True)
REFRESH = '--refresh' in sys.argv
OWN = ('helius-labs/', 'Lightprotocol/')
MARKERS = ['"@heliuslabs/spr"', 'spr-client language:TOML', 'zolana-client language:TOML',
           'ring1GaLCuJnkUMVkX2JeZLTTX17wKsV4fZmPVzXANW', '"@heliuslabs/spr-web-prover"',
           'getEncryptedUtxosByTags', 'helius-rpc.com/v1/spr']


def cached(key, fn, ttl_h=24):
    path = os.path.join(RAW, hashlib.sha1(key.encode()).hexdigest()[:16] + '.json')
    if not REFRESH and os.path.exists(path) and time.time() - os.path.getmtime(path) < ttl_h * 3600:
        return json.load(open(path))
    data = fn()
    if data is not None:
        json.dump(data, open(path, 'w'))
    return data


def gh(endpoint, pause):
    def call():
        for attempt in range(3):
            p = subprocess.run(['gh', 'api', '-X', 'GET', endpoint], capture_output=True, text=True)
            if p.returncode == 0:
                time.sleep(pause)
                return json.loads(p.stdout)
            if 'rate limit' in (p.stderr + p.stdout).lower():
                time.sleep(65)
                continue
            return {'error': (p.stderr or p.stdout).strip()[:200]}
        return {'error': 'rate limited'}
    return cached(endpoint, call)


def q(s):
    return urllib.parse.quote(s)


def http_json(url):
    def call():
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'research-scanner'})
            time.sleep(1)
            return json.load(urllib.request.urlopen(req, timeout=30))
        except Exception as e:
            return {'error': str(e)[:120]}
    return cached(url, call)


def builders():
    repos, errors = {}, []
    for m in MARKERS:
        for page in (1, 2, 3):
            r = gh(f'search/code?q={q(m)}&per_page=100&page={page}', 7)
            if 'error' in r:
                errors.append(f'{m}: {r["error"]}')
                break
            for it in r.get('items', []):
                full = it['repository']['full_name']
                repos.setdefault(full, {'markers': set(), 'files': 0})
                repos[full]['markers'].add(m.split()[0].strip('"'))
                repos[full]['files'] += 1
            if len(r.get('items', [])) < 100:
                break
        print(f'  marker {m[:44]:44} -> {len(repos)} repos so far')
    rows = []
    for full, info in repos.items():
        d = gh(f'repos/{full}', 0.3)
        if 'error' in d:
            continue
        rows.append({'repo': full, 'own': full.startswith(OWN) or d.get('fork', False), 'fork': d.get('fork', False),
                     'stars': d.get('stargazers_count', 0), 'created': (d.get('created_at') or '')[:10],
                     'pushed': (d.get('pushed_at') or '')[:10], 'desc': (d.get('description') or '').replace('|', '/')[:110],
                     'home': d.get('homepage') or '', 'files': info['files'], 'markers': sorted(info['markers'])})
    rows.sort(key=lambda r: (r['own'], -r['stars'], r['repo']))
    third = [r for r in rows if not r['own']]
    L = [f'# BUILDERS on Privacy Rings — public GitHub repos, generated {time.strftime("%Y-%m-%d %H:%M")}',
         f'{len(rows)} repos reference the SDK/program; {len(third)} are third-party (not helius-labs, not forks).',
         'Private repos and closed-source products are invisible here.', '',
         '| repo | stars | created | pushed | files | description | homepage |', '|---|---|---|---|---|---|---|']
    L += [f"| {r['repo']} | {r['stars']} | {r['created']} | {r['pushed']} | {r['files']} | {r['desc']} | {r['home'][:40]} |" for r in third]
    L += ['', '## helius-labs repos and forks', ', '.join(r['repo'] for r in rows if r['own'])]
    if errors:
        L += ['', '## errors', *errors]
    json.dump(rows, open(os.path.join(OUT, 'builders.json'), 'w'), indent=1)
    open(os.path.join(OUT, 'BUILDERS.md'), 'w').write('\n'.join(L) + '\n')
    print(f'{len(third)} third-party repos -> BRAIN/research/novelty/BUILDERS.md')


def ideas(path):
    cands = json.load(open(path))
    names = []
    if os.path.exists(os.path.join(OUT, 'builders.json')):
        names = [r for r in json.load(open(os.path.join(OUT, 'builders.json'))) if not r['own']]
    L = [f'# NOVELTY LEDGER — generated {time.strftime("%Y-%m-%d %H:%M")}',
         'A hit means prior work exists. Zero hits means "not found in GitHub/npm/CoinGecko", not "nobody is building it".', '']
    summary = []
    for c in cands:
        L += [f"## {c['id']} — {c['title']}", c.get('pitch', ''), '']
        total_hits = 0
        for query in c['queries']:
            r = gh(f'search/repositories?q={q(query)}&sort=stars&per_page=6', 2.2)
            n = r.get('total_count', 0) if 'error' not in r else -1
            L.append(f'- GitHub repos `{query}`: ' + ('ERROR ' + r['error'] if n < 0 else f'{n} hits'))
            for it in (r.get('items') or [])[:6]:
                L.append(f"    - {it['full_name']} ★{it['stargazers_count']} pushed {it['pushed_at'][:10]} — {(it.get('description') or '')[:120]}")
            total_hits += max(n, 0)
        for query in c.get('npm', []):
            r = http_json(f'https://registry.npmjs.org/-/v1/search?text={q(query)}&size=5')
            objs = r.get('objects', [])
            L.append(f'- npm `{query}`: {r.get("total", 0)} hits' + ''.join(
                f"\n    - {o['package']['name']} — {(o['package'].get('description') or '')[:100]}" for o in objs[:5]))
        for query in c.get('coins', []):
            r = http_json(f'https://api.coingecko.com/api/v3/search?query={q(query)}')
            coins = r.get('coins', [])[:6]
            L.append(f'- CoinGecko `{query}`: ' + (', '.join(f"{x['name']} ({x['symbol']}, rank {x.get('market_cap_rank') or '-'})" for x in coins) or 'no coins'))
        rx = [w.lower() for w in c.get('builder_keywords', [])]
        match = [r for r in names if any(w in (r['repo'] + ' ' + r['desc']).lower() for w in rx)]
        L.append(f'- Privacy Rings builders matching {rx}: ' + (', '.join(f"{r['repo']} ({r['desc'][:60]})" for r in match) or 'none'))
        L.append('')
        summary.append((c['id'], c['title'], total_hits, len(match)))
        print(f"  {c['id']:14} github_hits={total_hits:5} ring_builders={len(match)}")
    L[3:3] = ['| id | idea | GitHub hits (all queries) | Privacy Rings builders matching |', '|---|---|---|---|',
              *[f'| {a} | {b} | {c_} | {d} |' for a, b, c_, d in summary], '']
    open(os.path.join(OUT, 'LEDGER.md'), 'w').write('\n'.join(L) + '\n')
    print('ledger -> BRAIN/research/novelty/LEDGER.md')


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else ''
    if cmd == 'builders':
        builders()
    elif cmd == 'ideas':
        args = [a for a in sys.argv[2:] if not a.startswith('--')]
        ideas(args[0] if args else os.path.join(OUT, 'candidates.json'))
    else:
        sys.exit(__doc__)
