// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Test} from "forge-std/Test.sol";
import {Vm} from "forge-std/Vm.sol";
import {AgentBadge} from "../src/AgentBadge.sol";

contract MockRegistry {
    Vm constant vm = Vm(address(uint160(uint256(keccak256("hevm cheat code")))));
    mapping(address => uint256) private _balance;

    function setBalance(address a, uint256 n) external {
        _balance[a] = n;
    }

    function balanceOf(address owner) external view returns (uint256) {
        return _balance[owner];
    }

    function handleOf(address owner) external pure returns (string memory) {
        return string.concat("agent-", vm.toString(uint256(uint160(owner))), ".ai");
    }
}

contract AgentBadgeTest is Test {
    MockRegistry registry;
    AgentBadge badge;
    address holder = makeAddr("holder");
    address outsider = makeAddr("outsider");
    address other = makeAddr("other");

    event BadgeClaimed(address indexed agent, uint256 indexed questId, uint256 indexed badgeId, string handle);
    event AttestationAdded(address indexed attester, uint256 indexed badgeId, string note);

    function setUp() public {
        registry = new MockRegistry();
        badge = new AgentBadge(address(registry));
        registry.setBalance(holder, 1);
    }

    function test_gate_nonHolderReverts() public {
        vm.prank(outsider);
        vm.expectRevert(AgentBadge.NotAgentIdHolder.selector);
        badge.claimBadge(1);
    }

    function test_claim_succeedsForHolder() public {
        vm.prank(holder);
        badge.claimBadge(1);
        assertEq(badge.balanceOf(holder), 1);
        assertEq(badge.ownerOf(1), holder);
    }

    function test_claim_onePerWalletPerQuest() public {
        vm.startPrank(holder);
        badge.claimBadge(1);
        vm.expectRevert(AgentBadge.AlreadyClaimed.selector);
        badge.claimBadge(1);
        // different quest is fine
        badge.claimBadge(2);
        assertEq(badge.balanceOf(holder), 2);
        vm.stopPrank();
    }

    function test_claim_counters() public {
        registry.setBalance(other, 1);
        vm.prank(holder);
        badge.claimBadge(1);
        vm.prank(other);
        badge.claimBadge(1);
        assertEq(badge.questClaimCount(1), 2);
        assertEq(badge.totalBadges(), 2);
        assertEq(badge.uniqueAgents(), 2);
        // same wallet, new quest: uniqueAgents unchanged
        vm.prank(holder);
        badge.claimBadge(2);
        assertEq(badge.uniqueAgents(), 2);
        assertEq(badge.totalBadges(), 3);
    }

    function test_soulbound_transferReverts() public {
        vm.prank(holder);
        badge.claimBadge(1);
        vm.prank(holder);
        vm.expectRevert(AgentBadge.Soulbound.selector);
        badge.transferFrom(holder, other, 1);
        vm.prank(holder);
        vm.expectRevert(AgentBadge.Soulbound.selector);
        badge.safeTransferFrom(holder, other, 1);
    }

    function test_soulbound_approveAndTransferFromReverts() public {
        vm.prank(holder);
        badge.claimBadge(1);
        vm.prank(holder);
        badge.approve(other, 1);
        vm.prank(other);
        vm.expectRevert(AgentBadge.Soulbound.selector);
        badge.transferFrom(holder, other, 1);
    }

    function test_claim_emitsEventWithHandle() public {
        string memory h = registry.handleOf(holder);
        vm.prank(holder);
        vm.expectEmit(true, true, true, true);
        emit BadgeClaimed(holder, 1, 1, h);
        badge.claimBadge(1);
    }

    function test_attest_oncePerAttester() public {
        vm.prank(holder);
        badge.claimBadge(1);
        vm.prank(outsider);
        badge.attest(1, "great work");
        assertEq(badge.attestationCount(1), 1);
        vm.prank(outsider);
        vm.expectRevert(AgentBadge.AlreadyAttested.selector);
        badge.attest(1, "again");
        // different attester still fine
        vm.prank(other);
        badge.attest(1, "agreed");
        assertEq(badge.attestationCount(1), 2);
    }

    function test_attest_nonexistentBadgeReverts() public {
        vm.expectRevert(AgentBadge.BadgeDoesNotExist.selector);
        badge.attest(999, "nope");
    }

    function test_attest_emitsEvent() public {
        vm.prank(holder);
        badge.claimBadge(1);
        vm.prank(outsider);
        vm.expectEmit(true, true, false, true);
        emit AttestationAdded(outsider, 1, "solid");
        badge.attest(1, "solid");
    }

    function test_handleOfBadgeOwner() public {
        vm.prank(holder);
        badge.claimBadge(1);
        assertEq(badge.handleOfBadgeOwner(1), registry.handleOf(holder));
    }

    function test_registryReferenceImmutable() public {
        assertEq(address(badge.agentIdRegistry()), address(registry));
    }
}
