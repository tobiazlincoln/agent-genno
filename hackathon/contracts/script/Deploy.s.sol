// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Script, console2} from "forge-std/Script.sol";
import {AgentBadge} from "../src/AgentBadge.sol";

/// Deploy script.
///
/// Usage (BSC testnet, chain 97):
///   export PRIVATE_KEY=0x...            # funded testnet deployer
///   export REGISTRY=0x...               # real registry (56) or mock on 97
///   forge script script/Deploy.s.sol --rpc-url https://data-seed-prebsc-1-s1.binance.org:8545 --broadcast
///
/// Mainnet (56) — HUMAN GATE, requires BNB gas + BSCSCAN_API_KEY for verify:
///   forge script script/Deploy.s.sol --rpc-url https://bsc-dataseed.binance.org --broadcast --verify
contract Deploy is Script {
    // SPACE ID Agent ID registry on BSC mainnet (per hackathon RESEARCH.md, verified on-chain)
    address constant MAINNET_REGISTRY = 0x60B9262456dE011F7d15a54CdD8c48bAaa8B022F;

    function run() external returns (AgentBadge b) {
        // accept key with or without 0x prefix
        string memory raw = vm.envString("PRIVATE_KEY");
        string memory hexKey = bytes(raw)[0] == "0" ? raw : string.concat("0x", raw);
        uint256 pk = vm.parseUint(hexKey);
        address registry = vm.envOr("REGISTRY", MAINNET_REGISTRY);
        vm.startBroadcast(pk);
        b = new AgentBadge(registry);
        vm.stopBroadcast();
        console2.log("AgentBadge deployed:", address(b));
        console2.log("registry:", registry);
    }
}
