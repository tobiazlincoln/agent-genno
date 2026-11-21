# DESIGN INVESTIGATION: privacy autopilot on Solana Privacy Rings — 22 Nov 2026

Investigation before design. Sources: helius-labs/privacy-rings repo (code + commits),
@heliuslabs/zolana TS SDK README, empirical analysis of ~4.4k collected mainnet transactions
(partial dataset, 795 deposits + 619 withdrawals), Helius docs, audit reports.

## 1. Feasibility: every primitive the product needs already exists client-side

- TS SDK is now `@heliuslabs/zolana` (rename from `@heliuslabs/spr`; branch ts-sdk-v0.8.0-alpha).
  Full README cached at `research/deep/zolana-ts-sdk-README.md`.
- `buildDepositTransaction` — deposit to your own OR someone else's shielded address.
- `buildTransferTransaction` — multi-recipient in one transaction.
- `buildWithdrawalTransaction` — withdraw to a public address, any amount.
- Merge support — consolidate fragmented UTXOs (merge circuit needs no per-merge signature; delegable).
- Prover choice: remote TEE prover (policy pinned per network, client verifies signed policy)
  or local proving (`proofDataSource` modes). No SDK URL is hardcoded.
- Conclusion: no protocol change, no custom circuit, no custom ring needed for v1.
  The product is orchestration logic on top of the SDK.

## 2. Cost model (empirical, partial dataset)

- Median tx fee: 87,532 lamports (~0.00009 SOL); p75 same; max 422,876. Rent for nullifier
  PDAs ~706,120 lamports per account, refunded later by foresters.
- Splitting one withdrawal into 5 parts costs roughly 5 x 0.00009 SOL + refundable rent
  (order of $0.01 total at current SOL). Timing/amount shaping is CHEAP.
- Each proof request is one prover call (free tier RPS limits apply if remote prover).

## 3. The leak is real and measurable (partial data, not the final verdict)

- 151 same-address round trips observed: median deposit->withdraw gap 3.4 MINUTES,
  113 of 151 under 1 hour. Timing correlation is trivial for any observer.
- Amounts are heavily clustered: 0.01 SOL x232, 0.02 x110, 0.03, 0.1... Common amounts
  make "match by amount" noisy — the null model in the leak experiment exists for this.
- Users' current behaviour (tiny round amounts, minutes-scale round trips) is exactly the
  fingerprint an autopilot would remove.

## 4. Helius' own answer to the deposit leak is routing, not timing

- Official docs: "We recommend using on-ramp over deposit for better privacy."
  They acknowledge deposit visibility; their mitigation is the fiat onramp
  (or waiting for Custom Rings). Nobody — Helius included — ships timing/amount hygiene.
- Rings.run only WARNS users ("simple math on public deposits can undo privacy");
  no automated defence exists.

## 5. What an autopilot CAN and CANNOT fix (honesty list)

CAN (client-side, no protocol change):
- amount shaping: split deposits/withdrawals into non-round, variable-size parts
- timing shaping: randomized delays, background execution across hours
- routing choice: prefer fiat onramp, avoid withdraw-to-same-address patterns,
  warn on withdrawal to a freshly-funded or clustered recipient
- UTXO hygiene: merge fragmentation at quiet hours

CANNOT (protocol-level, acknowledged in audits / by design):
- zkSecurity #01 private_tx_hash leak and Certora L-05 public cache selection
  (links an output to its spend): protocol behaviour; code in that area changed
  after the audits, but the fixes are NOT independently verified by us.
- View tags: the sender's pubkey indexes encrypted outputs (sync speed trade-off).
- Deposit from public funds is inherently visible — onramp is the only full fix.
- Registry records announce who can receive private transfers.
- Exchange-side clustering of withdrawal recipients (off-chain analysis).

## 6. The core design constraint (discovered here)

Delayed withdrawals require the owner's signature at execution time (Solana blockhashes
expire ~60s; durable nonces do not give multi-hour scheduling). So an autopilot that
fires withdrawals at randomized times must either:
  a) run as a local process/phone holding the user key under an explicit spending
     policy (kill switch, caps, payee list) — the pattern Doei already uses for agent
     payments, applied to privacy hygiene; or
  b) use a custom ring delegate rail (protocol-level trust change, enterprise path), or
  c) the unaudited timelock-escrow example program (explicitly not for production).
Option (a) is the only v1 that ships without new trust assumptions. The UX price:
the product is a local daemon/app, not a pure web page.

## 7. Open items

- Final leak report (collector at ~50%+; finisher will write LEAK-REPORT.md automatically).
- zkSec #00/#01 fix verification against current code (needed before any marketing claim).
- Whether withdrawal recipients are exchange deposit addresses (would prove real-world
  demand beyond testers) — not yet measured.

## Decision

Proceed to design only after the final leak numbers arrive. If cross-address unique-match
rate is high above chance: build the autopilot (option 6a). If not: the idea dies here
and the fallback candidates from VERDICTS.md get re-examined.
