# NOVELTY LEDGER — generated 2026-11-22 00:38
A hit means prior work exists. Zero hits means "not found in GitHub/npm/CoinGecko", not "nobody is building it".

| id | idea | GitHub hits (all queries) | Privacy Rings builders matching |
|---|---|---|---|
| leak-meter | Privacy leak meter: measure how linkable Privacy Rings deposits/withdrawals really are, per wallet | 1 | 0 |
| hygiene | Privacy autopilot: schedule deposits/withdrawals (split, delay, round amounts) so they cannot be matched | 0 | 0 |
| proof-of-funds | ZK proof of funds from a shielded balance (prove balance >= X without revealing it) | 1 | 0 |
| view-ledger | Accounting / tax export and selective disclosure reports from a viewing key | 0 | 0 |
| inheritance | Private inheritance / dead-man's switch on a shielded balance | 0 | 0 |
| sealed-bid | Sealed-bid auctions / sealed token sales with private bid amounts | 0 | 0 |
| payroll | Private payroll / vesting / contributor payouts | 2 | 0 |
| agent-pay | Private payments for AI agents (x402) | 1 | 3 |

## leak-meter — Privacy leak meter: measure how linkable Privacy Rings deposits/withdrawals really are, per wallet
Deposits and withdrawals are public. Score each wallet's linkability from amount/timing and tell the user what leaked.

- GitHub repos `privacy rings linkability solana`: 0 hits
- GitHub repos `zolana anonymity set`: 0 hits
- GitHub repos `shielded pool deanonymization solana`: 0 hits
- GitHub repos `solana privacy score wallet linkability`: 1 hits
    - himanshu-rawat77/Solana-Privacy-Audit-tool ★0 pushed 2026-02-07 — A full-stack dashboard that analyzes a Solana wallet's "Privacy Score" by tracing its funding lineage and identifying li
- GitHub repos `tornado cash anonymity set analysis heuristics`: 0 hits
- npm `privacy score solana`: 50916 hits
    - @solana/web3.js — Solana Javascript API
    - @solana/errors — Throw, identify, and decode Solana JavaScript errors
    - @solana/rpc-parsed-types — Type definitions for parsed types used in the Solana RPC
    - @solana/codecs-core — Core types and helpers for encoding and decoding byte arrays on Solana
    - @solana/assertions — Helpers for asserting that a JavaScript environment supports certain features necessary for the oper
- Privacy Rings builders matching ['linkab', 'anonymity', 'leak', 'privacy score', 'heuristic', 'deanonym', 'analy']: none

## hygiene — Privacy autopilot: schedule deposits/withdrawals (split, delay, round amounts) so they cannot be matched
Client-side scheduler that removes the amount/timing fingerprint the leak meter detects.

- GitHub repos `privacy rings scheduler split delay withdraw`: 0 hits
- GitHub repos `shielded withdrawal timing obfuscation solana`: 0 hits
- GitHub repos `zolana decoy amount rounding`: 0 hits
- Privacy Rings builders matching ['schedul', 'delay', 'split', 'decoy', 'hygiene', 'autopilot', 'mixer']: none

## proof-of-funds — ZK proof of funds from a shielded balance (prove balance >= X without revealing it)
Attestation over your own UTXOs for OTC, lending, allowlists.

- GitHub repos `proof of funds zolana`: 0 hits
- GitHub repos `zero knowledge proof of funds solana shielded`: 0 hits
- GitHub repos `private proof of solvency solana`: 1 hits
    - ss1738/rwa-credit-proof ★0 pushed 2026-11-11 — Zero-knowledge proof-of-solvency for tokenized private credit. A fund proves it is solvent and fully KYC'd without revea
- GitHub repos `proof of balance privacy rings`: 0 hits
- npm `zk proof of funds solana`: 1333756 hits
    - @solana/zk-sdk — Universal WASM package for the rust solana-zk-sdk
    - @solana/errors — Throw, identify, and decode Solana JavaScript errors
    - @solana/rpc-parsed-types — Type definitions for parsed types used in the Solana RPC
    - @solana/codecs-numbers — Codecs for numbers of different sizes and endianness
    - @solana/rpc-subscriptions — A library for subscribing to Solana RPC notifications
