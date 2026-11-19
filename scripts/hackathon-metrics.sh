#!/usr/bin/env bash
# Monitor hackathon metrics: unique Agent ID interactors vs Innovation bar (30).
# Usage: scripts/hackathon-metrics.sh [CONTRACT_ADDRESS]
# Reads on-chain counters directly from the deployed AgentBadge contract.

set -e
RPC="${RPC:-https://bsc-dataseed.binance.org}"
export PATH="$HOME/.foundry/bin:$PATH"
CONTRACT="${1:-}"
REGISTRY="0x60B9262456dE011F7d15a54CdD8c48bAaa8B022F"

if [ -z "$CONTRACT" ]; then
  echo "usage: $0 <AgentBadge contract address on BSC mainnet>" >&2
  echo "contract not deployed yet (human gate p3-mainnet)" >&2
  exit 2
fi

UNIQUE=$(cast call "$CONTRACT" 'uniqueAgents()(uint256)' --rpc-url "$RPC")
TOTAL=$(cast call "$CONTRACT" 'totalBadges()(uint256)' --rpc-url "$RPC")
Q1=$(cast call "$CONTRACT" 'questClaimCount(uint256)(uint256)' 1 --rpc-url "$RPC")

echo "=== Agent Achievement Badge metrics ($(date -u +%FT%TZ)) ==="
echo "contract:      $CONTRACT"
echo "uniqueAgents:  $UNIQUE   (Innovation eligibility bar: 30)"
echo "totalBadges:   $TOTAL"
echo "quest1 claims: $Q1"
if [ "$UNIQUE" -ge 30 ] 2>/dev/null; then
  echo "STATUS: ELIGIBLE for Innovation Award (>= 30 unique .ai addresses)"
else
  N=$((30 - UNIQUE))
  echo "STATUS: need $N more unique .ai addresses for Innovation eligibility"
fi
