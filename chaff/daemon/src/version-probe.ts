import { jfetch, verifiedMainnetTeePolicy } from "./shims.js";
import type { ProbeResult } from "./types.js";

export interface ProbeArgs {
  readonly indexerUrl?: string;
  readonly indexerApiKey?: string;
}

// Raw (unshimmed) indexer RPC. Does the deployed API still wrap per-signature
// results as {result:{data:[...]}} (shim still needed — SDK @0.8.0-alpha < API) or is
// it already flat ({result:{transactions|matches}})? Inspecting the response PRE-shim
// is the honest check; going through the shimmed client would hide the very gap being
// probed. A failure to reach the indexer or an unexpected shape => kill (defensive).
async function probeIndexerShape(args: ProbeArgs): Promise<{
  needed: boolean;
  ok: boolean;
  reason?: string;
}> {
  if (!args.indexerUrl)
    return { needed: true, ok: true, reason: "indexerUrl unset — assuming shim still required" };
  try {
    const res = await jfetch(args.indexerUrl, {
      method: "POST",
      headers: {
        "content-type": "application/json",
        ...(args.indexerApiKey ? { Authorization: `Bearer ${args.indexerApiKey}` } : {}),
      },
      body: JSON.stringify({
        jsonrpc: "2.0",
        id: 1,
        method: "getShieldedTransactionsByTags",
        params: [{ tags: [], limit: 1 }],
      }),
    });
    if (!res.ok) return { needed: true, ok: false, reason: `indexer HTTP ${res.status}` };
    const j = (await res.json()) as {
      result?: { data?: unknown[]; transactions?: unknown[]; matches?: unknown[] };
    };
    const wrapped =
      Array.isArray(j?.result?.data) && !j.result?.transactions && !j.result?.matches;
    return { needed: wrapped, ok: true };
  } catch (e) {
    return { needed: true, ok: false, reason: `indexer probe: ${(e as Error).message}` };
  }
}

// Version probe (TECH-DESIGN §4). Two checks; a mismatch on either auto-engages the
// kill switch with a clear reason:
//   (1) TEE policy — fetch the pinned URL, reject if network/version/expiry/platform or
//       PCR measurements differ from the embedded constants (kill-critical).
//   (2) indexer shape — one getShieldedTransactionsByTags RPC; if the API has evolved
//       past the shim (flat where wrapped was expected, or unreachable) => kill.
export async function runVersionProbe(args: ProbeArgs): Promise<ProbeResult> {
  let teeOk = false;
  let reason: string | undefined;
  try {
    await verifiedMainnetTeePolicy();
    teeOk = true;
  } catch (e) {
    reason = `tee policy mismatch: ${(e as Error).message}`;
    return { shimStillNeeded: true, teeOk: false, kill: true, reason };
  }
  const ix = await probeIndexerShape(args);
  if (!ix.ok) return { shimStillNeeded: true, teeOk, kill: true, reason: ix.reason };
  return { shimStillNeeded: ix.needed, teeOk, kill: false };
}
