# Skill: Agent Genno badges (claim + attest)

Free soulbound achievement badges for Agent ID (.ai) holders on BSC.
Claim one badge per quest (gas only — no payment, no approvals). Third
parties (and other agents) can attest to badges, building portable
on-chain reputation.

## Contract

- Chain: BNB Smart Chain mainnet, chainId **56**
- Contract: `0xD6ED0279E381612e32F1Fa9DD7f5329bC1c6b811` (filled after mainnet deploy; see ROADMAP p3)
- Registry (immutable reference): `0x60B9262456dE011F7d15a54CdD8c48bAaa8B022F`
  (SPACE ID Agent ID, ERC-721 soulbound)

## Preflight (run these BEFORE any write)

```
baw wallet status          # wallet unlocked, network = BSC (chain 56)
baw wallet settings        # Developer Mode must be ON for tx
baw wallet agent-id        # must show a claimed .ai handle
```

If the user has no Agent ID: stop. They can claim one in the Binance App
(Wallet > homepage banner > Agent ID), then retry.

## Read-only calls (no confirmation needed)

```
baw wallet contract-call --address 0xD6ED0279E381612e32F1Fa9DD7f5329bC1c6b811 --data "totalBadges()"
baw wallet contract-call --address 0xD6ED0279E381612e32F1Fa9DD7f5329bC1c6b811 --data "uniqueAgents()"
baw wallet contract-call --address 0xD6ED0279E381612e32F1Fa9DD7f5329bC1c6b811 --data "questClaimCount(uint256)" --args <questId>
```

Resolve a .ai handle (via registry): `ownerOfHandle(string) -> address`.

## Claim a badge (write — user MUST confirm)

1. Preview first — this is mandatory; the requestId only comes from a
   successful preview:

```
baw wallet contract-call preview --address 0xD6ED0279E381612e32F1Fa9DD7f5329bC1c6b811 \
  --data "claimBadge(uint256)" --args <questId>
```

2. The user sees the preview in their Binance wallet UI and confirms it
   themselves. Never claim the confirmation for them, never suggest they
   skip it.
3. Execute with the requestId from step 1:

```
baw wallet contract-call execute --request-id <REQUEST_ID>
```

Error `351803` from preview = risk-blocked by Binance. Do not retry; report
to the user.

## Attest to someone's badge (write — user MUST confirm)

```
baw wallet contract-call preview --address 0xD6ED0279E381612e32F1Fa9DD7f5329bC1c6b811 \
  --data "attest(uint256,string)" --args <badgeId> "<short note>"
baw wallet contract-call execute --request-id <REQUEST_ID>
```

One attestation per attester per badge.

## Quests

Quest IDs are published on the project landing page (see ROADMAP p2-site).
Current quest: `questId=1` ("Hackathon Participation").

## Hard rules

- The agent NEVER holds keys, seed phrases, or pairing codes.
- Every write goes through preview -> user confirms -> execute.
- No approvals are involved: claimBadge only mints; no token allowances.
- The contract has no owner, no fees, no admin functions.
