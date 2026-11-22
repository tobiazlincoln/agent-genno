# NOVELTY VERDICTS — 22 Nov 2026 (round 1)

Method: tools/novelty-check.py (GitHub code+repo search, npm, CoinGecko) plus web search.
"Killed" = a live product or public repo already does it. "Not found" is NOT proof of novelty.

| idea | verdict | evidence |
|---|---|---|
| leak-meter (linkability score) | KILLED | ringexplorer.com ("Linkability score": fee payer, timing, matching amounts); iriscan.app tracing through Rings; xroot.dev article; Rings.run warns users |
| sealed-bid auction | KILLED | otc.rings.run has sealed-bid auctions |
| private payroll | KILLED | lopeselio/ringstack, evgeniko/confidential-payroll-zolana |
| agent payments (control) | KILLED (expected) | doei.io, rings.musebook.trade, devansh0703/veil |
| proof of funds | KILLED in concept | docs.cloak.ag "Compliance and proof of funds" (Cloak pool); zkRune integrating proofs with Helius Rings |
| viewing-key accounting/tax export | KILLED in concept | Cloak exports CSV/PDF compliance reports from a viewing key; not found for Helius Rings specifically |
| private trading (earlier hypothesis) | OCCUPIED | Vanish Trade, GoDark (dark-pool perps), Lumenless (pre-product) |
| privacy autopilot (auto split/delay/round) | NOT FOUND as a tool | Rings.run only warns; no automated scheduler found |
| private inheritance / dead-man's switch | NOT FOUND | zero hits in all sources |

## Market size facts (shieldedsol.com API, 21 Nov)
- All Solana privacy pools combined: $2.30M TVL across 12 protocols.
- Privacy Cash $1.44M, Helius Rings $606K, Umbra $191K, Arcium $53K, rest < $4K each.
- Helius Rings since 27 Oct: 25,642 tx, 5,011 deposits ($1.02M), 2,659 withdrawals ($412K), 14 failed.

## On-chain facts (public RPC, 22 Nov)
- Program upgrade authority: CuZ42BsoBcLaNTUboJpGhekGmrYMZ7sRhwVki4frz1FB, last deploy slot 467127839.
  The authority has no funded account on chain (consistent with a PDA; whether it is a multisig is UNVERIFIED).
- ~1,000 program tx per 13 hours. Transactions are version 1 (RPC needs maxSupportedTransactionVersion: 1).
- In a 14-tx sample: one wallet signed 9 of 14; a 2.040 SOL deposit and a 2.030 SOL withdrawal to a
  different address appeared close together (possible amount link; not proven).
- 12 tracked privacy protocols: Privacy Cash, Umbra, Cloak, Arcium, MagicBlock, Helius Rings, Vanish Trade,
  Turbine, Voidify, Mixoor, Light Protocol, Elusiv (sunset). Others: Houdini, Solflare Private Send, GoDark,
  Hinkal, zkRune, Lumenless, ShadowWire.
