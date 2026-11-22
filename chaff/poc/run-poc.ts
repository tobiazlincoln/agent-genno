/**
 * CHAFF PoC devnet (task_2, chaff-session.json):
 *   register (owner + recipient) -> deposit -> private transfer -> withdraw with fee-cut
 *   (feePayer = recipient, "Sponsored fees" — fee dipotong dari output, TANPA buffer).
 * Setiap langkah menghasilkan signature devnet yang dicetak. Secret di .devnet-key.json
 * (gitignored). Contoh unaudited TIDAK dipakai; hanya SDK @heliuslabs/zolana resmi.
 */
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import {
  AccountRole,
  appendTransactionMessageInstruction,
  createTransactionMessage,
  createKeyPairSignerFromPrivateKeyBytes,
  getBase58Encoder,
  getSignatureFromTransaction,
  pipe,
  sendAndConfirmTransactionFactory,
  setTransactionMessageFeePayerSigner,
  setTransactionMessageLifetimeUsingBlockhash,
  signTransactionMessageWithSigners,
  signTransactionWithSigners,
  type Address,
  type Instruction,
  type KeyPairSigner,
  type Signature,
  type Transaction,
} from "@solana/kit";
import {
  LocalKeys,
  SOL_MINT,
  ShieldedKeypair,
  SigningKey,
  Wallet,
  buildDepositTransaction,
  buildRegistrationTransaction,
  buildTransferTransaction,
  buildWithdrawalTransaction,
  createZolanaClient,
  syncWallet,
  type Bytes32,
} from "@heliuslabs/zolana";
import { SignedTeePolicy, teePolicyFromJson } from "@heliuslabs/zolana/client";


const OWNER_MIN = 85_000_000n;      // 0.085 SOL: topup recipient 0.005, register+rent, deposit 0.05, transfer 0.01, withdraw 0.025, fee/slack
const RECIPIENT_TOPUP = 5_000_000n; // 0.005 SOL: otomatis dikirim owner -> recipient (fee payer withdraw)
const DEPOSIT = 50_000_000n;        // 0.05 SOL
const TRANSFER = 10_000_000n;       // 0.01 SOL
const WITHDRAW = 25_000_000n;       // 0.025 SOL (harus > fee + dust; fee-cut dipotong dari sini)

const NETWORK = (process.env.CHAFF_NETWORK ?? "mainnet") as "mainnet" | "devnet";
const env0 = loadDotEnv(join(import.meta.dirname ?? ".", ".env"));
const HELIUS_KEY = (process.env.HELIUS_API_KEY ?? env0.HELIUS_API_KEY ?? "").trim();
const ENDPOINTS = NETWORK === "mainnet"
  ? HELIUS_KEY
    ? { // jalur didukung SDK: helius root meminjamkan /v1/spr ke indexer+prover (endpoint.js zolanaServiceUrl)
        rpc: `https://mainnet.helius-rpc.com/?api-key=${HELIUS_KEY}`,
        ws: `wss://mainnet.helius-rpc.com/?api-key=${HELIUS_KEY}`,
        indexer: undefined as string | undefined,
        prover: undefined as string | undefined,
        tee: SignedTeePolicy.forNetwork("mainnet"),
      }
    : { rpc: "https://api.mainnet-beta.solana.com", ws: "wss://api.mainnet-beta.solana.com",
        indexer: "https://dgcj4pjarvo65.cloudfront.net", prover: "https://d3ky2kt0ntqxt1.cloudfront.net",
        tee: SignedTeePolicy.forNetwork("mainnet") }
  : {
      rpc: "https://api.devnet.solana.com",
      ws: "wss://api.devnet.solana.com",
      indexer: "https://d34xe1hqb2ibg2.cloudfront.net",
      prover: "https://dd73hh473h6ha.cloudfront.net",
      tee: SignedTeePolicy.forNetwork("devnet"),
    };
const RPC_URL = process.env.CHAFF_RPC ?? ENDPOINTS.rpc;
const RPC_WS = process.env.CHAFF_RPC_WS ?? ENDPOINTS.ws;

