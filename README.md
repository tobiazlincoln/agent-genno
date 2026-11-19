# Agent Genno

Soulbound achievement badges for Agent ID (.ai) holders on BNB Smart Chain.

Free to claim (gas only), one badge per wallet per quest. Third parties and
other agents can attest to badges, building a portable on-chain track record.
The badge binds achievements to the holder's Agent ID identity — names are
displayed via the registry's `handleOf()`, not raw addresses.

## Design principles

- **No owner, no admin keys, no fees** — the Agent ID registry reference is
  immutable, set once at deploy.
- **Zero token approvals** — claiming only mints a soulbound badge.
- **Not an investment** — badges are credentials. No yield, no returns, no
  token, no trading.
- **User-confirmed actions** — everything goes through the user's own agent
  + wallet: preview -> user confirms -> execute. The agent never holds keys.

## Repo layout

```
contracts/        Foundry project
  src/AgentBadge.sol       the badge contract
  test/                    unit + fork tests (fork test hits mainnet registry)
  script/Deploy.s.sol      deploy script
skill.md          agent-facing instructions (baw flow)
llms.txt          machine-readable summary
site/             static landing page + read-only leaderboard
HUMAN-GATES.md    deployment & submission runbook
```

## Development

```bash
curl -L https://foundry.paradigm.xyz | bash && foundryup
forge install OpenZeppelin/openzeppelin-contracts --no-commit
forge test                                   # unit tests
forge test --match-contract Fork \
  --fork-url https://bsc-dataseed.binance.org  # fork test vs real registry
```

## Contract

- Chain: BNB Smart Chain mainnet (chainId 56)
- Agent ID registry: `0x60B9262456dE011F7d15a54CdD8c48bAaa8B022F`
  (SPACE ID Agent ID, ERC-721 soulbound)
- Badge contract: `0xD6ED0279E381612e32F1Fa9DD7f5329bC1c6b811` (verified on BscScan + Sourcify)

Core functions:

```solidity
claimBadge(uint256 questId)   // free mint, gated by registry balanceOf > 0
attest(uint256 badgeId, string note)  // one per attester per badge

// views
uniqueAgents() / totalBadges() / questClaimCount(uint256)
attestationCount(uint256) / handleOfBadgeOwner(uint256)
```

## Quests

- `questId=1` — Hackathon Participation (open)

## Monitoring

```bash
scripts/hackathon-metrics.sh <contract address>
```

## License

MIT
