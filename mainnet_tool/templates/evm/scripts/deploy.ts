// {{NAME}} — evm deploy/check entry (evidence first)
const EXPECTED_CHAIN_ID = {{CHAIN_ID}};
const RPC = process.env.RPC_URL ?? "{{RPC_URL}}";
const cmd = process.argv[2] ?? "check";
async function main() {
  if (cmd === "check") {
    const r = await fetch(RPC, {method: "POST", headers: {"Content-Type": "application/json"},
      body: JSON.stringify({jsonrpc: "2.0", id: 1, method: "eth_chainId", params: []})});
    const j = await r.json() as any;
    const id = parseInt(j.result, 16);
    if (id !== EXPECTED_CHAIN_ID) die(`WRONG NETWORK: chain id ${id}, expected ${EXPECTED_CHAIN_ID} — refusing to continue`);
    console.log("chainId", id, "OK @", RPC);
  } else die(`unknown command: ${cmd}`);
}
function die(m: string): never { console.error(m); process.exit(1); }
main();
