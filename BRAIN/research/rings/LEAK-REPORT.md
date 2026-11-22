# PRIVACY RINGS LEAK EXPERIMENT — generated 2026-11-22 02:43

## Data
- 8996 successful transactions analysed of 25698 program signatures (2026-10-27 to 2026-11-21 17:11 UTC).
- Deposit/withdraw coverage: 99.9% of 7666 vault-touching signatures (368 vault accounts).
- Flows found: 3124 deposits, 2183 withdrawals. Transaction kinds: {'private/other': 3837, 'dep': 2982, 'wd': 2069, 'dep+wd': 108}.
- Distinct depositors 1560, distinct withdrawal recipients 1319.
- Fee-payer concentration: top 1 pays 8.5%, top 5 pay 26.0% of analysed transactions (1946 distinct fee payers).

## Assets
| asset | deposits | withdrawals | deposit volume | withdraw volume | round-amount deposits |
|---|---|---|---|---|---|
| SOL | 1854 | 1372 | 8,273.43 | 3,256.96 | 31.7% |
| USDC | 524 | 367 | 214,814.15 | 91,606.43 | 67.7% |
| USDT | 44 | 40 | 86,403.84 | 58,843.00 | 52.3% |
| 12XbVdAs | 46 | 21 | 334,269,184.84 | 334,269,184.84 | 0.0% |
| 65iH8k73 | 24 | 20 | 2,488,577.57 | 2,424,439.65 | 29.2% |
| GdZ9rwHy | 3 | 39 | 30,882,360.00 | 30,882,360.00 | 100.0% |
| 7wKGTD1r | 24 | 14 | 125,316.03 | 125,316.03 | 0.0% |
| ZfkySvDU | 12 | 24 | 1,200.00 | 1,200.00 | 100.0% |
| DezXAZ8z | 23 | 12 | 172,852,419.02 | 991,704.95 | 34.8% |
| AD3ksG2W | 16 | 10 | 421,804.39 | 421,804.39 | 0.0% |
| 9cRCn9rG | 18 | 3 | 39.50 | 39.38 | 100.0% |
| FoAnSCG6 | 19 | 0 | 1,605.62 | 0.00 | 0.0% |

## Matching results (2183 withdrawals, 200 shuffles, 17,740,086 match evaluations, seed 7)

Share of withdrawals with exactly ONE matching earlier deposit (real data)
| window \ tolerance | 0% | 0.1% | 0.5% | 1% | 2% | 5% |
|---|---|---|---|---|---|---|
| 5m | 5.8% | 6.1% | 12.5% | 13.6% | 14.5% | 15.2% |
| 30m | 7.3% | 7.7% | 16.4% | 18.1% | 19.5% | 20.4% |
| 1h | 7.7% | 8.1% | 17.5% | 19.1% | 20.4% | 21.3% |
| 6h | 8.7% | 9.0% | 22.9% | 24.7% | 26.2% | 27.3% |
| 24h | 7.7% | 8.2% | 24.0% | 25.9% | 26.9% | 24.3% |
| 7d | 10.9% | 13.1% | 30.5% | 29.6% | 28.5% | 22.4% |
| all | 10.3% | 12.7% | 28.7% | 29.0% | 25.8% | 20.8% |

Same, expected by chance (mean over shuffles; 95th percentile in brackets)
| window \ tolerance | 0% | 0.1% | 0.5% | 1% | 2% | 5% |
|---|---|---|---|---|---|---|
| 5m | 1.2% (1.7%) | 1.3% (1.7%) | 1.7% (2.2%) | 1.8% (2.3%) | 2.0% (2.5%) | 2.3% (3.0%) |
| 30m | 2.2% (3.0%) | 2.3% (3.0%) | 3.5% (4.4%) | 3.9% (4.8%) | 4.3% (5.4%) | 5.6% (6.6%) |
| 1h | 2.8% (3.7%) | 2.9% (3.7%) | 4.5% (5.6%) | 5.1% (6.2%) | 5.8% (7.1%) | 7.6% (9.3%) |
| 6h | 4.6% (6.8%) | 4.9% (7.0%) | 8.5% (11.0%) | 9.8% (12.3%) | 11.7% (14.4%) | 15.3% (18.1%) |
| 24h | 5.8% (8.3%) | 6.5% (9.3%) | 12.6% (16.3%) | 14.9% (18.7%) | 17.7% (21.1%) | 20.6% (24.0%) |
| 7d | 8.4% (11.7%) | 10.6% (14.0%) | 21.1% (24.8%) | 22.7% (26.2%) | 21.9% (25.4%) | 17.6% (20.8%) |
| all | 8.6% (12.0%) | 11.2% (14.7%) | 21.3% (24.9%) | 22.7% (26.7%) | 20.7% (24.9%) | 15.8% (19.5%) |