// VERSION SHIM TEE (README + TECH-DESIGN T1): format policy baru {release, freshness} tidak bisa
// diverifikasi oleh SDK 0.8.0-alpha dan skema signature-nya belum terdokumentasi. Pendekatan:
// PCR measurements DI-EMBED sebagai konstanta (sumber: URL pinned Helius via HTTPS, 2026-11-22,
// sha256(payload) == release_sha256 dalam freshness terverifikasi). File yang di-fetch TOLAK jika
// measurements/policy != embedded. Attestasi enclave (PCR/nonce/HPKE) tetap diverifikasi SDK.
const TEE_POLICY_URL = "https://d3gbdb0egjwcw9.cloudfront.net/tee-policy/mainnet.json";
const TEE_EMBEDDED = {
  network: "mainnet",
  version: 5,
  expiresAt: 1801650052,
  measurements: [
    {
      pcr0: "de01051f48dec20d40d3666a99dbe14917b2e350f500981d77c85d5fc6a0a21917e8f695d6a4465d68a21e7eef942121",
      pcr1: "4b4d5b3661b3efc12920900c80e126e4ce783c522de6c02a2a5bf7af3a2b9327b86776f188e4be1c1c404a129dbda493",
      pcr2: "d2d4d066c3226e4cf89fdd143362dc63611978bb81a244db011c74623d3d9a37c5b8f275ca6363fe71c0df3245e50d4b",
    },
    {
      pcr0: "5d5b9e4c051c99c21c2553419850c36ea2c1889cc406fe5d92f264a2a89b3b65f9cc57df82c47db8d143db74df0cff98",
      pcr1: "4b4d5b3661b3efc12920900c80e126e4ce783c522de6c02a2a5bf7af3a2b9327b86776f188e4be1c1c404a129dbda493",
      pcr2: "a40538edc43176376d9619a4fffdc264c0ab1e22052ede82f9d20b475a07bbdcc14f0e0e08308e56224696609f3c0f7d",
    },
  ],
};

async function verifiedMainnetTeePolicy(): Promise<ReturnType<typeof teePolicyFromJson>> {
  let res: Response | undefined;
  for (const delay of [0, 2000, 6000]) {
    if (delay) await new Promise((r) => setTimeout(r, delay));
    try { res = await jfetch(TEE_POLICY_URL); break; } catch { /* retry */ }
  }
  if (!res?.ok) throw new Error(`tee policy HTTP ${res?.status ?? "unreachable"}`);
  const file: any = await res.json();
  const payload = JSON.parse(Buffer.from(file.release?.payload ?? file.payload, "hex").toString("utf8"));
  if (payload.network !== TEE_EMBEDDED.network) throw new Error(`tee network ${payload.network}`);
  if (payload.version < TEE_EMBEDDED.version) throw new Error("tee policy rollback");
  if (payload.expires_at < Math.floor(Date.now() / 1000)) throw new Error("tee policy expired");
  if (payload.policy?.platform !== "aws-nitro") throw new Error("tee platform berubah");
  const served = JSON.stringify(payload.policy.measurements);
  const pinned = JSON.stringify(TEE_EMBEDDED.measurements);
  if (served !== pinned) throw new Error("measurements berubah dari yang di-embed — JANGAN lanjut tanpa review");
  return teePolicyFromJson({ ...payload.policy, gpu: "optional", max_age_secs: 600 });
}

const step = (n: string, msg: string) => console.log(`[${n}] ${msg}`);
const fail = (n: string, e: unknown): never => {
  console.error(`[${n}] FAILED: ${e instanceof Error ? e.message : String(e)}`);
  process.exit(1);
};

/**
 * VERSION SHIM (T1, tercatat di README/TECH-DESIGN): API Helius ter-deploy mengembalikan
 * getShieldedTransactionsBy{Tags,Nullifiers} sebagai {context, outputTreeId, data:[{signature, events[]}], paginationToken},
 * sedangkan SDK 0.8.0-alpha mengharapkan {context, outputTreeId, transactions:[event...]}.
 * Transformasi HANYA menata ulang respons (tidak menyentuh kripto/kunci). Hapus saat SDK menyusul API.
 */
