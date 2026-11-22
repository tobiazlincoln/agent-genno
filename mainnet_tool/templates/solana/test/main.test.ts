import { test } from "node:test";
import assert from "node:assert";
import { Connection, PublicKey } from "@solana/web3.js";

// backtest minimal: RPC hidup & endpoint publik terbaca (evidence, bukan klaim)
test("rpc alive", async () => {
  const c = new Connection(process.env.RPC_URL ?? "https://api.mainnet-beta.solana.com", "confirmed");
  const slot = await c.getSlot();
  assert.ok(slot > 0, "slot harus > 0");
});
