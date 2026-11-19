// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {ERC721} from "@openzeppelin/contracts/token/ERC721/ERC721.sol";

interface IAgentIdRegistry {
    function balanceOf(address owner) external view returns (uint256);
    function handleOf(address owner) external view returns (string memory);
}

/// @title Agent Achievement Badge
/// @notice Soulbound achievement badges for Agent ID (.ai) holders.
/// Free to claim (gas only), one badge per wallet per quest. Third parties
/// can attest to any badge. No owner, no admin, no fees. The Agent ID
/// registry reference is immutable.
contract AgentBadge is ERC721 {
    /// @dev SPACE ID Agent ID registry on BSC mainnet (immutable, passed at deploy).
    IAgentIdRegistry public immutable agentIdRegistry;

    uint256 private _nextTokenId;

    mapping(uint256 questId => uint256) public questClaimCount;
    mapping(uint256 questId => mapping(address claimer => bool)) public hasClaimed;
    mapping(uint256 badgeId => mapping(address attester => bool)) public hasAttested;
    mapping(uint256 badgeId => uint256) public attestationCount;

    uint256 public totalBadges;
    uint256 public uniqueAgents; // wallets holding >= 1 badge

    mapping(address => bool) private _hasAnyBadge;

    event BadgeClaimed(address indexed agent, uint256 indexed questId, uint256 indexed badgeId, string handle);
    event AttestationAdded(address indexed attester, uint256 indexed badgeId, string note);

    error NotAgentIdHolder();
    error AlreadyClaimed();
    error Soulbound();
    error AlreadyAttested();
    error BadgeDoesNotExist();

    constructor(address registry) ERC721("Agent Achievement Badge", "AAB") {
        agentIdRegistry = IAgentIdRegistry(registry);
    }

    /// @notice Claim a free soulbound badge for a quest. Requires holding an
    /// Agent ID (.ai). One badge per wallet per quest.
    function claimBadge(uint256 questId) external {
        if (agentIdRegistry.balanceOf(msg.sender) == 0) revert NotAgentIdHolder();
        if (hasClaimed[questId][msg.sender]) revert AlreadyClaimed();

        hasClaimed[questId][msg.sender] = true;
        questClaimCount[questId] += 1;

        uint256 badgeId = ++_nextTokenId;
        totalBadges += 1;
        if (!_hasAnyBadge[msg.sender]) {
            _hasAnyBadge[msg.sender] = true;
            uniqueAgents += 1;
        }

        _mint(msg.sender, badgeId);
        emit BadgeClaimed(msg.sender, questId, badgeId, agentIdRegistry.handleOf(msg.sender));
    }

    /// @notice Third-party attestation on a badge. One attestation per
    /// attester per badge. Anyone can attest, including other agents.
    function attest(uint256 badgeId, string calldata note) external {
        if (_ownerOf(badgeId) == address(0)) revert BadgeDoesNotExist();
        if (hasAttested[badgeId][msg.sender]) revert AlreadyAttested();

        hasAttested[badgeId][msg.sender] = true;
        attestationCount[badgeId] += 1;
        emit AttestationAdded(msg.sender, badgeId, note);
    }

    /// @dev Soulbound: all transfers rejected. Minting/burning happen through
    /// internal hooks that are allowed to bypass this check.
    function _update(address to, uint256 tokenId, address auth) internal override returns (address) {
        address from = _ownerOf(tokenId);
        if (from != address(0) && to != address(0)) revert Soulbound();
        return super._update(to, tokenId, auth);
    }

    /// @notice The .ai handle of a badge owner (empty string if unresolvable).
    function handleOfBadgeOwner(uint256 badgeId) external view returns (string memory) {
        return agentIdRegistry.handleOf(_ownerOf(badgeId));
    }
}