/**
 * VERSION SHIM (T1, tercatat di README/TECH-DESIGN): API Helius ter-deploy membungkus hasil
 * per-signature ({data:[{signature, events[]|outputs[]}]}) dan memakai `data`/`paginationToken`,
 * sedangkan SDK 0.8.0-alpha mengharapkan `transactions`/`matches` flat. Transformasi HANYA
 * menata ulang respons (tidak menyentuh kripto/kunci). Hapus saat SDK menyusul API.
 */
function shimIndexerResponse(url: string, body: string): string {
  const txs = /(getShieldedTransactionsByTags|getShieldedTransactionsByNullifiers)/.test(url);
  const utxos = /getEncryptedUtxosByTags/.test(url);
  if (!txs && !utxos) return body;
  try {
    const j = JSON.parse(body);
    if (j?.result?.data && !j.result.transactions && !j.result.matches) {
      const { data, paginationToken, ...rest } = j.result;
      j.result = txs
        ? { ...rest, transactions: data.flatMap((d: { events?: unknown[] }) => d.events ?? []) }
        : { ...rest, matches: data.flatMap((d: { outputs?: unknown[] }) => d.outputs ?? []) };
      return JSON.stringify(j);
    }
  } catch { /* biarkan respons apa adanya */ }
  return body;
}

function shimFetch(next: typeof fetch): typeof fetch {
  return async (input, init) => {
    const res = await next(input as any, init);
    const url = typeof input === "string" ? input : input instanceof URL ? input.href : (input as Request).url ?? String(input);
    if (!/(getShieldedTransactionsByTags|getShieldedTransactionsByNullifiers|getEncryptedUtxosByTags)/.test(String(url))) return res;
    const body = await res.text();
    return new Response(shimIndexerResponse(String(url), body), {
      status: res.status, statusText: res.statusText, headers: res.headers,
    });
  };
}

const HTTP_TIMEOUT = 30_000;
const jfetch = (url: string, init?: RequestInit) => fetch(url, { ...init, signal: AbortSignal.timeout(HTTP_TIMEOUT) });

async function rpc(method: string, params: unknown[]): Promise<any> {
  let last: unknown;
  for (const delay of [0, 2000, 6000]) {
    if (delay) await new Promise((r) => setTimeout(r, delay));
    try {
      const res = await jfetch(RPC_URL, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ jsonrpc: "2.0", id: 1, method, params }),
      });
      const j: any = await res.json();
      if (j.error) throw new Error(`RPC ${method}: ${JSON.stringify(j.error)}`);
      return j.result;
    } catch (e) {
      last = e;
    }
  }
  throw last;
}

async function balance(pubkey: string): Promise<bigint> {
  const r = await rpc("getBalance", [pubkey, { commitment: "confirmed" }]);
  return BigInt(r.value);
}

async function checkFunded(owner: KeyPairSigner, recipient: KeyPairSigner): Promise<void> {
  const ob = await balance(owner.address);
  const rb = await balance(recipient.address);
  step("fund", `owner ${owner.address}: ${ob} | recipient ${recipient.address}: ${rb} lamports`);
  if (ob < OWNER_MIN) {
    console.error(
      `[fund] SALDO OWNER KURANG. Kirim MAINNET SOL ke ${owner.address}: >= ${OWNER_MIN} lamports (0.09 SOL) — punya ${ob}`);
    process.exit(1);
  }
  if (rb < RECIPIENT_TOPUP) {
    step("fund", `auto-fund recipient: ${RECIPIENT_TOPUP} lamports dari owner (plain transfer)`);
    await plainTransfer(owner, recipient.address, RECIPIENT_TOPUP);
  }
}

const SYSTEM_PROGRAM = "11111111111111111111111111111111" as Address;

let clientGlobal: Awaited<ReturnType<typeof createZolanaClient>>;
let sendAndConfirm: (t: any, o?: any) => Promise<void>;

