// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {ERC721} from "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import {Strings} from "@openzeppelin/contracts/utils/Strings.sol";
import {Base64} from "@openzeppelin/contracts/utils/Base64.sol";

interface IAgentIdRegistry {
    function balanceOf(address owner) external view returns (uint256);
    function handleOf(address owner) external view returns (string memory);
}

/// @title Agent Genno Badge V2
/// @notice Soulbound achievement badges for Agent ID (.ai) holders.
/// Improvements over V1:
///  - On-chain tokenURI: every badge carries a generative SVG + live metadata
///  - Permissionless quest registry: quests are defined on-chain by anyone
///  - Full enumeration: badgesOf(), getQuestClaimers(), totalBadges() — no log scanning
///  - Attestation aggregates per agent
/// Still: no owner, no fees, zero approvals, immutable registry reference,
/// soulbound (all transfers revert).
contract AgentBadgeV2 is ERC721 {
    using Strings for uint256;

    IAgentIdRegistry public immutable agentIdRegistry;

    struct Quest {
        string name;
        string descURI;
        address creator;
        uint64 createdAt;
    }

    struct Badge {
        uint256 questId;
        string handle;
        uint64 claimedAt;
    }

    uint256 private _nextTokenId;

    mapping(uint256 questId => Quest) public quests;
    uint256 public questCount;

    mapping(uint256 questId => mapping(address claimer => bool)) public hasClaimed;
    mapping(uint256 questId => uint256) public questClaimCount;
    mapping(uint256 badgeId => mapping(address attester => bool)) public hasAttested;
    mapping(uint256 badgeId => uint256) public attestationCount;
    mapping(address agent => uint256) public attestationScore;

    uint256 public totalBadges;
    uint256 public uniqueAgents;
    mapping(address => bool) private _hasAnyBadge;
    mapping(address => uint256[]) private _badgesOf;
    mapping(uint256 questId => address[]) private _questClaimers;

    Badge[] private _badges;

    event BadgeClaimed(address indexed agent, uint256 indexed questId, uint256 indexed badgeId, string handle);
    event QuestCreated(uint256 indexed questId, string name, address indexed creator);
    event AttestationAdded(address indexed attester, uint256 indexed badgeId, string note);

    error NotAgentIdHolder();
    error AlreadyClaimed();
    error Soulbound();
    error AlreadyAttested();
    error BadgeDoesNotExist();
    error EmptyQuestName();

    constructor(address registry) ERC721("Agent Genno Badge", "GENNO") {
        agentIdRegistry = IAgentIdRegistry(registry);
    }

    /* ------------------------------ | QUESTS | ------------------------------ */

    /// @notice Anyone can define a quest on-chain. Quests are public goods.
    function createQuest(string calldata name, string calldata descURI) external returns (uint256 questId) {
        if (bytes(name).length == 0) revert EmptyQuestName();
        questId = ++questCount;
        quests[questId] = Quest({name: name, descURI: descURI, creator: msg.sender, createdAt: uint64(block.timestamp)});
        emit QuestCreated(questId, name, msg.sender);
    }

    /* ------------------------------ | CLAIM | ------------------------------ */

    /// @notice Claim a free soulbound badge for a quest. Requires an Agent ID.
    function claimBadge(uint256 questId) external {
        if (agentIdRegistry.balanceOf(msg.sender) == 0) revert NotAgentIdHolder();
        if (hasClaimed[questId][msg.sender]) revert AlreadyClaimed();

        hasClaimed[questId][msg.sender] = true;
        questClaimCount[questId] += 1;

        string memory handle = agentIdRegistry.handleOf(msg.sender);
        uint256 badgeId = ++_nextTokenId;
        totalBadges += 1;
        if (!_hasAnyBadge[msg.sender]) {
            _hasAnyBadge[msg.sender] = true;
            uniqueAgents += 1;
        }

        _badges.push(Badge({questId: questId, handle: handle, claimedAt: uint64(block.timestamp)}));
        _badgesOf[msg.sender].push(badgeId);
        _questClaimers[questId].push(msg.sender);

        _mint(msg.sender, badgeId);
        emit BadgeClaimed(msg.sender, questId, badgeId, handle);
    }

    /* ------------------------------ | ATTEST | ------------------------------ */

    /// @notice Third-party attestation on a badge. One per attester per badge.
    /// The badge owner's agent accumulates an attestation score.
    function attest(uint256 badgeId, string calldata note) external {
        if (_ownerOf(badgeId) == address(0)) revert BadgeDoesNotExist();
        if (hasAttested[badgeId][msg.sender]) revert AlreadyAttested();

        hasAttested[badgeId][msg.sender] = true;
        attestationCount[badgeId] += 1;
        attestationScore[_ownerOf(badgeId)] += 1;
        emit AttestationAdded(msg.sender, badgeId, note);
    }

    /* ------------------------------ | VIEWS | ------------------------------ */

    /// @notice All badge ids owned by an agent.
    function badgesOf(address agent) external view returns (uint256[] memory) {
        return _badgesOf[agent];
    }

    /// @notice Paged claimer addresses for a quest (leaderboard without log scanning).
    function getQuestClaimers(uint256 questId, uint256 offset, uint256 limit)
        external view returns (address[] memory page, uint256 total)
    {
        address[] storage all = _questClaimers[questId];
        total = all.length;
        if (offset >= total) return (new address[](0), total);
        uint256 end = offset + limit;
        if (end > total) end = total;
        page = new address[](end - offset);
        for (uint256 i = offset; i < end; i++) page[i - offset] = all[i];
    }

    /// @notice Full badge record by id.
    function getBadge(uint256 badgeId) external view returns (Badge memory) {
        if (_ownerOf(badgeId) == address(0)) revert BadgeDoesNotExist();
        return _badges[badgeId - 1];
    }

    /// @notice Deterministic generative pattern seed (hue varies per badge).
    function badgeHue(uint256 badgeId) external pure returns (uint256) {
        return (uint256(keccak256(abi.encodePacked("genno", badgeId))) % 360);
    }

    /// @notice On-chain metadata: generative SVG sealed with the holder's handle.
    function tokenURI(uint256 badgeId) public view override returns (string memory) {
        if (_ownerOf(badgeId) == address(0)) revert BadgeDoesNotExist();
        Badge memory b = _badges[badgeId - 1];
        uint256 hue = this.badgeHue(badgeId);
        string memory svg = string.concat(
            '<svg xmlns="http://www.w3.org/2000/svg" width="320" height="320">',
            '<rect width="320" height="320" fill="#0b0f18"/>',
            '<circle cx="160" cy="160" r="120" fill="none" stroke="hsl(', hue.toString(), ',80%,60%)" stroke-width="2" stroke-dasharray="6 8"/>',
            '<rect x="95" y="95" width="130" height="130" rx="26" transform="rotate(45 160 160)" fill="hsl(', hue.toString(), ',85%,58%)"/>',
            '<path d="M133 166 L152 185 L194 136" stroke="#0b0f18" stroke-width="13" stroke-linecap="round" stroke-linejoin="round"/>',
            '<text x="160" y="270" text-anchor="middle" fill="#f5d78e" font-family="monospace" font-size="20">', b.handle, '</text>',
            '</svg>'
        );
        string memory json = string.concat(
            '{"name":"Agent Genno badge #', badgeId.toString(),
            unicode' — ', b.handle,
            '","description":"Soulbound achievement badge bound to Agent ID identity. Quest #',
            b.questId.toString(), '. Attestations: ', attestationCount[badgeId].toString(),
            '. Non-transferable.","image":"data:image/svg+xml;base64,',
            Base64.encode(bytes(svg)),
            '","attributes":[{"trait_type":"quest","value":"#', b.questId.toString(),
            '"},{"trait_type":"attestations","value":"', attestationCount[badgeId].toString(),
            '"},{"trait_type":"handle","value":"', b.handle, '"}]}'
        );
        return string.concat("data:application/json;base64,", Base64.encode(bytes(json)));
    }

    /* ------------------------------ | SOULBOUND | ------------------------------ */

    function _update(address to, uint256 tokenId, address auth) internal override returns (address) {
        address from = _ownerOf(tokenId);
        if (from != address(0) && to != address(0)) revert Soulbound();
        return super._update(to, tokenId, auth);
    }
}
