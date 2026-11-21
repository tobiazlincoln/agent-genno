#!/usr/bin/env python3
"""Collect every Privacy Rings (SPP) transaction from public Solana RPC. Resumable.

  rings-collect.py            collect signatures, then fetch all missing transactions
  rings-collect.py status     progress only

Output (BRAIN/research/rings/):
  sigs.jsonl  one signature record per line (newest first within each run)
  tx.jsonl    one compact transaction per line: public balance deltas, signers, ring ix data
Only public data is read. Nothing is decrypted.
Set HELIUS_API_KEY to add a faster endpoint.
"""
import json, os, sys, threading, time, urllib.request, queue

ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
OUT = os.path.join(ROOT, 'BRAIN', 'research', 'rings')
os.makedirs(OUT, exist_ok=True)
SIGS, TX = os.path.join(OUT, 'sigs.jsonl'), os.path.join(OUT, 'tx.jsonl')
PROGRAM = 'ring1GaLCuJnkUMVkX2JeZLTTX17wKsV4fZmPVzXANW'
# (url, threads, seconds between requests per thread)
ENDPOINTS = [('https://api.mainnet-beta.solana.com', 2, 0.55), ('https://solana-rpc.publicnode.com', 2, 0.35),
             ('https://public.rpc.solanavibestation.com', 2, 0.5)]
# Pool vaults: deposits and withdrawals are the only transactions that touch them (private transfers do not).
SOL_VAULT = 'CiNmas621VuyofiDSrEPfTXHKrdZuB6jMKECyNiMpLXE'
TOKEN_AUTHORITY = 'CaM8DbtJ2mSecgaHYo9xeT7VSKq7AnaqEUm5p7e5LW4a'
TOKEN_PROGRAMS = ('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA', 'TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb')
PRIORITY = os.path.join(OUT, 'priority.json')
if os.environ.get('HELIUS_API_KEY'):
    ENDPOINTS.append((f"https://mainnet.helius-rpc.com/?api-key={os.environ['HELIUS_API_KEY']}", 4, 0.45))
lock = threading.Lock()


def rpc(url, method, params):
    req = urllib.request.Request(url, json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params}).encode(),
                                 {'Content-Type': 'application/json', 'User-Agent': 'research-scanner'})
    return json.load(urllib.request.urlopen(req, timeout=30))


def load(path, key):
    seen = {}
    if os.path.exists(path):
        for line in open(path):
            try:
                r = json.loads(line)
                seen[r[key]] = r
            except ValueError:
                pass
    return seen


def collect_sigs():
    seen = load(SIGS, 'signature')
    url, before, new = ENDPOINTS[0][0], None, 0
    with open(SIGS, 'a') as f:
        while True:
            opts = {'limit': 1000, **({'before': before} if before else {})}
            for attempt in range(6):
                try:
                    page = rpc(url, 'getSignaturesForAddress', [PROGRAM, opts])['result']
                    break
                except Exception:
                    time.sleep(3 * (attempt + 1))
            else:
                sys.exit('signature paging failed repeatedly; re-run to resume')
            if not page:
                break
            fresh = [s for s in page if s['signature'] not in seen]
            for s in fresh:
                rec = {'signature': s['signature'], 'slot': s['slot'], 'blockTime': s.get('blockTime'), 'err': bool(s.get('err'))}
                seen[s['signature']] = rec
                f.write(json.dumps(rec) + '\n')
            new += len(fresh)
            before = page[-1]['signature']
            print(f'  sigs: {len(seen)} total (+{new} new), reached {time.strftime("%Y-%m-%d %H:%M", time.gmtime(page[-1].get("blockTime") or 0))} UTC', flush=True)
            # everything older than a fully-known page was collected by an earlier run
            if not fresh and new == 0 and len(seen) > 1000:
                oldest = min(seen.values(), key=lambda r: r['slot'])
                if page[-1]['slot'] > oldest['slot']:
                    before = oldest['signature']
                    continue
            if len(page) < 1000:
                break
            time.sleep(0.6)
    return seen


def retry(method, params, tries=6):
    for attempt in range(tries):
        for url, _, _ in ENDPOINTS[:2]:
            try:
                r = rpc(url, method, params)
                if 'result' in r:
                    return r['result']
            except Exception:
                pass
        time.sleep(2 * (attempt + 1))
    return None


def priority_sigs():
    """Signatures that touch a pool vault = every public deposit and withdrawal. Cached 6h."""
    if os.path.exists(PRIORITY) and time.time() - os.path.getmtime(PRIORITY) < 6 * 3600:
        return json.load(open(PRIORITY))
    vaults = [SOL_VAULT]
    for prog in TOKEN_PROGRAMS:
        res = retry('getTokenAccountsByOwner', [TOKEN_AUTHORITY, {'programId': prog}, {'encoding': 'base64', 'dataSlice': {'offset': 0, 'length': 0}}])
        vaults += [a['pubkey'] for a in (res or {}).get('value', [])]
        time.sleep(0.6)
    print(f'  vault accounts: {len(vaults)} (1 SOL + {len(vaults) - 1} token)', flush=True)
    out, failed = {}, 0
    for n, v in enumerate(vaults):
        before = None
        while True:
            page = retry('getSignaturesForAddress', [v, {'limit': 1000, **({'before': before} if before else {})}])
            if page is None:
                failed += 1
                break
            for s in page:
                out[s['signature']] = s['slot']
            if len(page) < 1000:
                break
            before = page[-1]['signature']
            time.sleep(0.5)
        time.sleep(0.45)
        if n % 25 == 0:
            print(f'  vault {n + 1}/{len(vaults)}: {len(out)} deposit/withdraw signatures', flush=True)
    data = {'vaults': len(vaults), 'failed_vaults': failed, 'sigs': sorted(out, key=out.get)}
    if not failed:
        json.dump(data, open(PRIORITY, 'w'))
    print(f'  priority set: {len(out)} signatures, {failed} vaults failed', flush=True)
    return data