async function plainTransfer(from: KeyPairSigner, to: Address, amount: bigint): Promise<void> {
  const { value: bh } = await clientGlobal.solanaRpc.getLatestBlockhash().send();
  const data = new Uint8Array(12);
  new DataView(data.buffer).setUint32(0, 2, true);          // system: Transfer
  new DataView(data.buffer).setBigUint64(4, amount, true);  // lamports
  const ix: Instruction = {
    programAddress: SYSTEM_PROGRAM,
    accounts: [
      { address: from.address, role: AccountRole.WRITABLE_SIGNER },
      { address: to, role: AccountRole.WRITABLE },
    ],
    data,
  };
  const msg = pipe(
    createTransactionMessage({ version: 0 }),
    (m) => setTransactionMessageFeePayerSigner(from, m),
    (m) => setTransactionMessageLifetimeUsingBlockhash(bh, m),
    (m) => appendTransactionMessageInstruction(ix, m),
  );
  const signed = await signTransactionMessageWithSigners(msg);
  await sendAndConfirm(signed, { commitment: "confirmed" });
  const sig = getSignatureFromTransaction(signed);
  console.log(`SIG fund-recipient ${String(from.address).slice(0, 8)}… -> ${String(to).slice(0, 8)}… : ${String(sig)}`);
}

interface KeyRecord {
  seed: string; // base64 32-byte owner seed
}
function loadDotEnv(file: string): Record<string, string> {
  const out: Record<string, string> = {};
  if (!existsSync(file)) return out;
  for (const line of readFileSync(file, "utf8").split("\n")) {
    const t = line.trim();
    if (!t || t.startsWith("#")) continue;
    const i = t.indexOf("=");
    if (i <= 0) continue;
    out[t.slice(0, i).trim()] = t.slice(i + 1).trim();
  }
  return out;
}

function parseOwnerKey(raw: string): Uint8Array {
  const s = raw.trim();
  if (s.startsWith("[") && s.endsWith("]")) {
    const arr = JSON.parse(s) as number[];
    if (!arr.every((n) => Number.isInteger(n) && n >= 0 && n <= 255)) throw new Error("key JSON array invalid");
    return new Uint8Array(arr);
  }
  if (/^[0-9a-fA-F]+$/.test(s) && s.length % 2 === 0) return new Uint8Array(Buffer.from(s, "hex"));
  if (/^[1-9A-HJ-NP-Za-km-z]+$/.test(s)) return new Uint8Array(getBase58Encoder().encode(s));
  throw new Error("CHAFF_OWNER_KEY format tidak dikenali (base58 / hex / JSON array)");
}

function loadOwnerFromEnv(): Bytes32 {
  const env = loadDotEnv(join(import.meta.dirname ?? ".", ".env"));
  const raw = env.CHAFF_OWNER_KEY;
  if (!raw) {
    console.error("[key] CHAFF_OWNER_KEY kosong di chaff/poc/.env — isi private key wallet kamu (base58/hex/JSON), lalu jalankan lagi.");
    process.exit(1);
  }
  const bytes = parseOwnerKey(raw);
  if (bytes.length !== 32 && bytes.length !== 64) throw new Error(`private key harus 32 atau 64 byte, dapat ${bytes.length}`);
  const seed = bytes.length === 64 ? bytes.slice(0, 32) : bytes;
  return seed as Bytes32;
}

function loadRecipientSeed(): Bytes32 {
  const env = loadDotEnv(join(import.meta.dirname ?? ".", ".env"));
  const raw = env.CHAFF_RECIPIENT_KEY;
  if (raw) {
    const bytes = parseOwnerKey(raw);
    if (bytes.length !== 32 && bytes.length !== 64) throw new Error(`recipient key harus 32 atau 64 byte, dapat ${bytes.length}`);
    const seed = bytes.length === 64 ? bytes.slice(0, 32) : bytes;
    console.log("[key] recipient key loaded from .env CHAFF_RECIPIENT_KEY");
    return seed as Bytes32;
  }
  const file = join(import.meta.dirname ?? ".", ".devnet-key-recipient.json");
  let rec: KeyRecord | undefined;
  if (existsSync(file)) {
    rec = JSON.parse(readFileSync(file, "utf8")) as KeyRecord;
  } else {
    mkdirSync(dirname(file), { recursive: true });
    rec = { seed: Buffer.from(crypto.getRandomValues(new Uint8Array(32))).toString("base64") };
    writeFileSync(file, JSON.stringify(rec, null, 2));
    console.log(`[key] new devnet seed for recipient written to ${file} (gitignored)`);
  }
  const seed = new Uint8Array(Buffer.from(rec!.seed, "base64"));
  if (seed.length !== 32) throw new Error("seed must be 32 bytes");
  return seed as Bytes32;
}

