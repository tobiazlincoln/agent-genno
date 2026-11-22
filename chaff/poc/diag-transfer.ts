/** Diagnose WALLET_BUILD_TRANSFER: sync owner, build transfer, dump full error chain + prover HTTP. */
import { readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { createKeyPairSignerFromPrivateKeyBytes } from "@solana/kit";
import { LocalKeys, SOL_MINT, ShieldedKeypair, SigningKey, Wallet, buildTransferTransaction, createZolanaClient, syncWallet, type Bytes32 } from "@heliuslabs/zolana";
import { teePolicyFromJson } from "@heliuslabs/zolana/client";
import { ed25519 } from "@noble/curves/ed25519.js";

function dumpErr(e: unknown, depth = 0): void {
  const anyE = e as any;
  console.log("  ".repeat(depth) + `- ${anyE?.constructor?.name}: ${anyE?.message}`);
  if (anyE?.code) console.log("  ".repeat(depth) + `  code: ${anyE.code}`);
  if (anyE?.details) console.log("  ".repeat(depth) + `  details: ${JSON.stringify(anyE.details)}`);
  if (anyE?.cause) dumpErr(anyE.cause, depth + 1);
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
  if (/^[0-9a-fA-F]+$/.test(s) && s.length % 2 === 0) {
    const b = new Uint8Array(Buffer.from(s, "hex"));
    return (b.length === 64 ? b.slice(0, 32) : b) as Bytes32;
  }
  const A = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz";
  let acc = 0n;
  for (const c of s) acc = acc * 58n + BigInt(A.indexOf(c));
  const b = new Uint8Array(Buffer.from(acc.toString(16).padStart(128, "0"), "hex"));
  return (b.length === 64 ? b.slice(0, 32) : b) as Bytes32;
}

async function main(): Promise<void> {
  const env = loadDotEnv(join(import.meta.dirname ?? ".", ".env"));
  const KEY = (env.HELIUS_API_KEY ?? "").trim();
  const owner = await createKeyPairSignerFromPrivateKeyBytes(toSeed(env.CHAFF_OWNER_KEY));
  const recipient = await createKeyPairSignerFromPrivateKeyBytes(toSeed(env.CHAFF_RECIPIENT_KEY));
  const logFetch: typeof fetch = async (input, init) => {    const url = typeof input === "string" ? input : input instanceof URL ? input.href : (input as Request).url ?? String(input);
    let res = await fetch(input as any, init);
    if (/getShieldedTransactionsByTags|getShieldedTransactionsByNullifiers|getEncryptedUtxosByTags/.test(String(url))) {
      const body = await res.text();
      let out = body;
      try {
        const j = JSON.parse(body);
        if (j?.result?.data && !j.result.transactions && !j.result.matches) {
          const { data, paginationToken, ...rest } = j.result;
          j.result = /getEncryptedUtxosBy/.test(String(url))
            ? { ...rest, matches: data.flatMap((d: any) => d.outputs ?? []) }
            : { ...rest, transactions: data.flatMap((d: any) => d.events ?? []) };
          out = JSON.stringify(j);
        }
      } catch { /* keep */ }
      res = new Response(out, { status: res.status, statusText: res.statusText, headers: res.headers });
    }
    if (String(url).includes("/v1/spr") && !/getShielded|getEncrypted|getMerkle|getNonInclusion|getUserRecords/.test(String(url))) {
      const body = await res.clone().text();
      console.log(`>>> ${String(url).replace(/api-key=[^&]+/, "api-key=***")} -> HTTP ${res.status}`);
      console.log(`>>> ${body.slice(0, 700)}`);
      writeFileSync(new URL("./last-prover-response.json", import.meta.url), body);
    }
    return res;
  };
  const tee = await (async () => {
    let res: Response | undefined;
    for (const delay of [0, 2000, 6000]) {
      if (delay) await new Promise((r) => setTimeout(r, delay));
      try { res = await fetch("https://d3gbdb0egjwcw9.cloudfront.net/tee-policy/mainnet.json"); break; } catch { /* retry */ }
    }
    if (!res?.ok) throw new Error("tee policy fetch gagal");
    const file: any = await res.json();
    const payload = JSON.parse(Buffer.from(file.release?.payload ?? file.payload, "hex").toString("utf8"));
    const EMBEDDED = [
      { pcr0: "de01051f48dec20d40d3666a99dbe14917b2e350f500981d77c85d5fc6a0a21917e8f695d6a4465d68a21e7eef942121", pcr1: "4b4d5b3661b3efc12920900c80e126e4ce783c522de6c02a2a5bf7af3a2b9327b86776f188e4be1c1c404a129dbda493", pcr2: "d2d4d066c3226e4cf89fdd143362dc63611978bb81a244db011c74623d3d9a37c5b8f275ca6363fe71c0df3245e50d4b" },
      { pcr0: "5d5b9e4c051c99c21c2553419850c36ea2c1889cc406fe5d92f264a2a89b3b65f9cc57df82c47db8d143db74df0cff98", pcr1: "4b4d5b3661b3efc12920900c80e126e4ce783c522de6c02a2a5bf7af3a2b9327b86776f188e4be1c1c404a129dbda493", pcr2: "a40538edc43176376d9619a4fffdc264c0ab1e22052ede82f9d20b475a07bbdcc14f0e0e08308e56224696609f3c0f7d" },
    ];
    if (payload.network !== "mainnet" || payload.policy?.platform !== "aws-nitro" || payload.expires_at < Math.floor(Date.now() / 1000)) throw new Error("tee policy tidak sesuai");
    if (JSON.stringify(payload.policy.measurements) !== JSON.stringify(EMBEDDED)) throw new Error("measurements berubah dari embedded");
    return teePolicyFromJson({ ...payload.policy, gpu: "optional", max_age_secs: 600 });
  })();
  const client = await createZolanaClient({
    solanaRpcUrl: `https://mainnet.helius-rpc.com/?api-key=${KEY}`,
    solanaRpcSubscriptionsUrl: `wss://mainnet.helius-rpc.com/?api-key=${KEY}`,
    proverTee: tee,
    fetch: logFetch,
  });
  const kp = ShieldedKeypair.fromKeypair(SigningKey.fromEd25519Bytes(toSeed(env.CHAFF_OWNER_KEY)));
  const wallet = new Wallet({ identity: kp.shieldedAddress() });
  const keys = LocalKeys.fromKeypair(kp, client.proofService);
  await syncWallet({ client, wallet, keys });
  console.log("owner private balance:", wallet.balance(SOL_MINT)?.amount);

  console.log("buildTransferTransaction…");
  try {
    const tx = await buildTransferTransaction({
      client, wallet, keys,
      feePayer: owner.address,
      recipient: recipient.address,
      amount: 10_000_000n,
    });
    console.log("BUILD OK", tx !== undefined);
  } catch (e) {
    console.log("build error:");
    dumpErr(e);
  }
}
main().catch((e) => { console.log("fatal:"); dumpErr(e); process.exit(1); });
