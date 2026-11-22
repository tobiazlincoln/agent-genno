#!/usr/bin/env python3
"""Leak experiment on Privacy Rings: how often can a public withdrawal be matched to a public deposit?

  rings-analyze.py [--perms 200] [--seed 7]

Reads BRAIN/research/rings/tx.jsonl (from rings-collect.py), writes LEAK-REPORT.md.

Pre-registered before looking at results:
  primary cell   : window 1h,  withdrawal within 1% below the deposit
  secondary cell : window 24h, same tolerance
A withdrawal is "uniquely matched" when exactly ONE earlier deposit of the same asset falls in
the window with amount in [w, w*(1+tol)]. Every cell is compared with a null model that shuffles
deposit amounts among deposits of the same asset (times kept), to measure matches expected by chance.

What a match means in the default ring: addresses are already public, so a match does not unmask
anyone. It reveals the AMOUNT that moved privately between the depositor and the withdrawer.
"""
import bisect, collections, json, os, sys, time
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
OUT = os.path.join(ROOT, 'BRAIN', 'research', 'rings')
SOL_VAULT = 'CiNmas621VuyofiDSrEPfTXHKrdZuB6jMKECyNiMpLXE'
TOKEN_AUTHORITY = 'CaM8DbtJ2mSecgaHYo9xeT7VSKq7AnaqEUm5p7e5LW4a'
RENT_DUST = 2_000_000          # lamports: ignore rent-sized SOL moves when finding counterparties
WINDOWS = [('5m', 300), ('30m', 1800), ('1h', 3600), ('6h', 21600), ('24h', 86400), ('7d', 604800), ('all', 10**10)]
TOLS = [0.0, 0.001, 0.005, 0.01, 0.02, 0.05]
PRIMARY, SECONDARY = ('1h', 0.01), ('24h', 0.01)
NAMES = {'SOL': 'SOL', 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v': 'USDC',
         'Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB': 'USDT'}
arg = lambda name, default: type(default)(sys.argv[sys.argv.index(name) + 1]) if name in sys.argv else default
PERMS, SEED = arg('--perms', 200), arg('--seed', 7)


def flows(r):
    """Public pool flows in one transaction: (kind, asset, amount, counterparty)."""
    signers = r['keys'][:r['nsig']]
    out = []
    sol = {r['keys'][i]: d for i, d in r['sol']}
    v = sol.get(SOL_VAULT, 0)
    if abs(v) > RENT_DUST:
        others = {k: d for k, d in sol.items() if k != SOL_VAULT}
        if v > 0:   # deposit: whoever lost the most SOL funded it
            cp = min(others, key=others.get) if others else signers[0]
        else:       # withdrawal: whoever gained the most SOL received it
            cp = max(others, key=others.get) if others else signers[0]
        out.append(('dep' if v > 0 else 'wd', 'SOL', abs(v) / 1e9, cp))
    by_mint = collections.defaultdict(lambda: [0, {}])
    for _, mint, owner, d, dec in r['tok']:
        d = int(d) / 10 ** dec
        if owner == TOKEN_AUTHORITY:
            by_mint[mint][0] += d
        else:
            by_mint[mint][1][owner] = by_mint[mint][1].get(owner, 0) + d
    for mint, (v, others) in by_mint.items():
        if v == 0:
            continue
        cp = (min(others, key=others.get) if v > 0 else max(others, key=others.get)) if others else signers[0]
        out.append(('dep' if v > 0 else 'wd', mint, abs(v), cp))
    return out


def load():
    seen, rows = set(), []
    for line in open(os.path.join(OUT, 'tx.jsonl')):
        try:
            r = json.loads(line)
        except ValueError:
            continue
        if r['sig'] in seen or r['err'] or not r.get('t'):
            continue
        seen.add(r['sig'])
        rows.append(r)
    rows.sort(key=lambda r: (r['slot'], r['sig']))
    return rows


def match_counts(dep_t, dep_a, wd_t, wd_a):
    """counts[w, window, tol] = number of earlier deposits matching withdrawal w."""
    counts = np.zeros((len(wd_t), len(WINDOWS), len(TOLS)), dtype=np.int32)
    tols = np.array(TOLS)
    for i, (t, a) in enumerate(zip(wd_t, wd_a)):
        hi = bisect.bisect_right(dep_t, t)
        for wi, (_, span) in enumerate(WINDOWS):
            lo = bisect.bisect_left(dep_t, t - span)
            if hi <= lo:
                continue
            amt = dep_a[lo:hi]
            # float noise guard: 1e-9 relative
            ok = (amt[:, None] >= a * (1 - 1e-9)) & (amt[:, None] <= a * (1 + tols[None, :]) * (1 + 1e-9))
            counts[i, wi, :] = ok.sum(axis=0)
    return counts


def unique_partner(dep_t, dep_a, dep_cp, t, a, span, tol):
    hi, lo = bisect.bisect_right(dep_t, t), bisect.bisect_left(dep_t, t - span)
    idx = [j for j in range(lo, hi) if a * (1 - 1e-9) <= dep_a[j] <= a * (1 + tol) * (1 + 1e-9)]
    return idx[0] if len(idx) == 1 else None