async function submit(
  sendAndConfirm: (t: any, o?: any) => Promise<void>,
  tx: Transaction,
  signers: KeyPairSigner[],
  label: string,
): Promise<Signature> {
  const signed = await signTransactionWithSigners(signers, tx);
  await sendAndConfirm(signed, { commitment: "confirmed" });
  const sig = getSignatureFromTransaction(signed);
  console.log(`SIG ${label}: ${String(sig)}`);
  return sig;
}

async function confirmTx(client: any, sig: string): Promise<bigint> {
  try {
    return await client.confirmTransaction(sig as any);
  } catch (e) {
    step("confirm", `client poll gagal (${e instanceof Error ? e.message : String(e)}); fallback getTransaction`);
    for (let i = 0; i < 12; i++) {
      const r = await rpc("getTransaction", [sig, { commitment: "confirmed", maxSupportedTransactionVersion: 1 }]);
      if (r?.slot) return BigInt(r.slot);
      await new Promise((res) => setTimeout(res, 3000));
    }
    throw new Error("transaction tidak ditemukan setelah 36s");
  }
}

async function syncSafe(args: any): Promise<void> {
  let last: unknown;
  for (const delay of [0, 3000, 9000]) {
    if (delay) await new Promise((r) => setTimeout(r, delay));
    try {
      await syncWallet(args);
      return;
    } catch (e) {
      last = e;
      step("sync", `retry setelah: ${e instanceof Error ? e.message : String(e)}`);
    }
  }
  throw last;
}

