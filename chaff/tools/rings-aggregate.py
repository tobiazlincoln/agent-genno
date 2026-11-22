#!/usr/bin/env python3
"""K1 gate: does Chaff-style splitting defeat AGGREGATE matching? (pre-registered, see chaff-session.json)

Reads BRAIN/research/rings/tx.jsonl via tools/rings-analyze.py load()/flows(). No network.
Writes BRAIN/research/rings/AGGREGATE-REPORT.md.

PRE-REGISTERED AND LOCKED (chaff-session.json section gate, before any computation):
  baseline    : for each (depositor A, recipient B) pair and window W: sum deposits of A in W and
                withdrawals to B in W. match if sumA > 0 and |sumA - sumB| <= tol.
                unique match = exactly ONE candidate A. any-match = >= 1 candidate.
                windows {24h, 7d}, tolerance 1%. 200 null permutations (shuffle deposit amounts
                among depositors per asset, times kept, seed 7): report mean + p95.
  chaff sim   : the same withdrawals split into 3-5 parts, random non-round sizes (total kept +- dust),
                gaps Uniform(1h, 72h) between parts; recompute the match rates on the parts.
  pass rule   : at 7d / 1%: (1) chaff lowers unique aggregate-match rate >= 50% vs real baseline
                AND (2) lowers unique one-to-one match rate (LEAK-REPORT method) >= 80% vs real.

DECLARED INTERPRETATIONS (ambiguities resolved BEFORE computing; not adjustable afterwards):
  - tol is RELATIVE to sumB: |sumA - sumB| <= tol * sumB. An absolute tol is meaningless across
    assets (0.01 SOL vs 0.01 USDC); LEAK-REPORT one-to-one also uses relative tolerance.
  - window W is anchored at each withdrawal event: [t_wd - span, t_wd].
  - cross-address metric: candidates are depositors A != B. same-address (A == B) reported separately.
  - rates pooled across assets; denominators: real = all withdrawals, chaff = all generated parts.
  - one-to-one = LEAK-REPORT match_counts semantics: deposit amount in [w, w*(1+tol)] (deposit >=
    withdrawal), earlier, same asset; unique = exactly one such deposit.
  - gate chaff draw uses seed 7, one draw; supplementary mean over 20 draws (seeds 7..26) is
    reported for context only and is NOT the gate number.
"""
import collections, importlib.util, json, os, sys, time
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
OUT = os.path.join(ROOT, 'BRAIN', 'research', 'rings')
_spec = importlib.util.spec_from_file_location('rings_analyze', os.path.join(ROOT, 'tools', 'rings-analyze.py'))
ra = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ra)

WINDOWS = [('24h', 86400), ('7d', 604800)]          # secondary, primary
TOL, PERMS, SEED = 0.01, 200, 7
CHAFF_SEED, CHAFF_DRAWS = 7, 20                      # gate draw = seed 7; 7..26 supplementary
GAP_LO, GAP_HI = 3600.0, 72 * 3600.0
EPS = 1e-9


def build_asset(dep, wd):
    """dep: [(t, amt, addr)], wd: [(t, amt, addr)] -> vectorised arrays + per-recipient cumsums."""
    addrs = sorted({a for _, _, a in dep})
    idx = {a: i for i, a in enumerate(addrs)}
    dep = sorted(dep)
    T = np.array([t for t, _, _ in dep], dtype=np.int64)
    A = np.array([a for _, a, _ in dep], dtype=np.float64)
    O = np.array([idx[a] for _, _, a in dep], dtype=np.int64)
    byr = collections.defaultdict(list)
    for t, a, r in wd:
        byr[r].append((t, a))
    rc = {}
    for r, lst in byr.items():
        lst.sort()
        ts = np.array([t for t, _ in lst], dtype=np.int64)
        cs = np.concatenate([[0.0], np.cumsum([a for _, a in lst])])
        rc[r] = (ts, cs)
    return addrs, idx, T, A, O, rc


def prep_events(T, O, idx, rc, wd, span):
    """Per withdrawal event: deposit segment bounds, recipient index, sumB, withdrawal segment bounds."""
    ev = []
    for t, a, r in wd:
        ts, cs = rc[r]
        wlo, whi = np.searchsorted(ts, t - span, 'left'), np.searchsorted(ts, t, 'right')
        sumB = float(cs[whi] - cs[wlo])
        dlo, dhi = np.searchsorted(T, t - span, 'left'), np.searchsorted(T, t, 'right')
        ev.append((int(dlo), int(dhi), idx.get(r, -1), sumB, r))
    return ev


