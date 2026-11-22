# USER BEHAVIOUR FINGERPRINT — generated 2026-11-22 02:43
Dataset: 8996 successful tx, deposit/withdraw coverage 7658/7666 (99.9%) of deposit/withdraw signatures.
Everything below is read from PUBLIC chain data only. Partial-dataset caveat applies while coverage < 100%; early activity is dominated by testers and integrators.

## Flows
| asset | deposits | withdrawals | dep volume | wd volume |
|---|---|---|---|---|
| SOL | 1854 | 1372 | 8,273.43 | 3,256.96 |
| EPjFWdd5Au | 524 | 367 | 214,814.15 | 91,606.43 |
| Es9vMFrzaC | 44 | 40 | 86,403.84 | 58,843.00 |
| 12XbVdAszA | 46 | 21 | 334,269,184.84 | 334,269,184.84 |
| 65iH8k736Q | 24 | 20 | 2,488,577.57 | 2,424,439.65 |
| GdZ9rwHyKc | 3 | 39 | 30,882,360.00 | 30,882,360.00 |
| 7wKGTD1r2j | 24 | 14 | 125,316.03 | 125,316.03 |
| ZfkySvDU6d | 12 | 24 | 1,200.00 | 1,200.00 |
| DezXAZ8z7P | 23 | 12 | 172,852,419.02 | 991,704.95 |
| AD3ksG2WY3 | 16 | 10 | 421,804.39 | 421,804.39 |
- distinct depositors: 1560; distinct withdrawal recipients: 1319
- tx fee lamports: p10=5000 / p25=5000 / p50=87532 / p75=87532 / p90=325000

## Amount clustering (why matching is ambiguous)
Exact-amount collisions among deposits: how many OTHER deposits share the same exact amount.
A withdrawal of amount x can be uniquely matched only if few deposits share x.
- SOL: 1854 deposits, 986 distinct amounts, 852 unique (86.4% of distinct amounts seen exactly once). Top amounts: 0.01 x109, 0.1 x49, 0.02 x48, 0.03 x40, 0.020495 x36, 0.0022 x33.
- EPjFWdd5Au: 524 deposits, 221 distinct amounts, 192 unique (86.9% of distinct amounts seen exactly once). Top amounts: 0.01 x133, 1 x58, 10 x15, 2 x14, 100 x10, 50 x10.
- 12XbVdAszA: 46 deposits, 46 distinct amounts, 46 unique (100.0% of distinct amounts seen exactly once). Top amounts: 2.89386e+06 x1, 29230.9 x1, 1.71293e+07 x1, 173023 x1, 1.69708e+07 x1, 171422 x1.
- Es9vMFrzaC: 44 deposits, 41 distinct amounts, 39 unique (95.1% of distinct amounts seen exactly once). Top amounts: 1 x3, 20 x2, 1.0971 x1, 1e-06 x1, 1.69208 x1, 0.32188 x1.

## Same-address round trips (deposit -> withdraw to the SAME address, one-to-one matching, 168h horizon)
- 395 of 2183 withdrawals (18.1%) return to an address that deposited a matching amount within the horizon (one-to-one, deposit consumed once).
- gap seconds: p10=16 / p25=92 / p50=553 / p75=19246 / p90=97179
- under 1h: 250 (63.3%); under 5 min: 168 (42.5%).
- 269 distinct addresses do this.

This is the trivial, unambiguous leak: no statistical inference needed, the addresses match.
Note: many of these are testers cycling funds, so treat the share as an upper bound on "real" behaviour.

## Cross-address matches (withdraw to a DIFFERENT address, unique amount match within window)
- window 1h, tolerance 1%: 278 withdrawals (12.7%) uniquely match one earlier deposit FROM ANOTHER ADDRESS.
- window 24h, tolerance 1%: 363 withdrawals (16.6%) uniquely match one earlier deposit FROM ANOTHER ADDRESS.

These are the interesting cases: the amount that moved privately between two addresses is revealed.
Compare against the null model in LEAK-REPORT.md before reading them as leaks.
