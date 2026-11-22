import {
  LocalKeys,
  SOL_MINT,
  ShieldedKeypair,
  SigningKey,
  Wallet,
  createZolanaClient,
  type Address,
  type Bytes32,
  type SyncWalletInput,
  type WalletKeys,
} from "@heliuslabs/zolana";
import { readFileSync } from "node:fs";
import { shimFetch, verifiedMainnetTeePolicy } from "./shims.js";
import { createKeyPairSignerFromPrivateKeyBytes, decodeBase58 } from "./kit-bridge.js";

// The full zolana client: indexer + Solana RPC + proof service + TEE. Built once,
// reused by sync + execute. Both mandatory shims (shimFetch for the indexer response
// shape, verifiedMainnetTeePolicy for the pinned PCR measurements) are wired here so
// there is a single place a zolana client is constructed.
export type ZolanaClient = Awaited<ReturnType<typeof createZolanaClient>>;
export type OwnerKeys = SyncWalletInput["keys"];

export interface Ed25519Signer {
  readonly address: Address;
  signTransaction(transaction: unknown): Promise<unknown>;
}

export interface ClientEndpoints {
  readonly rpcUrl: string;
  readonly rpcWsUrl: string;
  readonly indexerUrl?: string;
  readonly proverUrl?: string;
}

export interface OwnerContext {
  readonly client: ZolanaClient;
  readonly wallet: Wallet;
  readonly keys: WalletKeys;
  readonly keypair: ShieldedKeypair;
  readonly signer: Ed25519Signer;
}

function loadDotEnv(): NodeJS.ProcessEnv {
  if (process.env.CHAFF_OWNER_KEY && process.env.CHAFF_OWNER_KEY.trim())
    return process.env;
  // Local .env only when present (never required when the runner injects env).
  try {
    const text = readFileSync(".env", "utf8");
    const env: Record<string, string> = {};
    for (const line of text.split("\n")) {
      const m = /^\s*([A-Z_][A-Z0-9_]*)\s*=\s*(.*)\s*$/.exec(line);
      if (m && !m[1].startsWith("#")) env[m[1]] = m[2].replace(/^["']|["']$/g, "");
    }
    return { ...env, ...process.env } as NodeJS.ProcessEnv;
  } catch {
    return process.env;
  }
}

function loadOwnerSeed(): Bytes32 {
  const env = loadDotEnv();
  const raw = env.CHAFF_OWNER_KEY;
  if (!raw || !raw.trim())
    throw new Error("client: CHAFF_OWNER_KEY missing from environment/.env");
  const bytes = decodeBase58(raw.trim());
  if (bytes.length !== 32 && bytes.length !== 64)
    throw new Error(`client: owner key must be 32 or 64 bytes, got ${bytes.length}`);
  return (bytes.length === 64 ? bytes.subarray(0, 32) : bytes) as unknown as Bytes32;
}

export function endpointsFromEnv(): ClientEndpoints {
  const env = loadDotEnv();
  const rpc =
    env.SOLANA_RPC_URL ??
    `https://mainnet.helius-rpc.com/?api-key=${env.HELIUS_API_KEY ?? ""}`;
  const ws = env.SOLANA_WS_URL ?? rpc.replace(/^http/, "ws");
  return {
    rpcUrl: rpc,
    rpcWsUrl: ws,
    indexerUrl: env.CHAFF_INDEXER_URL,
    proverUrl: env.CHAFF_PROVER_URL,
  };
}

export async function buildOwnerContext(endpoints: ClientEndpoints): Promise<OwnerContext> {
  const seed = loadOwnerSeed();
  const signer = (await createKeyPairSignerFromPrivateKeyBytes(seed)) as Ed25519Signer;
  const client = await createZolanaClient({
    solanaRpcUrl: endpoints.rpcUrl,
    solanaRpcSubscriptionsUrl: endpoints.rpcWsUrl,
    ...(endpoints.indexerUrl ? { indexerUrl: endpoints.indexerUrl } : {}),
    ...(endpoints.proverUrl ? { proverUrl: endpoints.proverUrl } : {}),
    proverTee: await verifiedMainnetTeePolicy(),
    fetch: shimFetch(globalThis.fetch),
  });
  const keypair = ShieldedKeypair.fromKeypair(SigningKey.fromEd25519Bytes(seed));
  const wallet = new Wallet({ identity: keypair.shieldedAddress() });
  const keys = LocalKeys.fromKeypair(keypair, client.proofService);
  return { client, wallet, keys, keypair, signer };
}

export { SOL_MINT };