def pct(x):
    return f'{100 * x:.1f}%'


def main():
    rows = load()
    if not rows:
        sys.exit('no transactions collected yet')
    rng = np.random.default_rng(SEED)
    deps, wds, kinds = collections.defaultdict(list), collections.defaultdict(list), collections.Counter()
    payers, flow_tx = collections.Counter(), 0
    for r in rows:
        payers[r['keys'][0]] += 1
        fl = flows(r)
        kinds['private/other' if not fl else '+'.join(sorted({f[0] for f in fl}))] += 1
        flow_tx += bool(fl)
        for kind, asset, amt, cp in fl:
            (deps if kind == 'dep' else wds)[asset].append((r['t'], amt, cp, r['sig']))
    t0, t1 = rows[0]['t'], rows[-1]['t']
    sig_total = sum(1 for _ in open(os.path.join(OUT, 'sigs.jsonl'))) if os.path.exists(os.path.join(OUT, 'sigs.jsonl')) else 0
    prio = json.load(open(os.path.join(OUT, 'priority.json'))) if os.path.exists(os.path.join(OUT, 'priority.json')) else None
    have = {r['sig'] for r in rows}
    cover = sum(1 for s in prio['sigs'] if s in have) / max(len(prio['sigs']), 1) if prio else None

    n_dep, n_wd = sum(map(len, deps.values())), sum(map(len, wds.values()))
    L = [f'# PRIVACY RINGS LEAK EXPERIMENT — generated {time.strftime("%Y-%m-%d %H:%M")}', '',
         '## Data',
         f'- {len(rows)} successful transactions analysed of {sig_total} program signatures '
         f'({time.strftime("%Y-%m-%d", time.gmtime(t0))} to {time.strftime("%Y-%m-%d %H:%M", time.gmtime(t1))} UTC).',
         f'- Deposit/withdraw coverage: ' + (f'{pct(cover)} of {len(prio["sigs"])} vault-touching signatures '
                                              f'({prio["vaults"]} vault accounts).' if prio else 'UNKNOWN (no priority set).'),
         f'- Flows found: {n_dep} deposits, {n_wd} withdrawals. Transaction kinds: {dict(kinds)}.',
         f'- Distinct depositors {len({c for v in deps.values() for _, _, c, _ in v})}, '
         f'distinct withdrawal recipients {len({c for v in wds.values() for _, _, c, _ in v})}.',
         f'- Fee-payer concentration: top 1 pays {pct(payers.most_common(1)[0][1] / len(rows))}, '
         f'top 5 pay {pct(sum(c for _, c in payers.most_common(5)) / len(rows))} of analysed transactions '
         f'({len(payers)} distinct fee payers).', '']

    L += ['## Assets', '| asset | deposits | withdrawals | deposit volume | withdraw volume | round-amount deposits |', '|---|---|---|---|---|---|']
    for asset in sorted(set(deps) | set(wds), key=lambda a: -(len(deps[a]) + len(wds[a])))[:12]:
        d, w = deps[asset], wds[asset]
        rnd = sum(1 for _, a, _, _ in d if abs(a * 100 - round(a * 100)) < 1e-6) / max(len(d), 1)
        L.append(f'| {NAMES.get(asset, asset[:8])} | {len(d)} | {len(w)} | {sum(a for _, a, _, _ in d):,.2f} | '
                 f'{sum(a for _, a, _, _ in w):,.2f} | {pct(rnd)} |')
    L.append('')

    # ---- matching, real vs null ----
    real = np.zeros((len(WINDOWS), len(TOLS), 2))          # [unique, any]
    null = np.zeros((PERMS, len(WINDOWS), len(TOLS)))
    per_wd = []                                              # (asset, t, amt, recipient, sig, counts[window, tol])
    evals = 0
    for asset, w in wds.items():
        d = sorted(deps.get(asset, []))
        w = sorted(w)
        dep_t = [x[0] for x in d]
        dep_a = np.array([x[1] for x in d])
        wd_t, wd_a = [x[0] for x in w], [x[1] for x in w]
        c = match_counts(dep_t, dep_a, wd_t, wd_a) if d else np.zeros((len(w), len(WINDOWS), len(TOLS)), dtype=np.int32)
        real[:, :, 0] += (c == 1).sum(axis=0)
        real[:, :, 1] += (c >= 1).sum(axis=0)
        evals += c.size
        per_wd += [(asset, *w[i][:4], c[i]) for i in range(len(w))]
        if len(d) > 1:
            for p in range(PERMS):
                cp = match_counts(dep_t, rng.permutation(dep_a), wd_t, wd_a)
                null[p] += (cp == 1).sum(axis=0)
                evals += cp.size
    null_mean, null_p95 = null.mean(axis=0) / max(n_wd, 1), np.percentile(null, 95, axis=0) / max(n_wd, 1)
    uniq = real[:, :, 0] / max(n_wd, 1)

    def table(title, value):
        t = [title, '| window \\ tolerance | ' + ' | '.join(f'{100 * x:g}%' for x in TOLS) + ' |', '|---|' + '---|' * len(TOLS)]
        t += [f'| {name} | ' + ' | '.join(value(wi, ti) for ti in range(len(TOLS))) + ' |' for wi, (name, _) in enumerate(WINDOWS)]
        return t + ['']

    L += [f'## Matching results ({n_wd} withdrawals, {PERMS} shuffles, {evals:,} match evaluations, seed {SEED})', '']
    L += table('Share of withdrawals with exactly ONE matching earlier deposit (real data)', lambda wi, ti: pct(uniq[wi, ti]))
    L += table('Same, expected by chance (mean over shuffles; 95th percentile in brackets)',
               lambda wi, ti: f'{pct(null_mean[wi, ti])} ({pct(null_p95[wi, ti])})')
    L += table('Excess over chance (real minus shuffled mean)', lambda wi, ti: f'{100 * (uniq[wi, ti] - null_mean[wi, ti]):+.1f} pt')
    L += table('Share of withdrawals with at least one matching deposit', lambda wi, ti: pct(real[wi, ti, 1] / max(n_wd, 1)))

    # ---- pre-registered cells, split by same-address vs cross-address ----
    L += ['## Pre-registered cells']
    win = dict(WINDOWS)
    for label, (wname, tol) in (('PRIMARY', PRIMARY), ('SECONDARY', SECONDARY)):
        wi, ti = [n for n, _ in WINDOWS].index(wname), TOLS.index(tol)
        same = cross = 0
        wallets_all, wallets_hit = set(), set()
        for asset, t, a, rcp, sig, c in per_wd:
            wallets_all.add(rcp)
            if c[wi, ti] != 1:
                continue
            d = sorted(deps[asset])
            j = unique_partner([x[0] for x in d], [x[1] for x in d], None, t, a, win[wname], tol)
            if j is None:
                continue
            wallets_hit.add(rcp)
            if d[j][2] == rcp:
                same += 1
            else:
                cross += 1
        p_emp = (np.sum(null[:, wi, ti] >= real[wi, ti, 0]) + 1) / (PERMS + 1)
        L += [f'- {label} ({wname}, {100 * tol:g}%): {int(real[wi, ti, 0])} of {n_wd} withdrawals uniquely matched = {pct(uniq[wi, ti])}; '
              f'chance {pct(null_mean[wi, ti])}; shuffles reaching the real count: p = {p_emp:.4f}.',
              f'    - of these, {same} return to the SAME address that deposited (nothing new revealed), '
              f'{cross} go to a DIFFERENT address (the privately moved amount is revealed).',
              f'    - wallets: {len(wallets_hit)} of {len(wallets_all)} withdrawal recipients have at least one uniquely matched withdrawal '
              f'({pct(len(wallets_hit) / max(len(wallets_all), 1))}).']
    L.append('')

    # ---- concentration of withdrawals ----
    rc = collections.Counter(x[3] for x in per_wd)
    top = rc.most_common(5)
    L += ['## Who withdraws', f'- {len(rc)} recipients; top 5 receive {pct(sum(c for _, c in top) / max(n_wd, 1))} of withdrawals: '
          + ', '.join(f'{k[:6]}… ({c})' for k, c in top) + '.',
          f'- Recipients with exactly one withdrawal: {sum(1 for c in rc.values() if c == 1)}.', '']

    # ---- same result without the heaviest recipients ----
    heavy = {k for k, c in rc.items() if c >= 20}
    light = [x for x in per_wd if x[3] not in heavy]
    wi, ti = [n for n, _ in WINDOWS].index(PRIMARY[0]), TOLS.index(PRIMARY[1])
    wi2 = [n for n, _ in WINDOWS].index(SECONDARY[0])
    if light:
        L += ['## Excluding heavy recipients (20+ withdrawals each, likely bots or services)',
              f'- {len(heavy)} heavy recipients removed, {len(light)} withdrawals remain.',
              f'- uniquely matched: primary {pct(sum(1 for x in light if x[5][wi, ti] == 1) / len(light))}, '
              f'secondary {pct(sum(1 for x in light if x[5][wi2, ti] == 1) / len(light))} (no null model for this subset).', '']

    L += ['## Limits of this experiment',
          '- A match is a statistical inference, not proof. There is no ground truth for who funded which withdrawal.',
          '- Only pass-through behaviour is detectable (withdraw about what was deposited). Partial withdrawals, merged deposits '
          'and funds that stay in the pool are invisible to this method, so the true leak can be higher or lower.',
          '- Counterparties are inferred from public balance changes (largest loser funds a deposit, largest gainer receives a withdrawal).',
          '- The pool is weeks old; activity includes testers, integrators and bots, which may not behave like future users.',
          '- Leak rate measures exposure, not demand: it does not show that users care or would pay to fix it.']
    path = os.path.join(OUT, 'LEAK-REPORT.md')
    open(path, 'w').write('\n'.join(L) + '\n')
    print('\n'.join(L[:14]))
    print(f'... full report -> {os.path.relpath(path, ROOT)}')


if __name__ == '__main__':
    main()
