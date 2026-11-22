#!/usr/bin/env python3
"""POST-HOC diagnostic (NOT the gate): is matching on chaffed parts above chance?

Gate K1 FAILED and its verdict (BRAIN/research/rings/AGGREGATE-REPORT.md) stands untouched.
The gate's null model was computed on unsplit withdrawals. This script computes the null
(shuffle deposit amounts among depositors, times kept, seed 7, 200 perms) ON the chaffed
parts, so we can separate signal from the coincidence floor after splitting. Post-hoc:
decision support only, never a verdict flip.
"""
import collections, importlib.util, os, sys, time
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

def _mod(name, path):
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, path))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

agg = _mod('rings_aggregate', 'tools/rings-aggregate.py')
ra = agg.ra

PERMS = 200

def main():
    rows = ra.load()
    deps, wds = collections.defaultdict(list), collections.defaultdict(list)
    for r in rows:
        for kind, asset, amt, cp in ra.flows(r):
            (deps if kind == 'dep' else wds)[asset].append((r['t'], amt, cp))
    assets = sorted(set(deps) & set(wds), key=lambda a: -(len(deps[a]) + len(wds[a])))
    n_wd = sum(map(len, wds.values()))

    rng_c = np.random.default_rng(agg.CHAFF_SEED)
    parts = {a: agg.chaff_parts(wds[a], rng_c) for a in assets}
    n_parts = sum(map(len, parts.values()))

    out = {}
    for wname, span in agg.WINDOWS:
        chaff_u = chaff_oto = 0
        null_u = np.zeros(PERMS); null_oto = np.zeros(PERMS)
        rng = np.random.default_rng(agg.SEED)
        for a in assets:
            addrs, idx, T, A0, O, _ = agg.build_asset(deps[a], wds[a])
            p = parts[a]
            evp = agg.prep_events(T, O, idx, agg.build_asset(deps[a], p)[5], p, span)
            u, _, _, _ = agg.agg_rates(T, O, A0, addrs, idx, evp, span)
            chaff_u += u
            chaff_oto += agg.oto_unique(T, A0, p, span)
            for k in range(PERMS):
                A = A0[rng.permutation(len(A0))]
                nu, _, _, _ = agg.agg_rates(T, O, A, addrs, idx, evp, span)
                null_u[k] += nu
                null_oto[k] += agg.oto_unique(T, A, p, span)
        out[wname] = dict(
            chaff_agg=chaff_u / n_parts, null_agg_mean=null_u.mean() / n_parts,
            null_agg_p95=np.percentile(null_u, 95) / n_parts,
            chaff_oto=chaff_oto / n_parts, null_oto_mean=null_oto.mean() / n_parts,
            null_oto_p95=np.percentile(null_oto, 95) / n_parts)

    print(f'POST-HOC null-on-parts diagnostic ({n_parts} parts, {PERMS} perms, seed {agg.SEED}; NOT the gate)')
    for wname, _ in agg.WINDOWS:
        d = out[wname]
        print(f'\n[{wname}] rate over chaffed parts')
        print(f'  aggregate unique: chaff {100*d["chaff_agg"]:.1f}%  vs null-on-parts {100*d["null_agg_mean"]:.1f}% '
              f'(p95 {100*d["null_agg_p95"]:.1f}%)  -> excess {100*(d["chaff_agg"]-d["null_agg_mean"]):+.1f} pt')
        print(f'  one-to-one unique: chaff {100*d["chaff_oto"]:.1f}%  vs null-on-parts {100*d["null_oto_mean"]:.1f}% '
              f'(p95 {100*d["null_oto_p95"]:.1f}%)  -> excess {100*(d["chaff_oto"]-d["null_oto_mean"]):+.1f} pt')
    print('\nReference (gate report): real unsplit excess over null at 7d: aggregate +0.4 pt, one-to-one +4.4 pt.')

if __name__ == '__main__':
    main()
