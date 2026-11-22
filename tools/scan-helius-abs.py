#!/usr/bin/env python3
"""Absolute deep scan: crypto spec, audits, SDK surface, on-chain state, npm."""
import json, os, re, sys, time, urllib.request, urllib.error
OUT = os.path.join(os.path.dirname(__file__), '..', 'Heliusoft', 'research', 'deep')
os.makedirs(OUT, exist_ok=True)
UA = {'User-Agent': 'Mozilla/5.0 (abs-scanner)'}
def fetch(url, timeout=30):
    try:
        return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout).read().decode('utf-8','replace')
    except Exception as e: return f'__ERR_{type(e).__name__}__'
def save(name, data):
    open(os.path.join(OUT, name),'w').write(data); print(f'  -> {name} ({len(data)})')

# 1. crypto spec docs (custom rings sub-specs + zolana spec crypto)
for doc in ['spec/crypto/hashing.md','spec/crypto/envelope.md','spec/crypto/disclosure.md',
            'spec/crypto/public-inputs.md','docs/design/co-signing.md','docs/design/privacy.md',
            'docs/design/record-writer.md','docs/design/proof-composition.md']:
    d = fetch(f'https://raw.githubusercontent.com/helius-labs/custom-privacy-rings/main/{doc}')
    if not d.startswith('__'): save(f'cpr-{doc.replace("/","_")}', d[:40000]); time.sleep(0.3)

# 2. zolana full spec sections (security, audits, fees)
for doc in ['docs/security.md','docs/audits.md','SECURITY.md','docs/fees.md',
            'services/registry/README.md','services/merge-service/README.md',
            'protocol-ops/README.md','prover/README.md','programs/shielded-pool/src/lib.rs']:
    d = fetch(f'https://raw.githubusercontent.com/helius-labs/zolana/main/{doc}')
    if not d.startswith('__'): save(f'zolana-{doc.replace("/","_")}', d[:50000]); time.sleep(0.3)

# 3. npm registry — real package info + versions + files
for pkg in ['@heliuslabs/spr','@heliuslabs/spr-web-prover','helius-sdk','@helius-labs/spr']:
    d = fetch('https://registry.npmjs.org/' + urllib.parse.quote(pkg, safe='@'))
    if not d.startswith('__'):
        try:
            j = json.loads(d)
            latest = j.get('dist-tags',{}).get('latest','?')
            vers = sorted(j.get('versions',{}).keys())[-10:]
            info = {'latest': latest, 'versions': vers,
                    'desc': j.get('description',''),
                    'weekly': None}
            # downloads
            dl = fetch(f'https://api.npmjs.org/downloads/point/last-week/{urllib.parse.quote(pkg, safe="")}')
            if not dl.startswith('__'): info['weekly'] = json.loads(dl).get('downloads')
            save(f'npm-{pkg.replace("/","_").replace("@","")}.json', json.dumps(info, indent=1))
        except Exception as e: save(f'npm-{pkg.replace("/","_")}', d[:500])
    time.sleep(0.3)

# 4. on-chain: program account info via public RPC
prog = 'ring1GaLCuJnkUMVkX2JeZLTTX17wKsV4fZmPVzXANW'
for rpc in ['https://api.mainnet-beta.solana.com']:
    body = json.dumps({"jsonrpc":"2.0","id":1,"method":"getAccountInfo",
        "params":[prog,{"encoding":"base64"}]}).encode()
    try:
        req = urllib.request.Request(rpc, data=body, headers={'Content-Type':'application/json'})
        r = json.loads(urllib.request.urlopen(req, timeout=20).read())
        acc = r.get('result',{}).get('value')
        if acc:
            save('onchain-spp.json', json.dumps({
                'program': prog, 'executable': acc.get('executable'),
                'owner': acc.get('owner'), 'lamports': acc.get('lamports'),
                'data_len': len(acc.get('data',[''])[0]) if acc.get('data') else 0}, indent=1))
            print('  on-chain SPP account:', acc.get('executable'), 'owner', acc.get('owner'))
        else: save('onchain-spp.json', json.dumps(r, indent=1)[:2000])
    except Exception as e: print('  onchain fail:', e)
    break

# 5. crates.io for zolana packages
for crate in ['zolana-client','zolana-interface','zolana-program','spr-client','photon-indexer']:
    d = fetch(f'https://crates.io/api/v1/crates/{crate}')
    if not d.startswith('__'):
        j = json.loads(d)
        v = j.get('crate',{})
        save(f'crate-{crate}.json', json.dumps({'newest': v.get('newest_version'),
             'downloads': v.get('downloads'), 'desc': v.get('description','')}, indent=1))
    time.sleep(0.3)
print('done')
