#!/usr/bin/env python3
"""Behavioural fingerprint of Privacy Rings users (public deposit/withdraw data).

  rings-behaviour.py [--window 604800]

Writes BRAIN/research/rings/BEHAVIOUR.md. Re-run any time; safe on partial data
(coverage is printed). Findings here are design inputs for the leak experiment
and the autopilot: they describe WHAT users currently reveal, not what a fix earns.

Improvements over the one-off analysis:
  - one-to-one greedy matching (a deposit can fund at most one counted round trip)
  - amount-collision statistics (why round amounts make matching ambiguous)
  - cross-address unique matches (the actual leak signal), separated from same-address
"""
import collections, importlib.util, json, os, sys, time

_here = os.path.dirname(os.path.realpath(__file__))
_spec = importlib.util.spec_from_file_location('rings_analyze', os.path.join(_here, 'rings-analyze.py'))
rings_analyze = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rings_analyze)
flows, load, OUT = rings_analyze.flows, rings_analyze.load, rings_analyze.OUT

arg = lambda name, default: type(default)(sys.argv[sys.argv.index(name) + 1]) if name in sys.argv else default
WINDOW = arg('--window', 604800)  # 7d round-trip horizon


def pct(x):
    return f'{100 * x:.1f}%' if x is not None else '-'


def qs(vals, ps=(.1, .25, .5, .75, .9)):
    if not vals:
        return 'n/a'
    s = sorted(vals)
    return ' / '.join(f'p{int(p * 100)}={s[min(int(p * len(s)), len(s) - 1)]:g}' for p in ps)


def main():
    rows = load()
    if not rows:
        sys.exit('no transactions yet')
    deps, wds = collections.defaultdict(list), collections.defaultdict(list)
    fees = []
    for r in rows:
        fees.append(r['fee'])
        for kind, asset, amt, cp in flows(r):
            (deps if kind == 'dep' else wds)[asset].append((r['t'], amt, cp))
    prio_path = os.path.join(OUT, 'priority.json')
    have = {r['sig'] for r in rows}
    cover = 'unknown'
    if os.path.exists(prio_path):
        prio = json.load(open(prio_path))
        n = sum(1 for s in prio['sigs'] if s in have)
        cover = f'{n}/{len(prio["sigs"])} ({pct(n / max(len(prio["sigs"]), 1))}) of deposit/withdraw signatures'
    n_dep, n_wd = sum(map(len, deps.values())), sum(map(len, wds.values()))

    L = [f'# USER BEHAVIOUR FINGERPRINT — generated {time.strftime("%Y-%m-%d %H:%M")}',
         f'Dataset: {len(rows)} successful tx, deposit/withdraw coverage {cover}.',
         'Everything below is read from PUBLIC chain data only. Partial-dataset caveat applies '
         'while coverage < 100%; early activity is dominated by testers and integrators.', '']

    L += ['## Flows', '| asset | deposits | withdrawals | dep volume | wd volume |', '|---|---|---|---|---|']
    for asset in sorted(set(deps) | set(wds), key=lambda a: -(len(deps[a]) + len(wds[a])))[:10]:
        d, w = deps[asset], wds[asset]
        L.append(f'| {asset[:10]} | {len(d)} | {len(w)} | {sum(a for _, a, _ in d):,.2f} | {sum(a for _, a, _ in w):,.2f} |')
    L += [f'- distinct depositors: {len({c for v in deps.values() for _, _, c in v})}; '
          f'distinct withdrawal recipients: {len({c for v in wds.values() for _, _, c in v})}',
          f'- tx fee lamports: {qs(fees)}', '']

    # amount clustering (ambiguity engine)
    L += ['## Amount clustering (why matching is ambiguous)',
          'Exact-amount collisions among deposits: how many OTHER deposits share the same exact amount.',
          'A withdrawal of amount x can be uniquely matched only if few deposits share x.']
    for asset in sorted(deps, key=lambda a: -len(deps[a]))[:4]:
        cnt = collections.Counter(round(a, 6) for _, a, _ in deps[asset])
        n = len(deps[asset])
        lonely = sum(1 for a, c in cnt.items() if c == 1)
        L += [f'- {asset[:10]}: {n} deposits, {len(cnt)} distinct amounts, {lonely} unique '
              f'({pct(lonely / max(len(cnt), 1))} of distinct amounts seen exactly once). '
              f'Top amounts: ' + ', '.join(f'{a:g} x{c}' for a, c in cnt.most_common(6)) + '.']
    L.append('')

    # same-address round trips, one-to-one greedy
    L += [f'## Same-address round trips (deposit -> withdraw to the SAME address, one-to-one matching, {WINDOW // 3600}h horizon)']
    total_rt, gaps, rt_wallets, wd_total = 0, [], set(), 0
    for asset, w in wds.items():
        d = sorted(deps.get(asset, []))
        used = [False] * len(d)
        for t, a, cp in sorted(w):
            wd_total += 1
            best = None
            for j, (dt, da, dcp) in enumerate(d):
                if used[j] or dcp != cp or dt > t or t - dt > WINDOW:
                    continue
                if da < a * 0.99 or da > a * 1.05:
                    continue
                if best is None or dt > d[best][0]:
                    best = j
            if best is not None:
                used[best] = True
                total_rt += 1
                gaps.append(t - d[best][0])
                rt_wallets.add(cp)
    L += [f'- {total_rt} of {wd_total} withdrawals ({pct(total_rt / max(wd_total, 1))}) return to an address that '
          f'deposited a matching amount within the horizon (one-to-one, deposit consumed once).',
          f'- gap seconds: {qs(gaps)}',
          f'- under 1h: {sum(1 for g in gaps if g < 3600)} ({pct(sum(1 for g in gaps if g < 3600) / max(len(gaps), 1))}); '
          f'under 5 min: {sum(1 for g in gaps if g < 300)} ({pct(sum(1 for g in gaps if g < 300) / max(len(gaps), 1))}).',
          f'- {len(rt_wallets)} distinct addresses do this.',
          '', 'This is the trivial, unambiguous leak: no statistical inference needed, the addresses match.',
          'Note: many of these are testers cycling funds, so treat the share as an upper bound on "real" behaviour.']

    # cross-address unique matches (the real leak signal)
    L += ['', '## Cross-address matches (withdraw to a DIFFERENT address, unique amount match within window)']
    for window_h, tol in ((1, 0.01), (24, 0.01)):
        hits = wallets = 0
        for asset, w in wds.items():
            d = sorted(deps.get(asset, []))
            for t, a, cp in sorted(w):
                cands = [(dt, da, dcp) for dt, da, dcp in d if dt <= t < dt + 0 or (dt <= t and t - dt <= window_h * 3600)
                         and dcp != cp and a * 0.99 <= da <= a * (1 + tol)]
                if len(cands) == 1:
                    hits += 1
        L += [f'- window {window_h}h, tolerance {tol:.0%}: {hits} withdrawals ({pct(hits / max(n_wd, 1))}) '
              f'uniquely match one earlier deposit FROM ANOTHER ADDRESS.']
    L += ['', 'These are the interesting cases: the amount that moved privately between two addresses is revealed.',
          'Compare against the null model in LEAK-REPORT.md before reading them as leaks.']

    path = os.path.join(OUT, 'BEHAVIOUR.md')
    open(path, 'w').write('\n'.join(L) + '\n')
    print(f'{len(rows)} tx -> {os.path.relpath(path)}')
    print('\n'.join(L[3:20]))


if __name__ == '__main__':
    main()
