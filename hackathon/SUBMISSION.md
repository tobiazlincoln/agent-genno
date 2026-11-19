# Submission copy — Binance Agent ID Hackathon
Form: https://app.binance.com/uni-qr/user-survey/fb26d2bd25e04329b1ba77c7b3811d23

## Project name
Agent Genno

## Website
https://tobiazlincoln.github.io/agent-genno/

## Contract address(es) — BSC mainnet, verified on BscScan
0xD6ED0279E381612e32F1Fa9DD7f5329bC1c6b811

## Source code
https://github.com/tobiazlincoln/agent-genno (public, MIT)

## Agent-facing docs
https://tobiazlincoln.github.io/agent-genno/skill.md
https://tobiazlincoln.github.io/agent-genno/llms.txt

## Description of Agent ID usage (for the form — written to the 30% depth rubric)

Agent Genno issues soulbound achievement badges bound to Agent ID (.ai)
identity. Agent ID is the subject of the product, not a gate:

- Gating: claimBadge(questId) calls balanceOf(caller) on the official
  SPACE ID Agent ID registry (0x60B9...022F) — only .ai holders can claim.
- Identity display: the contract resolves handleOf(owner) so badges carry
  the holder's .ai name on-chain (events emit the handle), not raw hex.
- Portability: a public attest() function lets any third party or other
  agent vouch for a badge — .ai reputation becomes queryable by other
  dApps (access, trust, credit decisions).
- Agent-native UX: no wallet connect on the site; the holder's own AI
  agent reads skill.md, runs baw preflight, previews the call, and the
  user confirms in their own Binance wallet. No sessions, no keys, no
  QR login — fully within the hackathon safety rules.

## Compliance notes (mirror for judges)
No owner/admin functions; immutable registry reference; zero token
approvals; no promised returns; soulbound = no secondary market; all
claims previewed + confirmed by the user in their own wallet.
