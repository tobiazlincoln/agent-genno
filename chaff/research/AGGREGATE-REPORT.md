# AGGREGATE-MATCH GATE (K1) — generated 2026-11-22 02:58

Pre-registered in chaff-session.json (section gate) BEFORE computation; thresholds not adjusted.
Tool: `tools/rings-aggregate.py` (reads tx.jsonl only, no network).

## Data
- 8996 successful transactions, 3124 deposits, 2183 withdrawals (2026-10-27 to 2026-11-21 17:11 UTC).
- Chaff simulation: each withdrawal split into 3-5 random non-round parts (total preserved exactly), gaps Uniform(1h, 72h) between parts, seed 7; 8757 parts replace 2183 withdrawals.

## Declared interpretations (fixed before computing)
- tolerance RELATIVE to sumB: |sumA - sumB| <= tol * sumB (absolute tol is meaningless across assets).
- window anchored at each withdrawal event: [t_wd - span, t_wd].
- cross-address candidates: depositors A != B; same-address (A == B) reported separately.
- rates pooled across assets; denominators: real = withdrawals, chaff = parts.
- one-to-one = LEAK-REPORT semantics: deposit amount in [w, w*(1+tol)], earlier, same asset, unique = exactly one.
- gate chaff draw = seed 7, single draw; 20-draw mean (seeds 7..26) shown as context, NOT gate.

## Results (tolerance 1%, pooled across assets)
| metric | window | real | null mean (p95) | chaff (seed 7) | chaff mean 20 draws |
|---|---|---|---|---|---|
| aggregate unique-match (cross) | 24h | 17.3% | 15.2% (17.9%) | 5.5% | 5.5% |
| aggregate any-match (cross) | 24h | 32.2% | 28.9% (31.8%) | — | — |
| aggregate same-address | 24h | 14.8% | — | — | — |
| one-to-one unique (LEAK-REPORT) | 24h | 25.9% | 17.4% (21.1%) | 3.3% | 3.3% |
| aggregate unique-match (cross) | 7d | 18.7% | 18.3% (21.3%) | 16.3% | 16.1% |
| aggregate any-match (cross) | 7d | 46.7% | 48.6% (50.9%) | — | — |
| aggregate same-address | 7d | 17.6% | — | — | — |
| one-to-one unique (LEAK-REPORT) | 7d | 29.6% | 25.2% (29.2%) | 10.6% | 10.8% |

## Separation and pairs
- real cross-address unique aggregate matches: 409 of 2183 withdrawals (7d); distinct (depositor A, recipient B) pairs among them: 580.
- real same-address aggregate hits (deposit total ≈ withdrawal total of the SAME address in window): 385 (7d) / 322 (24h) of 2183.

## Limitations
- No ground truth: a match is a statistical inference; real pass-through pairs are never observed directly.
- Coverage of vault-touching signatures is 99.9% (BEHAVIOUR.md); the missing <1% is random RPC loss, assumed independent of behaviour.
- The pool is ~3 weeks old and tester-heavy (BEHAVIOUR.md: many round trips are testers cycling funds); behaviour may not match future users.
- Windows anchored at every event overlap heavily at 7d, so matched events are not independent; the null model captures chance but not this dependence.
- Chaff simulation is a client-side scheduling model only: it shapes withdrawals, not deposits, and cannot address protocol-level leaks (zkSec #01, Certora L-05).
- Chaff draw is a single random draw (seed 7); the 20-draw mean is reported as context. Variance across draws is small but nonzero.

## Reading (interpretation only; no threshold touched)
- At 7d, real aggregate unique-match (18.7%) sits barely above the null mean (18.3%): in this tester-heavy pool with round-amount clustering, aggregate matching itself carries almost no signal beyond chance.
- Consequently Chaff splitting cannot reach a 50% cut of the aggregate rate: most surviving matches are coincidental (the null floor), not true pass-through pairs that splitting would hide. Splitting DOES break the true-pair signal (one-to-one 29.6% -> 10.5%), but not enough to clear the pre-registered 80% bar, and the aggregate coincidence floor remains.

## Gate evaluation (PRE-REGISTERED pass rule, 7d / 1%)
- (1) unique aggregate-match: real 18.7% -> chaff 16.3% = 13.0% reduction; rule requires >= 50% -> FAIL
- (2) unique one-to-one: real 29.6% -> chaff 10.6% = 64.4% reduction; rule requires >= 80% -> FAIL

## Verdict

**FAIL** — K1 gate failed: the pre-registered thresholds were not met at 7d/1%. Per chaff-session.json on_fail: stop; task_2 is NOT started.
