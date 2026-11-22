/** Diagnose WALLET_SYNC: confirm deposit signature + sync with full error chain. */
import { readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { createKeyPairSignerFromPrivateKeyBytes } from "@solana/kit";
import { LocalKeys, SOL_MINT, ShieldedKeypair, SigningKey, Wallet, createZolanaClient, syncWallet, type Bytes32 } from "@heliuslabs/zolana";
import { SignedTeePolicy } from "@heliuslabs/zolana/client";

const DEP_SIG = process.argv[2];

function dumpErr(e: unknown, depth = 0): void {
  const anyE = e as any;
  console.log("  ".repeat(depth) + `- ${anyE?.constructor?.name}: ${anyE?.message}`);
  if (anyE?.code) console.log("  ".repeat(depth) + `  code: ${anyE.code}`);
  if (anyE?.details) console.log("  ".repeat(depth) + `  details: ${JSON.stringify(anyE.details)}`);
  if (anyE?.status) console.log("  ".repeat(depth) + `  status: ${anyE.status}`);
  if (anyE?.cause) dumpErr(anyE.cause, depth + 1);
  if (depth === 0 && anyE?.stack) console.log(anyE.stack.split("\n").slice(1, 4).join("\n"));
}

function loadDotEnv(file: string): Record<string, string> {
  const out: Record<string, string> = {};
  for (const line of readFileSync(file, "utf8").split("\n")) {
    const t = line.trim();
    if (!t || t.startsWith("#")) continue;
    const i = t.indexOf("=");
    if (i <= 0) continue;
    out[t.slice(0, i).trim()] = t.slice(i + 1).trim();
  }
  return out;
}

function toSeed(raw: string): Bytes32 {
  const s = raw.trim();
  const bytes = /^[0-9a-fA-F]+$/.test(s) && s.length % 2 === 0
    ? new Uint8Array(Buffer.from(s, "hex"))
    : new Uint8Array((() => { const u = new Uint8Array(64); let acc = 0n; const A = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz";
        for (const c of s) { const v = A.indexOf(c); if (v < 0) throw new Error("not base58"); acc = acc * 58n + BigInt(v); }
        let hex = acc.toString(16).padStart(128, "0"); return Buffer.from(hex, "hex"); })());
  return (bytes.length === 64 ? bytes.slice(0, 32) : bytes) as Bytes32;
}

async function main(): Promise<void> {
  const env = loadDotEnv(join(import.meta.dirname ?? ".", ".env"));
  const KEY = (env.HELIUS_API_KEY ?? "").trim();
  const owner = await createKeyPairSignerFromPrivateKeyBytes(toSeed(env.CHAFF_OWNER_KEY));
  console.log("endpoints resolved via helius /v1/spr");
  const loggingFetch: typeof fetch = async (input, init) => {
    const url = typeof input === "string" ? input : (input as any).url ?? String((input as any) instanceof Request ? (input as any).url : input);
    const res = await fetch(input as any, init);
    if (String(url).includes("/v1/spr")) {
      const clone = res.clone();
      const body = await clone.text();
      console.log(`>>> indexer ${String(url).replace(/api-key=[^&]+/, "api-key=***")} -> HTTP ${res.status}`);
      writeFileSync(new URL("./last-indexer-response.json", import.meta.url), `${String(url).split("/").pop()?.split("?")[0]}\n${body}`);
      console.log(`>>> body saved (${body.length} bytes)`);
    }
    return res;
  };
  const client = await createZolanaClient({
    solanaRpcUrl: `https://mainnet.helius-rpc.com/?api-key=${KEY}`,
    solanaRpcSubscriptionsUrl: `wss://mainnet.helius-rpc.com/?api-key=${KEY}`,
    proverTee: SignedTeePolicy.forNetwork("mainnet"),
    fetch: async (input, init) => {
      const url = typeof input === "string" ? input : input instanceof URL ? input.href : (input as Request).url ?? String(input);
      const res = await loggingFetch(input as any, init);
      if (!/getShieldedTransactionsBy|getEncryptedUtxosBy/.test(String(url))) return res;
      const body = await res.text();
      try {
        const j = JSON.parse(body);
        if (j?.result?.data && !j.result.transactions && !j.result.matches) {
          const { data, paginationToken, ...rest } = j.result;
          const flat = /getEncryptedUtxosBy/.test(String(url))
            ? { ...rest, matches: data.flatMap((d: any) => d.outputs ?? []) }
            : { ...rest, transactions: data.flatMap((d: any) => d.events ?? []) };
          j.result = flat;
          return new Response(JSON.stringify(j), { status: res.status, statusText: res.statusText, headers: res.headers });
        }
      } catch { /* keep */ }
      return new Response(body, { status: res.status, statusText: res.statusText, headers: res.headers });
    },
  });
  const kp = ShieldedKeypair.fromKeypair(SigningKey.fromEd25519Bytes(toSeed(env.CHAFF_OWNER_KEY)));
  const wallet = new Wallet({ identity: kp.shieldedAddress() });
  const keys = LocalKeys.fromKeypair(kp, client.proofService);

  if (DEP_SIG) {
    console.log("confirmTransaction…");
    const slot = await client.confirmTransaction(DEP_SIG as any);
    console.log("confirmed at slot", slot);
    console.log("syncWallet with requireSlot…");
    try {
      await syncWallet({ client, wallet, keys, config: { requireSlot: slot } });
      console.log("SYNC OK, balance:", wallet.balance(SOL_MINT)?.amount);
    } catch (e) { console.log("sync error:"); dumpErr(e); }
  } else {
    console.log("syncWallet (plain)…");
    try {
      await syncWallet({ client, wallet, keys });
      console.log("SYNC OK, balance:", wallet.balance(SOL_MINT)?.amount);
    } catch (e) { console.log("sync error:"); dumpErr(e); }
  }
}
main().catch((e) => { console.log("fatal:"); dumpErr(e); process.exit(1); });