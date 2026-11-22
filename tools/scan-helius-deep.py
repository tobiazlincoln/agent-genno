#!/usr/bin/env python3
"""Deep scan: repo trees, spec docs, SDK API surface, competitive intel."""
import json, os, re, sys, time, urllib.request, urllib.error

OUT = os.path.join(os.path.dirname(__file__), '..', 'research', 'helius', 'deep')
os.makedirs(OUT, exist_ok=True)
UA = {'User-Agent': 'Mozilla/5.0 (deep-scanner)'}

def fetch(url, timeout=30):
    try:
        req = urllib.request.Request(url, headers=UA)
        return urllib.request.urlopen(req, timeout=timeout).read().decode('utf-8', 'replace')
    except Exception as e:
        return f'__ERR_{type(e).__name__}__'

def save(name, data):
    p = os.path.join(OUT, name)
    open(p, 'w').write(data)
    print(f'  -> {name} ({len(data)})')

def tree(repo, path=''):
    """List repo tree via GitHub API."""
    u = f'https://api.github.com/repos/helius-labs/{repo}/git/trees/HEAD?recursive=1'
    d = fetch(u)
    if d.startswith('__'): return []
    try:
        return [t['path'] for t in json.loads(d)['tree']]
    except: return []

# 1. repo trees for the key repos
for repo in ['zolana', 'custom-privacy-rings', 'privacy-ring-examples',
             'privacy-ring-web-sdk', 'privacy-ring-mobile-sdk']:
    print(f'[tree] {repo}')
    save(f'tree-{repo}.txt', '\n'.join(tree(repo)))
    time.sleep(0.5)

# 2. custom-privacy-rings spec docs
for doc in ['docs/spec.md', 'docs/design/owner-rails.md', 'docs/design/audit-and-recovery.md',
            'docs/design/records-and-roots.md', 'services/ring-rpc/README.md', 'README.md']:
    d = fetch(f'https://raw.githubusercontent.com/helius-labs/custom-privacy-rings/main/{doc}')
    if not d.startswith('__'):
        save(f'cpr-{doc.replace("/","_")}', d[:40000])
        time.sleep(0.3)

# 3. zolana key spec/design docs
for doc in ['README.md', 'docs/spec.md', 'docs/architecture.md', 'docs/security.md',
            'programs/shielded-pool/README.md', 'sdk-libs/client/README.md']:
    d = fetch(f'https://raw.githubusercontent.com/helius-labs/zolana/main/{doc}')
    if not d.startswith('__'):
        save(f'zolana-{doc.replace("/","_")}', d[:40000])
        time.sleep(0.3)

print('done')
