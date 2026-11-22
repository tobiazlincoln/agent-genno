import { buildTransferTransaction, type Address } from "@heliuslabs/zolana";
import {
  buildOwnerContext,
  endpointsFromEnv,
  type OwnerContext,
} from "./client.js";
import { syncDaemonWallet } from "./sync.js";
import { runVersionProbe } from "./version-probe.js";
import { planSplit } from "./planner.js";
import { CsprngRng, SeededRng, type Rng } from "./rng.js";
import { loadPolicyConfig, PolicyEngine } from "./policy.js";
import {
  getSignatureFromTransaction,
  sendAndConfirmTransactionFactory,
  signTransactionWithSigners,
  type SendAndConfirm,
} from "./kit-bridge.js";

export interface ExecuteArgs {
  readonly configPath: string;
  readonly amount: bigint;
  readonly recipient: string;
  readonly seed?: string;
}

// --execute path (TECH-DESIGN §1/§4/§5/§7). Order is load-bearing:
//   enforce policy -> version probe (kill on mismatch) -> build owner context (wires
//   BOTH shims) -> sync persisted wallet -> plan split -> sign+send one private
//   transfer per scheduled part, sleeping the planned delay between sends.
// WIRED BUT NOT EXECUTED this session ("Eksekusi tx nyata TIDAK diperlukan sesi ini"):
// it needs .env (CHAFF_OWNER_KEY, HELIUS_API_KEY) and mainnet private balance.
export async function runExecute(args: ExecuteArgs): Promise<number> {
  const cfg = loadPolicyConfig(args.configPath);
  const engine = new PolicyEngine(cfg);

  // Re-enforce at the execute gate (defense in depth; the dry-run path already
  // checks policy, and policy is the gate before the planner).
  const decision = engine.enforce({
    recipient: args.recipient,
    amountLamports: args.amount,
    spentTodayLamports: 0n,
  });
  if (!decision.ok) {
    console.error(`execute: policy refused — ${decision.reason}`);
    return 2;
  }

  const endpoints = endpointsFromEnv();

  // (1) Version probe BEFORE any sync/spend. TEE measurement mismatch => auto kill.
  const probe = await runVersionProbe({
    indexerUrl: endpoints.indexerUrl,
    indexerApiKey: process.env.HELIUS_API_KEY,
  });
  if (probe.kill) {
    console.error(`execute: version probe FAILED — auto kill-switch. ${probe.reason ?? ""}`);
    console.error("execute: refusing to sync or sign. Review src/shims.ts or pin a matching SDK.");
    return 3;
  }
  if (probe.shimStillNeeded)
    console.error(
      "execute: note — indexer shim still required (SDK @heliuslabs/zolana@0.8.0-alpha < deployed API).",
    );

  // (2) Build owner context (loads CHAFF_OWNER_KEY, wires BOTH mandatory shims).
  const owner: OwnerContext = await buildOwnerContext(endpoints);

  // (3) Sync persisted wallet (encrypted snapshot under state/, gitignored).
  const synced = await syncDaemonWallet({
    client: owner.client,
    wallet: owner.wallet,
    keys: owner.keys,
    keypair: owner.keypair,
    stateDir: "state",
  });
  console.error(
    `execute: wallet synced, encrypted snapshot ${synced.snapshot.length} bytes (state/wallet.snapshot).`,
  );

  // (4) Plan the split (3-5 non-round parts, 1-72h delays; deterministic if seeded).
  const rng: Rng = args.seed ? new SeededRng(args.seed) : new CsprngRng();
  const plan = planSplit(args.amount, { rng });

  // (5) Build + sign + send one private transfer per scheduled part.
  const confirm: SendAndConfirm = sendAndConfirmTransactionFactory({
    rpc: owner.client.solanaRpc,
    rpcSubscriptions: owner.client.solanaRpcSubscriptions,
  });
  const feePayer: Address = owner.signer.address;
  const recipientDest = args.recipient as Address;
  let sent = 0;
  for (const part of plan.parts) {
    const tx = await buildTransferTransaction({
      client: owner.client,
      wallet: owner.wallet,
      keys: owner.keys,
      feePayer,
      recipient: recipientDest,
      amount: part.amountLamports,
    });
    const signed = await signTransactionWithSigners([owner.signer], tx);
    await confirm(signed, { commitment: "confirmed" });
    const sig = getSignatureFromTransaction(signed);
    sent++;
    console.error(
      `execute: sent part #${part.index} — ${part.amountLamports} lamports, sig ${sig}, next in ${part.delayHours}h`,
    );
    if (part.delayHours > 0)
      await new Promise((r) => setTimeout(r, part.delayHours * 3_600_000));
  }
  console.error(`execute: complete — ${sent}/${plan.parts.length} transfers sent.`);
  return 0;
}