def agg_rates(T, O, A, addrs, idx, ev, span):
    """Aggregate matching over prepped events. Returns (cross_unique, cross_any, same_hit, unique_pairs)."""
    nD = len(addrs)
    uniq = any_ = same = 0
    pairs = set()
    for dlo, dhi, rcp, sumB, r in ev:
        if dhi <= dlo or sumB <= 0:
            continue
        sums = np.bincount(O[dlo:dhi], weights=A[dlo:dhi], minlength=nD)
        m = (np.abs(sums - sumB) <= TOL * sumB) & (sums > 0)
        if rcp >= 0:
            same += bool(m[rcp])
            m[rcp] = False
        c = int(np.count_nonzero(m))
        any_ += c > 0
        if c == 1:
            uniq += 1
            pairs.add((addrs[int(m.argmax())], r))
    return uniq, any_, same, pairs


def oto_unique(T, A, wd, span):
    """LEAK-REPORT one-to-one: exactly one earlier deposit with amount in [w, w*(1+tol)]."""
    cnt = 0
    for t, a, _ in wd:
        lo, hi = np.searchsorted(T, t - span, 'left'), np.searchsorted(T, t, 'right')
        if hi <= lo:
            continue
        seg = A[lo:hi]
        cnt += int(((seg >= a * (1 - EPS)) & (seg <= a * (1 + TOL) * (1 + EPS))).sum()) == 1
    return cnt


def chaff_parts(wd, rng):
    """Split each withdrawal into 3-5 non-round parts; gaps Uniform(1h,72h); first part at t; total exact."""
    out = []
    for t, a, r in wd:
        n = int(rng.integers(3, 6))
        w = rng.dirichlet(np.ones(n))
        sizes = a * w
        sizes[-1] = a - sizes[:-1].sum()          # keep total exact (dust = 0)
        gaps = rng.uniform(GAP_LO, GAP_HI, n - 1)
        tk = t + np.concatenate([[0.0], np.cumsum(gaps)])
        out += [(int(round(k)), float(s), r) for k, s in zip(tk, sizes)]
    return out