Excess over chance (real minus shuffled mean)
| window \ tolerance | 0% | 0.1% | 0.5% | 1% | 2% | 5% |
|---|---|---|---|---|---|---|
| 5m | +4.6 pt | +4.8 pt | +10.8 pt | +11.7 pt | +12.5 pt | +12.8 pt |
| 30m | +5.1 pt | +5.4 pt | +12.9 pt | +14.2 pt | +15.2 pt | +14.8 pt |
| 1h | +5.0 pt | +5.2 pt | +13.1 pt | +14.0 pt | +14.7 pt | +13.6 pt |
| 6h | +4.1 pt | +4.1 pt | +14.4 pt | +14.9 pt | +14.4 pt | +12.0 pt |
| 24h | +1.9 pt | +1.7 pt | +11.5 pt | +11.0 pt | +9.2 pt | +3.6 pt |
| 7d | +2.6 pt | +2.5 pt | +9.4 pt | +7.0 pt | +6.6 pt | +4.8 pt |
| all | +1.7 pt | +1.5 pt | +7.4 pt | +6.3 pt | +5.1 pt | +5.0 pt |

Share of withdrawals with at least one matching deposit
| window \ tolerance | 0% | 0.1% | 0.5% | 1% | 2% | 5% |
|---|---|---|---|---|---|---|
| 5m | 7.3% | 7.6% | 14.2% | 15.3% | 16.3% | 17.1% |
| 30m | 9.8% | 10.2% | 19.9% | 21.9% | 23.4% | 24.8% |
| 1h | 10.4% | 10.9% | 21.7% | 24.0% | 25.6% | 27.3% |
| 6h | 13.3% | 13.8% | 30.4% | 33.7% | 37.2% | 42.7% |
| 24h | 16.4% | 17.2% | 37.4% | 41.6% | 46.4% | 54.2% |
| 7d | 24.8% | 27.3% | 53.3% | 58.6% | 66.8% | 75.6% |
| all | 25.1% | 28.1% | 54.2% | 60.6% | 67.7% | 76.3% |

## Pre-registered cells
- PRIMARY (1h, 1%): 417 of 2183 withdrawals uniquely matched = 19.1%; chance 5.1%; shuffles reaching the real count: p = 0.0050.
    - of these, 184 return to the SAME address that deposited (nothing new revealed), 233 go to a DIFFERENT address (the privately moved amount is revealed).
    - wallets: 350 of 1319 withdrawal recipients have at least one uniquely matched withdrawal (26.5%).
- SECONDARY (24h, 1%): 565 of 2183 withdrawals uniquely matched = 25.9%; chance 14.9%; shuffles reaching the real count: p = 0.0050.
    - of these, 215 return to the SAME address that deposited (nothing new revealed), 350 go to a DIFFERENT address (the privately moved amount is revealed).
    - wallets: 481 of 1319 withdrawal recipients have at least one uniquely matched withdrawal (36.5%).

## Who withdraws
- 1319 recipients; top 5 receive 6.3% of withdrawals: 2kgbLo… (46), FEhuTm… (26), 6chn9n… (23), GhDVCM… (21), FhVo3m… (21).
- Recipients with exactly one withdrawal: 924.

## Excluding heavy recipients (20+ withdrawals each, likely bots or services)
- 5 heavy recipients removed, 2046 withdrawals remain.
- uniquely matched: primary 20.3%, secondary 27.4% (no null model for this subset).

## Limits of this experiment
- A match is a statistical inference, not proof. There is no ground truth for who funded which withdrawal.
- Only pass-through behaviour is detectable (withdraw about what was deposited). Partial withdrawals, merged deposits and funds that stay in the pool are invisible to this method, so the true leak can be higher or lower.
- Counterparties are inferred from public balance changes (largest loser funds a deposit, largest gainer receives a withdrawal).
- The pool is weeks old; activity includes testers, integrators and bots, which may not behave like future users.
- Leak rate measures exposure, not demand: it does not show that users care or would pay to fix it.
