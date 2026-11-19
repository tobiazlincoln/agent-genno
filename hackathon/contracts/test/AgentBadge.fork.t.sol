// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Test} from "forge-std/Test.sol";
import {AgentBadge} from "../src/AgentBadge.sol";

/// Fork test against BSC mainnet. Verifies the real SPACE ID Agent ID
/// registry gates claims. Requires an RPC with historical state.
contract AgentBadgeForkTest is Test {
    // SPACE ID Agent ID registry, BSC mainnet
    address constant REGISTRY = 0x60B9262456dE011F7d15a54CdD8c48bAaa8B022F;
    // known holder: owner of "heyi" (co-CEO Binance handle, per research)
    address constant KNOWN_HOLDER = 0x72B73415e263C2b976B2770ee764BACD02ec3004;
    address constant NON_HOLDER = 0x00000000000000000000000000000000000DEaD1;

    AgentBadge badge;

    function setUp() public {
        badge = new AgentBadge(REGISTRY);
    }

    function test_realRegistry_gatesClaim() public {
        // Only meaningful against a BSC mainnet fork (run with --fork-url).
        if (block.chainid != 56) return;
        // non-holder reverts on the real registry
        vm.prank(NON_HOLDER);
        vm.expectRevert(AgentBadge.NotAgentIdHolder.selector);
        badge.claimBadge(1);

        // real .ai holder can claim; handle resolves on mainnet state
        vm.prank(KNOWN_HOLDER);
        badge.claimBadge(1);
        assertEq(badge.ownerOf(1), KNOWN_HOLDER);
        assertEq(badge.uniqueAgents(), 1);
    }
}
