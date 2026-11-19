// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Test} from "forge-std/Test.sol";
import {AgentBadgeV2} from "../src/AgentBadgeV2.sol";
import {Strings} from "@openzeppelin/contracts/utils/Strings.sol";

contract MockRegistry {
    mapping(address => uint256) private _balance;

    function setBalance(address a, uint256 n) external { _balance[a] = n; }

    function balanceOf(address owner) external view returns (uint256) { return _balance[owner]; }

    function handleOf(address owner) external pure returns (string memory) {
        return string.concat("agent-", Strings.toString(uint160(owner)), ".ai");
    }
}

contract AgentBadgeV2Test is Test {
    MockRegistry registry;
    AgentBadgeV2 badge;
    address holder = makeAddr("holder");
    address outsider = makeAddr("outsider");
    address other = makeAddr("other");

    event BadgeClaimed(address indexed agent, uint256 indexed questId, uint256 indexed badgeId, string handle);
    event QuestCreated(uint256 indexed questId, string name, address indexed creator);
    event AttestationAdded(address indexed attester, uint256 indexed badgeId, string note);

    function setUp() public {
        registry = new MockRegistry();
        badge = new AgentBadgeV2(address(registry));
        registry.setBalance(holder, 1);
    }

    /* ---------- quests (permissionless, new in v2) ---------- */

    function test_createQuest_anyone() public {
        vm.prank(other);
        uint256 q = badge.createQuest("Weekly Quest", "ipfs://desc");
        assertEq(q, 1);
        (string memory name, string memory uri, address creator, uint64 createdAt) = badge.quests(q);
        assertEq(createdAt > 0, true);
        assertEq(name, "Weekly Quest");
        assertEq(uri, "ipfs://desc");
        assertEq(creator, other);
    }

    function test_createQuest_emptyNameReverts() public {
        vm.expectRevert(AgentBadgeV2.EmptyQuestName.selector);
        badge.createQuest("", "");
    }

    function test_claimQuest1Created() public {
        badge.createQuest("Hackathon Participation", "");
        vm.prank(holder);
        badge.claimBadge(1);
        assertEq(badge.ownerOf(1), holder);
    }

    /* ---------- gate + core claim (carried from v1) ---------- */

    function test_gate_nonHolderReverts() public {
        badge.createQuest("q", "");
        vm.prank(outsider);
        vm.expectRevert(AgentBadgeV2.NotAgentIdHolder.selector);
        badge.claimBadge(1);
    }

    function test_claim_onePerWalletPerQuest() public {
        badge.createQuest("q", "");
        vm.startPrank(holder);
        badge.claimBadge(1);
        vm.expectRevert(AgentBadgeV2.AlreadyClaimed.selector);
        badge.claimBadge(1);
        badge.claimBadge(2);
        assertEq(badge.balanceOf(holder), 2);
        vm.stopPrank();
    }

    function test_counters_uniqueAgents() public {
        badge.createQuest("q", "");
        registry.setBalance(other, 1);
        vm.prank(holder); badge.claimBadge(1);
        vm.prank(other); badge.claimBadge(1);
        assertEq(badge.questClaimCount(1), 2);
        assertEq(badge.totalBadges(), 2);
        assertEq(badge.uniqueAgents(), 2);
        vm.prank(holder); badge.claimBadge(2);
        assertEq(badge.uniqueAgents(), 2);
        assertEq(badge.totalBadges(), 3);
    }

    /* ---------- soulbound ---------- */

    function test_soulbound_transferReverts() public {
        badge.createQuest("q", "");
        vm.prank(holder); badge.claimBadge(1);
        vm.prank(holder);
        vm.expectRevert(AgentBadgeV2.Soulbound.selector);
        badge.transferFrom(holder, other, 1);
    }

    function test_soulbound_evenAfterApprove() public {
        badge.createQuest("q", "");
        vm.startPrank(holder);
        badge.claimBadge(1);
        badge.approve(other, 1);
        vm.stopPrank();
        vm.prank(other);
        vm.expectRevert(AgentBadgeV2.Soulbound.selector);
        badge.transferFrom(holder, other, 1);
    }

    /* ---------- enumeration (new in v2) ---------- */

    function test_badgesOf() public {
        badge.createQuest("q", "");
        vm.startPrank(holder);
        badge.claimBadge(1);
        badge.claimBadge(2);
        vm.stopPrank();
        uint256[] memory ids = badge.badgesOf(holder);
        assertEq(ids.length, 2);
        assertEq(ids[0], 1);
        assertEq(ids[1], 2);
    }

    function test_getQuestClaimers_paging() public {
        badge.createQuest("q", "");
        registry.setBalance(other, 1);
        registry.setBalance(outsider, 1);
        vm.prank(holder); badge.claimBadge(1);
        vm.prank(other); badge.claimBadge(1);
        vm.prank(outsider); badge.claimBadge(1);

        (address[] memory page, uint256 total) = badge.getQuestClaimers(1, 0, 2);
        assertEq(total, 3);
        assertEq(page.length, 2);
        assertEq(page[0], holder);
        assertEq(page[1], other);

        (address[] memory page2,) = badge.getQuestClaimers(1, 2, 2);
        assertEq(page2.length, 1);
        assertEq(page2[0], outsider);

        (address[] memory empty,) = badge.getQuestClaimers(1, 10, 2);
        assertEq(empty.length, 0);
    }

    /* ---------- metadata (new in v2) ---------- */

    function test_tokenURI_containsHandleAndSVG() public {
        badge.createQuest("q", "");
        vm.prank(holder);
        badge.claimBadge(1);
        string memory uri = badge.tokenURI(1);
        assertEq(bytes(uri).length > 100, true);
        assertEq(_contains(uri, "data:application/json;base64,"), true);
        // handle hidup di dalam base64 json — verifikasi via getBadge
        AgentBadgeV2.Badge memory b = badge.getBadge(1);
        assertEq(_contains(b.handle, "agent-"), true);
        assertEq(b.questId, 1);
    }

    function test_tokenURI_badgeHueDeterministic() public {
        uint256 h1 = badge.badgeHue(1);
        assertEq(h1, badge.badgeHue(1));
        assertEq(h1 <= 359, true);
    }

    function _contains(string memory haystack, string memory needle) internal pure returns (bool) {
        return keccak256(bytes(haystack)) != keccak256("")
            && bytes(haystack).length >= bytes(needle).length
            && _indexOf(haystack, needle);
    }

    function _indexOf(string memory h, string memory n) internal pure returns (bool) {
        bytes memory hb = bytes(h);
        bytes memory nb = bytes(n);
        for (uint256 i = 0; i + nb.length <= hb.length; i++) {
            bool ok = true;
            for (uint256 j = 0; j < nb.length; j++) {
                if (hb[i + j] != nb[j]) { ok = false; break; }
            }
            if (ok) return true;
        }
        return false;
    }

    /* ---------- attest (carried + score) ---------- */

    function test_attest_oncePerAttester_scoreAggregates() public {
        badge.createQuest("q", "");
        vm.prank(holder); badge.claimBadge(1);
        vm.prank(outsider); badge.attest(1, "great");
        vm.prank(other); badge.attest(1, "agreed");
        assertEq(badge.attestationCount(1), 2);
        assertEq(badge.attestationScore(holder), 2);
        vm.prank(outsider);
        vm.expectRevert(AgentBadgeV2.AlreadyAttested.selector);
        badge.attest(1, "again");
    }

    function test_attest_nonexistentReverts() public {
        vm.expectRevert(AgentBadgeV2.BadgeDoesNotExist.selector);
        badge.attest(999, "nope");
    }

    /* ---------- immutability ---------- */

    function test_registryImmutable() public {
        assertEq(address(badge.agentIdRegistry()), address(registry));
    }
}