- CoinGecko `proof of funds`: no coins
- Privacy Rings builders matching ['proof of funds', 'proof-of-funds', 'solvency', 'proof of balance', 'attest']: none

## view-ledger — Accounting / tax export and selective disclosure reports from a viewing key
Explorers and tax tools cannot read private balances; a viewing-key ledger makes them reportable.

- GitHub repos `viewing key tax export solana`: 0 hits
- GitHub repos `zolana viewing key accounting`: 0 hits
- GitHub repos `privacy rings transaction history export csv`: 0 hits
- GitHub repos `shielded balance tax report solana`: 0 hits
- npm `viewing key accounting solana`: 315098 hits
    - @solana/errors — Throw, identify, and decode Solana JavaScript errors
    - @solana/keys — Helpers for generating and transforming key material
    - @solana/signers — An abstraction layer over signing messages and transactions in Solana
    - @solana/transactions — Helpers for creating and serializing transactions
    - @solana/web3.js — Solana Javascript API
- Privacy Rings builders matching ['tax', 'accounting', 'ledger', 'export', 'report', 'explorer', 'history', 'disclos']: none

## inheritance — Private inheritance / dead-man's switch on a shielded balance
Timelock escrow releases a private balance to heirs after inactivity.

- GitHub repos `dead man switch solana shielded`: 0 hits
- GitHub repos `private inheritance zolana`: 0 hits
- GitHub repos `crypto inheritance solana timelock escrow privacy`: 0 hits
- CoinGecko `inheritance`: no coins
- Privacy Rings builders matching ['inherit', 'dead man', 'deadman', 'will', 'heir', 'recovery']: none

## sealed-bid — Sealed-bid auctions / sealed token sales with private bid amounts
Bids locked in private escrow, revealed only at close.

- GitHub repos `sealed bid auction zolana`: 0 hits
- GitHub repos `sealed-bid auction solana privacy rings`: 0 hits
- GitHub repos `private auction solana shielded escrow`: 0 hits
- CoinGecko `sealed bid`: no coins
- Privacy Rings builders matching ['auction', 'sealed', 'bid', 'launch']: none

## payroll — Private payroll / vesting / contributor payouts
Pay a team without publishing salaries.

- GitHub repos `private payroll solana privacy rings`: 1 hits
    - lopeselio/ringstack ★1 pushed 2026-11-08 — Private payments on Solana, built on Helius Privacy: payment requests, receipts and proofs, a webhook daemon, and privat
- GitHub repos `zolana payroll`: 1 hits
    - evgeniko/confidential-payroll-zolana ★0 pushed 2026-09-07 — 
- GitHub repos `confidential vesting solana shielded`: 0 hits
- Privacy Rings builders matching ['payroll', 'vesting', 'salary', 'payout', 'stream']: none

## agent-pay — Private payments for AI agents (x402)
Known to exist (Doei, musebook) — included as a control that the method detects prior work.

- GitHub repos `x402 privacy rings agent`: 0 hits
- GitHub repos `confidential agent payments solana x402`: 1 hits
    - devansh0703/veil ★0 pushed 2026-10-13 — Veil — private payment rails for the agent economy. x402 agent payments settled confidentially on Solana via Token-2022 
- GitHub repos `zolana x402`: 0 hits
- npm `x402 privacy rings`: 26212 hits
    - @dicebear/rings — Avatar style for DiceBear
    - @x402/extensions — x402 Payment Protocol Extensions
    - @x402/evm — x402 Payment Protocol EVM Implementation
    - x402 — x402 Payment Protocol
    - @x402/svm — x402 Payment Protocol SVM Implementation
- Privacy Rings builders matching ['agent', 'x402', 'mcp']: solana-foundation/solana-mcp (), solanabr/skills (Solana ecosystem agent skill directory.), D4NZ-jpg/hermes-wispr-stt (Hermes Agent STT plugin backed by Wispr Flow (via wispr-clie)