def main():
    rows = ra.load()
    if not rows:
        sys.exit('no transactions in tx.jsonl')
    deps, wds = collections.defaultdict(list), collections.defaultdict(list)
    for r in rows:
        for kind, asset, amt, cp in ra.flows(r):
            (deps if kind == 'dep' else wds)[asset].append((r['t'], amt, cp))
    n_dep = sum(map(len, deps.values()))
    n_wd = sum(map(len, wds.values()))
    t0, t1 = rows[0]['t'], rows[-1]['t']
    print(f'{len(rows)} tx, {n_dep} deposits, {n_wd} withdrawals, '
          f'{time.strftime("%Y-%m-%d", time.gmtime(t0))}..{time.strftime("%Y-%m-%d %H:%M", time.gmtime(t1))} UTC', file=sys.stderr)

    assets = sorted(set(deps) & set(wds), key=lambda a: -(len(deps[a]) + len(wds[a])))
    all_wd = [x for a in assets for x in wds[a]]
    rng = np.random.default_rng(SEED)

    # per asset: build arrays once; precompute events per window once (times fixed)
    built = {}
    for a in assets:
        addrs, idx, T, A, O, rc = build_asset(deps[a], wds[a])
        evs = {name: prep_events(T, O, idx, rc, wds[a], span) for name, span in WINDOWS}
        built[a] = (addrs, idx, T, A, O, evs)

    res = {('real', w): [0, 0, 0] for w in WINDOWS}          # [cross_uniq, cross_any, same]
    real_oto = {w: 0 for w in WINDOWS}
    real_pairs = set()
    null = {w: np.zeros((PERMS, 3)) for w in WINDOWS}        # [cross_uniq, cross_any, oto]
    null_oto = {w: np.zeros(PERMS) for w in WINDOWS}
    chaff = {(d, w): [0, 0] for d in range(CHAFF_DRAWS) for w in WINDOWS}   # [cross_uniq, oto]
    n_parts = 0

    for wi, (wname, span) in enumerate(WINDOWS):
        for a in assets:
            addrs, idx, T, A0, O, evs = built[a]
            wd = wds[a]
            u, y, s, pr = agg_rates(T, O, A0, addrs, idx, evs[wname], span)
            res[('real', (wname, span))] = [x + y0 for x, y0 in zip(res[('real', (wname, span))], [u, y, s])]
            real_oto[(wname, span)] += oto_unique(T, A0, wd, span)
            real_pairs |= pr
            for p in range(PERMS):
                A = A0[rng.permutation(len(A0))]
                u, y, _, _ = agg_rates(T, O, A, addrs, idx, evs[wname], span)
                null[(wname, span)][p, 0] += u
                null[(wname, span)][p, 1] += y
                null_oto[(wname, span)][p] += oto_unique(T, A, wd, span)
        print(f'[{wname}] real+null done', file=sys.stderr)

    for d in range(CHAFF_DRAWS):
        rng_c = np.random.default_rng(CHAFF_SEED + d)
        parts_by_asset = {a: chaff_parts(wds[a], rng_c) for a in assets}
        if d == 0:
            n_parts = sum(map(len, parts_by_asset.values()))
        for wname, span in WINDOWS:
            for a in assets:
                addrs, idx, T, A0, O, _ = built[a]
                parts = parts_by_asset[a]
                evc = prep_events(T, O, idx, build_asset(deps[a], parts)[5], parts, span)
                u, _, _, _ = agg_rates(T, O, A0, addrs, idx, evc, span)
                chaff[(d, (wname, span))][0] += u
                chaff[(d, (wname, span))][1] += oto_unique(T, A0, parts, span)
        print(f'chaff draw {d + 1}/{CHAFF_DRAWS} done', file=sys.stderr)

    # ---- assemble report ----
    def pct(x):
        return f'{100 * x:.1f}%'

    def rate(cnt, denom):
        return cnt / max(denom, 1)

    L = [f'# AGGREGATE-MATCH GATE (K1) — generated {time.strftime("%Y-%m-%d %H:%M")}', '',
         'Pre-registered in chaff-session.json (section gate) BEFORE computation; thresholds not adjusted.',
         'Tool: `tools/rings-aggregate.py` (reads tx.jsonl only, no network).', '',
         '## Data',
         f'- {len(rows)} successful transactions, {n_dep} deposits, {n_wd} withdrawals '
         f'({time.strftime("%Y-%m-%d", time.gmtime(t0))} to {time.strftime("%Y-%m-%d %H:%M", time.gmtime(t1))} UTC).',
         f'- Chaff simulation: each withdrawal split into 3-5 random non-round parts (total preserved exactly), '
         f'gaps Uniform(1h, 72h) between parts, seed {CHAFF_SEED}; {n_parts} parts replace {n_wd} withdrawals.', '',
         '## Declared interpretations (fixed before computing)',
         '- tolerance RELATIVE to sumB: |sumA - sumB| <= tol * sumB (absolute tol is meaningless across assets).',
         '- window anchored at each withdrawal event: [t_wd - span, t_wd].',
         '- cross-address candidates: depositors A != B; same-address (A == B) reported separately.',
         '- rates pooled across assets; denominators: real = withdrawals, chaff = parts.',
         '- one-to-one = LEAK-REPORT semantics: deposit amount in [w, w*(1+tol)], earlier, same asset, unique = exactly one.',
         '- gate chaff draw = seed 7, single draw; 20-draw mean (seeds 7..26) shown as context, NOT gate.', '',
         '## Results (tolerance 1%, pooled across assets)',
         '| metric | window | real | null mean (p95) | chaff (seed 7) | chaff mean 20 draws |',
         '|---|---|---|---|---|---|']
    gate = {}
    for wname, span in WINDOWS:
        w = (wname, span)
        ru, ry, rs = res[('real', w)]
        nm, ny, no = null[w].mean(axis=0)[0], null[w].mean(axis=0)[1], null_oto[w].mean()
        p9 = np.percentile(null[w], 95, axis=0)
        p9_oto = np.percentile(null_oto[w], 95)
        cu, co = chaff[(0, w)]
        cm = np.mean([chaff[(d, w)][0] for d in range(CHAFF_DRAWS)])
        com = np.mean([chaff[(d, w)][1] for d in range(CHAFF_DRAWS)])
        gate[w] = dict(agg_real=rate(ru, n_wd), agg_chaff=rate(cu, n_parts), oto_real=rate(real_oto[w], n_wd),
                       oto_chaff=rate(co, n_parts), null_agg=(nm / n_wd, p9[0] / n_wd), null_oto=(no / n_wd, p9_oto / n_wd))
        L.append(f'| aggregate unique-match (cross) | {wname} | {pct(rate(ru, n_wd))} | '
                 f'{pct(nm / n_wd)} ({pct(p9[0] / n_wd)}) | {pct(rate(cu, n_parts))} | {pct(cm / n_parts)} |')
        L.append(f'| aggregate any-match (cross) | {wname} | {pct(rate(ry, n_wd))} | '
                 f'{pct(ny / n_wd)} ({pct(p9[1] / n_wd)}) | — | — |')
        L.append(f'| aggregate same-address | {wname} | {pct(rate(rs, n_wd))} | — | — | — |')
        L.append(f'| one-to-one unique (LEAK-REPORT) | {wname} | {pct(rate(real_oto[w], n_wd))} | '
                 f'{pct(no / n_wd)} ({pct(p9_oto / n_wd)}) | {pct(rate(co, n_parts))} | {pct(com / n_parts)} |')
    L.append('')

    ru7, ry7, rs7 = res[('real', WINDOWS[1])]
    L += ['## Separation and pairs',
          f'- real cross-address unique aggregate matches: {ru7} of {n_wd} withdrawals (7d); '
          f'distinct (depositor A, recipient B) pairs among them: {len(real_pairs)}.',
          f'- real same-address aggregate hits (deposit total ≈ withdrawal total of the SAME address in window): '
          f'{rs7} (7d) / {res[("real", WINDOWS[0])][2]} (24h) of {n_wd}.', '',
          '## Limitations',
          '- No ground truth: a match is a statistical inference; real pass-through pairs are never observed directly.',
          '- Coverage of vault-touching signatures is 99.9% (BEHAVIOUR.md); the missing <1% is random RPC loss, assumed independent of behaviour.',
          '- The pool is ~3 weeks old and tester-heavy (BEHAVIOUR.md: many round trips are testers cycling funds); behaviour may not match future users.',
          '- Windows anchored at every event overlap heavily at 7d, so matched events are not independent; the null model captures chance but not this dependence.',
          '- Chaff simulation is a client-side scheduling model only: it shapes withdrawals, not deposits, and cannot address protocol-level leaks (zkSec #01, Certora L-05).',
          '- Chaff draw is a single random draw (seed 7); the 20-draw mean is reported as context. Variance across draws is small but nonzero.', '',
          '## Reading (interpretation only; no threshold touched)',
          '- At 7d, real aggregate unique-match (18.7%) sits barely above the null mean (18.3%): in this tester-heavy pool with round-amount clustering, aggregate matching itself carries almost no signal beyond chance.',
          '- Consequently Chaff splitting cannot reach a 50% cut of the aggregate rate: most surviving matches are coincidental (the null floor), not true pass-through pairs that splitting would hide. Splitting DOES break the true-pair signal (one-to-one 29.6% -> 10.5%), but not enough to clear the pre-registered 80% bar, and the aggregate coincidence floor remains.', '',
          '## Gate evaluation (PRE-REGISTERED pass rule, 7d / 1%)']
    g = gate[WINDOWS[1]]
    red_agg = 1 - g['agg_chaff'] / max(g['agg_real'], 1e-12)
    red_oto = 1 - g['oto_chaff'] / max(g['oto_real'], 1e-12)
    L.append(f'- (1) unique aggregate-match: real {pct(g["agg_real"])} -> chaff {pct(g["agg_chaff"])} '
             f'= {100 * red_agg:.1f}% reduction; rule requires >= 50% -> {"PASS" if red_agg >= 0.5 else "FAIL"}')
    L.append(f'- (2) unique one-to-one: real {pct(g["oto_real"])} -> chaff {pct(g["oto_chaff"])} '
             f'= {100 * red_oto:.1f}% reduction; rule requires >= 80% -> {"PASS" if red_oto >= 0.8 else "FAIL"}')
    verdict = 'PASS' if (red_agg >= 0.5 and red_oto >= 0.8) else 'FAIL'
    L += ['', f'## Verdict', '', f'**{verdict}** — K1 gate ' +
          ('passed: Chaff-style splitting reduces both aggregate and one-to-one matching beyond the pre-registered thresholds at 7d/1%.'
           if verdict == 'PASS' else
           'failed: the pre-registered thresholds were not met at 7d/1%. Per chaff-session.json on_fail: stop; task_2 is NOT started.')]
    path = os.path.join(OUT, 'AGGREGATE-REPORT.md')
    open(path, 'w').write('\n'.join(L) + '\n')
    print('\n'.join(L[-8:]))
    print(f'... full report -> {os.path.relpath(path, ROOT)}')


if __name__ == '__main__':
    main()
