#!/usr/bin/env python3
"""Deterministic Helius intelligence scanner.
Fetches docs index, GitHub repos, and public X mirrors ONCE, caches to disk.
Re-run only for refresh. Usage: python3 tools/scan-helius.py [docs|github|x|all]
"""
import json, os, re, sys, time, urllib.request, urllib.error

OUT = os.path.join(os.path.dirname(__file__), '..', 'research', 'helius')
os.makedirs(OUT, exist_ok=True)
UA = {'User-Agent': 'Mozilla/5.0 (research-scanner)'}

def fetch(url, timeout=30, binary=False):
    try:
        req = urllib.request.Request(url, headers=UA)
        r = urllib.request.urlopen(req, timeout=timeout)
        return r.read() if binary else r.read().decode('utf-8', 'replace')
    except urllib.error.HTTPError as e:
        return f'__HTTP_{e.code}__'
    except Exception as e:
        return f'__ERR_{type(e).__name__}:{e}__'

def save(name, data):
    p = os.path.join(OUT, name)
    mode = 'wb' if isinstance(data, bytes) else 'w'
    with open(p, mode) as f:
        f.write(data)
    print(f'  -> {name} ({len(data)} bytes)')

def scan_docs():
    print('[docs] fetching helius docs index...')
    idx = fetch('https://www.helius.dev/docs/llms.txt')
    save('docs-llms.txt', idx)
    if idx.startswith('__'): return
    # extract all privacy-related doc urls
    urls = sorted(set(re.findall(r'https://www\.helius\.dev/docs/[^\s)\]]+', idx)))
    priv = [u for u in urls if 'privacy' in u]
    print(f'[docs] {len(urls)} total urls, {len(priv)} privacy pages')
    bundle = []
    for u in priv:
        body = fetch(u if u.endswith('.md') else u + '.md')
        if body.startswith('__'):
            body = fetch(u)
        bundle.append(f'\n\n========== {u} ==========\n{body[:15000]}')
        time.sleep(0.3)
    save('docs-privacy-all.txt', ''.join(bundle))
    # key non-privacy pages
    for slug, name in [('/pricing', 'page-pricing.txt'), ('/docs/api-reference/privacy', 'page-privacy-api.txt')]:
        b = fetch('https://www.helius.dev' + slug)
        if not b.startswith('__'):
            save(name, re.sub(r'<[^>]+>', ' ', b)[:20000])

def scan_github():
    print('[github] fetching helius-labs org repos...')
    repos = []
    for page in (1, 2, 3):
        d = fetch(f'https://api.github.com/orgs/helius-labs/repos?per_page=100&page={page}&sort=updated')
        if d.startswith('__'): break
        arr = json.loads(d)
        if not arr: break
        repos += arr
    save('github-repos.json', json.dumps(repos, indent=1))
    summary = []
    interesting = ['zolana', 'privacy', 'spr', 'helius', 'photon']
    for r in repos:
        line = f"{r['name']:35s} ★{r['stargazers_count']:5d} {r.get('language') or '-':12s} {r['description'] or ''}"
        summary.append(line)
    save('github-repos-summary.txt', '\n'.join(sorted(summary)))
    # fetch READMEs of the most relevant repos
    key = [r['name'] for r in repos if any(k in r['name'].lower() for k in interesting)]
    key += ['zolana', 'privacy-rings', 'privacy-ring-examples', 'zolana-examples']
    seen = set()
    for name in key:
        if name in seen: continue
        seen.add(name)
        for br in ('main', 'master'):
            rd = fetch(f'https://raw.githubusercontent.com/helius-labs/{name}/{br}/README.md')
            if not rd.startswith('__'):
                save(f'repo-{name}-README.md', rd[:20000])
                break

def scan_x():
    print('[x] fetching @helius timeline via nitter mirrors...')
    mirrors = ['https://nitter.net', 'https://nitter.poast.org', 'https://nitter.privacydev.net']
    for m in mirrors:
        html = fetch(m + '/helius', timeout=20)
        if not html.startswith('__') and 'timeline' in html.lower():
            tweets = re.findall(r'class="tweet-content[^"]*"[^>]*>(.*?)</div>', html, re.S)
            cleaned = [re.sub(r'<[^>]+>', ' ', t).strip()[:500] for t in tweets]
            save('x-helius-timeline.txt', '\n---\n'.join(cleaned))
            print(f'  nitter ok via {m}: {len(cleaned)} tweets')
            return
    print('  all nitter mirrors failed')
    save('x-helius-timeline.txt', 'FAILED: nitter mirrors unreachable')

if __name__ == '__main__':
    which = sys.argv[1] if len(sys.argv) > 1 else 'all'
    if which in ('docs', 'all'): scan_docs()
    if which in ('github', 'all'): scan_github()
    if which in ('x', 'all'): scan_x()
    print('done. output in', os.path.abspath(OUT))