def compact(sig, tx):
    m, msg = tx['meta'], tx['transaction']['message']
    keys = list(msg['accountKeys']) + (m.get('loadedAddresses') or {}).get('writable', []) + (m.get('loadedAddresses') or {}).get('readonly', [])
    sol = [[i, post - pre] for i, (pre, post) in enumerate(zip(m['preBalances'], m['postBalances'])) if post != pre]
    pre_t = {b['accountIndex']: b for b in m.get('preTokenBalances') or []}
    post_t = {b['accountIndex']: b for b in m.get('postTokenBalances') or []}
    tok = []
    for i in sorted(set(pre_t) | set(post_t)):
        b = post_t.get(i) or pre_t[i]
        d = int((post_t.get(i) or {'uiTokenAmount': {'amount': '0'}})['uiTokenAmount']['amount']) - \
            int((pre_t.get(i) or {'uiTokenAmount': {'amount': '0'}})['uiTokenAmount']['amount'])
        if d:
            tok.append([i, b['mint'], b.get('owner'), str(d), b['uiTokenAmount']['decimals']])
    ring = keys.index(PROGRAM) if PROGRAM in keys else -1
    ix = [{'a': i['accounts'], 'd': i['data']} for i in msg['instructions'] if i['programIdIndex'] == ring]
    inner = sum(len(g['instructions']) for g in m.get('innerInstructions') or [])
    return {'sig': sig, 'slot': tx['slot'], 't': tx.get('blockTime'), 'err': bool(m.get('err')), 'fee': m['fee'],
            'nsig': msg['header']['numRequiredSignatures'], 'keys': keys, 'sol': sol, 'tok': tok, 'ix': ix,
            'inner': inner, 'v': tx.get('version')}


def worker(url, pause, todo, out, stats):
    while True:
        try:
            sig = todo.get_nowait()
        except queue.Empty:
            return
        delay = pause
        for attempt in range(8):
            try:
                r = rpc(url, 'getTransaction', [sig, {'encoding': 'json', 'maxSupportedTransactionVersion': 1, 'commitment': 'finalized'}])
                if r.get('result'):
                    rec = compact(sig, r['result'])
                    with lock:
                        out.write(json.dumps(rec, separators=(',', ':')) + '\n')
                        out.flush()
                        stats['ok'] += 1
                    break
                if 'error' in r and r['error'].get('code') not in (429, -32005):
                    with lock:
                        stats['bad'] += 1
                        stats['last_err'] = str(r['error'])[:120]
                    break
            except Exception as e:
                with lock:
                    stats['retry'] += 1
                    stats['last_err'] = str(e)[:80]
            delay = min(delay * 2, 20)
            time.sleep(delay)
        else:
            with lock:
                stats['bad'] += 1
        time.sleep(pause)


def status():
    sigs, txs = load(SIGS, 'signature'), load(TX, 'sig')
    ts = [r['blockTime'] for r in sigs.values() if r.get('blockTime')]
    span = f"{time.strftime('%Y-%m-%d', time.gmtime(min(ts)))} -> {time.strftime('%Y-%m-%d %H:%M', time.gmtime(max(ts)))} UTC" if ts else '-'
    print(f'signatures: {len(sigs)} ({span}), failed on chain: {sum(r["err"] for r in sigs.values())}')
    print(f'transactions fetched: {len(txs)} / {len(sigs)} ({100 * len(txs) / max(len(sigs), 1):.1f}%)')
    return sigs, txs


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'status':
        status()
        sys.exit(0)
    print('phase 1: signatures', flush=True)
    collect_sigs()
    sigs, txs = status()
    print('phase 1b: deposit/withdraw signatures (fetched first)', flush=True)
    prio = priority_sigs()['sigs']
    pset = set(prio)
    print(f'  priority: {len(pset)} total, {sum(1 for s in pset if s not in txs)} still to fetch', flush=True)
    todo = queue.Queue()
    for sig in prio + [s['signature'] for s in sorted(sigs.values(), key=lambda r: r['slot']) if s['signature'] not in pset]:
        if sig not in txs:
            todo.put(sig)
    total, stats, t0 = todo.qsize(), {'ok': 0, 'bad': 0, 'retry': 0, 'last_err': ''}, time.time()
    print(f'phase 2: fetching {total} transactions from {len(ENDPOINTS)} endpoints', flush=True)
    with open(TX, 'a') as out:
        threads = [threading.Thread(target=worker, args=(u, p, todo, out, stats), daemon=True)
                   for u, n, p in ENDPOINTS for _ in range(n)]
        [t.start() for t in threads]
        while any(t.is_alive() for t in threads):
            time.sleep(30)
            done = stats['ok'] + stats['bad']
            rate = done / max(time.time() - t0, 1)
            print(f"  {done}/{total} ok={stats['ok']} bad={stats['bad']} retries={stats['retry']} "
                  f"{rate:.1f} tx/s eta {((total - done) / max(rate, 0.01)) / 60:.0f} min | {stats['last_err']}", flush=True)
    print(f"done: ok={stats['ok']} bad={stats['bad']}", flush=True)
    status()