async function main(): Promise<void> {
  const ownerSeed = loadOwnerFromEnv();
  const recipientSeed = loadRecipientSeed();

  const owner = await createKeyPairSignerFromPrivateKeyBytes(ownerSeed);
  const recipient = await createKeyPairSignerFromPrivateKeyBytes(recipientSeed);
  step("keys", `owner (wallet kamu) ${owner.address}`);
  step("keys", `recipient (fee payer withdraw) ${recipient.address}`);

  const client = await createZolanaClient({
    solanaRpcUrl: RPC_URL,
    solanaRpcSubscriptionsUrl: RPC_WS,
    ...(ENDPOINTS.indexer ? { indexerUrl: ENDPOINTS.indexer } : {}),
    ...(ENDPOINTS.prover ? { proverUrl: ENDPOINTS.prover } : {}),
    proverTee: NETWORK === "mainnet" ? await verifiedMainnetTeePolicy() : ENDPOINTS.tee,
    fetch: shimFetch(globalThis.fetch),
  });
  step("client", `zolana client ready (${NETWORK}${HELIUS_KEY ? ", helius gateway /v1/spr" : ", public endpoints"}; TEE policy verified)`);
  clientGlobal = client;
  sendAndConfirm = sendAndConfirmTransactionFactory({
    rpc: client.solanaRpc,
    rpcSubscriptions: client.solanaRpcSubscriptions,
  }) as (t: any, o?: any) => Promise<void>;

  await checkFunded(owner, recipient);

  const ownerKp = ShieldedKeypair.fromKeypair(SigningKey.fromEd25519Bytes(ownerSeed));
  const recipientKp = ShieldedKeypair.fromKeypair(SigningKey.fromEd25519Bytes(recipientSeed));
  const ownerWallet = new Wallet({ identity: ownerKp.shieldedAddress() });
  const recipientWallet = new Wallet({ identity: recipientKp.shieldedAddress() });
  const ownerKeys = LocalKeys.fromKeypair(ownerKp, client.proofService);
  const recipientKeys = LocalKeys.fromKeypair(recipientKp, client.proofService);

  // 1) register (registrasi recipient di-sponsori owner: payer = owner.address)
  {
    const tx = await buildRegistrationTransaction({ client, owner: owner.address, address: ownerKp.shieldedAddress() });
    if (tx === undefined) {
      console.log(`SIG register ${owner.address}: already registered (undefined)`);
    } else {
      await submit(sendAndConfirm, tx, [owner], `register owner ${owner.address.slice(0, 8)}…`);
    }
    const rtx = await buildRegistrationTransaction({
      client, owner: recipient.address, address: recipientKp.shieldedAddress(), payer: owner.address,
    });
    if (rtx === undefined) {
      console.log(`SIG register ${recipient.address}: already registered (undefined)`);
    } else {
      await submit(sendAndConfirm, rtx, [owner, recipient], `register recipient ${recipient.address.slice(0, 8)}… (sponsor: owner)`);
    }
  }

  // re-entrant: sinkronkan dulu; deposit hanya kalau saldo privat belum cukup utk transfer+withdraw
  await syncSafe({ client, wallet: ownerWallet, keys: ownerKeys });
  const have = BigInt(ownerWallet.balance(SOL_MINT).amount);
  const need = TRANSFER + WITHDRAW;
  let depSig: Signature | undefined;
  if (have >= need) {
    step("deposit", `skip — private balance ${have} lamports >= ${need} (deposit run sebelumnya sudah on-chain)`);
  } else {
    step("deposit", `owner deposits ${DEPOSIT} lamports to own shielded address (punya ${have})`);
    const dep = await buildDepositTransaction({
      client,
      feePayer: owner.address,
      recipient: ownerKp.shieldedAddress(),
      amount: DEPOSIT,
    });
    depSig = await submit(sendAndConfirm, dep, [owner], "deposit");
    const depSlot = await confirmTx(client, depSig);
    await syncSafe({ client, wallet: ownerWallet, keys: ownerKeys, config: { requireSlot: depSlot } });
  }
  step("deposit", `private balance now ${ownerWallet.balance(SOL_MINT).amount} lamports`);

  // 2) private transfer owner -> recipient (both registered); skip jika recipient sudah pernah terima
  await syncSafe({ client, wallet: recipientWallet, keys: recipientKeys });
  const rcv = BigInt(recipientWallet.balance(SOL_MINT).amount);
  let trSig: Signature | undefined;
  if (rcv >= TRANSFER) {
    step("transfer", `skip — recipient private balance ${rcv} lamports >= ${TRANSFER}`);
  } else {
    step("transfer", `private transfer ${TRANSFER} lamports to ${recipient.address}`);
    const tr = await buildTransferTransaction({
      client,
      wallet: ownerWallet,
      keys: ownerKeys,
      feePayer: owner.address,
      recipient: recipient.address,
      amount: TRANSFER,
    });
    trSig = await submit(sendAndConfirm, tr, [owner], "private-transfer");
    const trSlot = await confirmTx(client, trSig);
    await syncSafe({ client, wallet: ownerWallet, keys: ownerKeys, config: { requireSlot: trSlot } });
  }

  // 3) withdraw with fee-cut: feePayer = recipient (public recipient signs; fee dipotong dari output)
  step("withdraw", `withdraw ${WITHDRAW} lamports to ${recipient.address} with feePayer = recipient (fee-cut, no buffer)`);
  await syncSafe({ client, wallet: ownerWallet, keys: ownerKeys });
  const wd = await buildWithdrawalTransaction({
    client,
    wallet: ownerWallet,
    keys: ownerKeys,
    feePayer: recipient.address,
    recipient: recipient.address,
    amount: WITHDRAW,
  });
  const wdSig = await submit(sendAndConfirm, wd, [recipient, owner], "withdraw-fee-cut");
  const wdSlot = await confirmTx(client, wdSig);
  await syncSafe({ client, wallet: ownerWallet, keys: ownerKeys, config: { requireSlot: wdSlot } });

  const recBal = await balance(recipient.address);
  const recPriv = BigInt(recipientWallet.balance(SOL_MINT).amount);
  step("done", `recipient: public ${recBal} lamports (fee-cut terlihat), private ${recPriv} lamports`);
  step("done", `owner private sisa: ${ownerWallet.balance(SOL_MINT).amount} lamports`);
  console.log("\nPOC RESULT");
  console.log(JSON.stringify({
    network: NETWORK, owner: owner.address, recipient: recipient.address,
    deposit: depSig ?? "skipped (already funded)", transfer: trSig ?? "skipped (already funded)",
    withdrawFeeCut: wdSig, recipientPublicBalance: recBal.toString(), recipientPrivateBalance: recPriv.toString(),
  }, null, 2));
}

main().catch((e) => fail("poc", e));
