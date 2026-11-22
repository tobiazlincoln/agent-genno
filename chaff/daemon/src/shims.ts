import { SignedTeePolicy, teePolicyFromJson } from "@heliuslabs/zolana/client";

// =============================================================================
// VERSION SHIMS — copied verbatim from chaff/poc/run-poc.ts (proven PoC mainnet).
// Two shims are MANDATORY in every zolana client build because the deployed Helius
// API is newer than SDK @heliuslabs/zolana@0.8.0-alpha. Remove only when the SDK
// catches up (the version probe below reports shimStillNeeded === false).
// =============================================================================

// --- Shim 2: TEE policy. PCR measurements pinned as constants (source: pinned Helius
// URL via HTTPS, 2026-11-22). The fetched file is REJECTED if measurements/policy != embedded.
// Enclave attestation (PCR/nonce/HPKE) is still verified by the SDK.
export const TEE_POLICY_URL = "https://d3gbdb0egjwcw9.cloudfront.net/tee-policy/mainnet.json";
export const TEE_EMBEDDED = {
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

const HTTP_TIMEOUT = 30_000;
export const jfetch = (url: string, init?: RequestInit): Promise<Response> =>
  fetch(url, { ...init, signal: AbortSignal.timeout(HTTP_TIMEOUT) });

export async function verifiedMainnetTeePolicy(): Promise<ReturnType<typeof teePolicyFromJson>> {
  let res: Response | undefined;
  for (const delay of [0, 2000, 6000]) {
    if (delay) await new Promise((r) => setTimeout(r, delay));
    try {
      res = await jfetch(TEE_POLICY_URL);
      break;
    } catch {
      /* retry */
    }
  }
  if (!res?.ok) throw new Error(`tee policy HTTP ${res?.status ?? "unreachable"}`);
  const file: { release?: { payload?: string }; payload?: string } = await res.json() as { release?: { payload?: string }; payload?: string };
  const payload = JSON.parse(
    Buffer.from(file.release?.payload ?? file.payload ?? "", "hex").toString("utf8"),
  ) as {
    network: string;
    version: number;
    expires_at: number;
    policy: { platform: string; measurements: unknown };
  };
  if (payload.network !== TEE_EMBEDDED.network) throw new Error(`tee network ${payload.network}`);
  if (payload.version < TEE_EMBEDDED.version) throw new Error("tee policy rollback");
  if (payload.expires_at < Math.floor(Date.now() / 1000)) throw new Error("tee policy expired");
  if (payload.policy?.platform !== "aws-nitro") throw new Error("tee platform berubah");
  const served = JSON.stringify(payload.policy.measurements);
  const pinned = JSON.stringify(TEE_EMBEDDED.measurements);
  if (served !== pinned)
    throw new Error("measurements berubah dari yang di-embed — JANGAN lanjut tanpa review");
  return teePolicyFromJson({ ...payload.policy, gpu: "optional", max_age_secs: 600 });
}

// --- Shim 1: indexer response shape. The deployed API wraps per-signature results as
// {data:[{signature, events[]|outputs[]}]} with paginationToken; the SDK expects
// `transactions`/`matches` flat. This ONLY rearranges the response (no crypto/keys).
export function shimIndexerResponse(url: string, body: string): string {
  const txs = /(getShieldedTransactionsByTags|getShieldedTransactionsByNullifiers)/.test(url);
  const utxos = /getEncryptedUtxosByTags/.test(url);
  if (!txs && !utxos) return body;
  try {
    const j = JSON.parse(body) as {
      result?: {
        data?: Array<{ events?: unknown[]; outputs?: unknown[] }>;
        transactions?: unknown[];
        matches?: unknown[];
        paginationToken?: unknown;
      };
    };
    if (j?.result?.data && !j.result.transactions && !j.result.matches) {
      const { data, paginationToken, ...rest } = j.result;
      void paginationToken;
      j.result = txs
        ? { ...rest, transactions: data.flatMap((d) => d.events ?? []) }
        : { ...rest, matches: data.flatMap((d) => d.outputs ?? []) };
      return JSON.stringify(j);
    }
  } catch {
    /* leave response as-is */
  }
  return body;
}

export function shimFetch(next: typeof fetch): typeof fetch {
  return async (input, init) => {
    const res = await next(input as Parameters<typeof fetch>[0], init);
    const url =
      typeof input === "string"
        ? input
        : input instanceof URL
          ? input.href
          : (input as Request).url ?? String(input);
    if (
      !/(getShieldedTransactionsByTags|getShieldedTransactionsByNullifiers|getEncryptedUtxosByTags)/.test(
        String(url),
      )
    )
      return res;
    const body = await res.text();
    return new Response(shimIndexerResponse(String(url), body), {
      status: res.status,
      statusText: res.statusText,
      headers: res.headers,
    });
  };
}

export { SignedTeePolicy };
