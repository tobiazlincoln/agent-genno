import { parseArgs } from "node:util";
import { resolve } from "node:path";
import { loadPolicyConfig, PolicyEngine } from "./policy.js";
import { planSplit } from "./planner.js";
import { CsprngRng, SeededRng, type Rng } from "./rng.js";

interface CliArgs {
  readonly dryRun: boolean;
  readonly execute: boolean;
  readonly seed: string | undefined;
  readonly config: string;
  readonly amount: bigint;
  readonly recipient: string | undefined;
}

function parseAmount(s: string | undefined): bigint {
  if (!s) return 15_000_000n;
  if (!/^\d+$/.test(s))
    throw new Error(`--amount must be a positive integer (lamports), got "${s}"`);
  return BigInt(s);
}

function readArgs(): CliArgs {
  const { values } = parseArgs({
    options: {
      "dry-run": { type: "boolean", default: false },
      execute: { type: "boolean", default: false },
      seed: { type: "string" },
      config: { type: "string", default: "config/policy.json" },
      amount: { type: "string" },
      recipient: { type: "string" },
    },
    strict: true,
  });
  const dryRun = Boolean(values["dry-run"]);
  const execute = Boolean(values.execute);
  if (dryRun && execute)
    throw new Error("--dry-run and --execute are mutually exclusive");
  // Dry-run is the DEFAULT: neither flag => dry-run. Real execution needs --execute.
  const wantDryRun = dryRun || !execute;
  return {
    dryRun: wantDryRun,
    execute,
    seed: typeof values.seed === "string" ? values.seed : undefined,
    config: values.config ?? "config/policy.json",
    amount: parseAmount(typeof values.amount === "string" ? values.amount : undefined),
    recipient: typeof values.recipient === "string" ? values.recipient : undefined,
  };
}

function makeRng(seed: string | undefined): Rng {
  return seed ? new SeededRng(seed) : new CsprngRng();
}

async function main(): Promise<number> {
  const args = readArgs();
  const cfg = loadPolicyConfig(resolve(args.config));
  const engine = new PolicyEngine(cfg);

  const recipient = args.recipient ?? cfg.payeeAllowlist[0] ?? "";
  if (!recipient) throw new Error("no --recipient given and policy allowlist is empty");

  // Policy is enforced BEFORE the planner in every mode (kill switch / daily cap /
  // payee allowlist). A refusal halts with a clear reason and exit 2.
  const decision = engine.enforce({
    recipient,
    amountLamports: args.amount,
    spentTodayLamports: 0n,
  });
  if (!decision.ok) {
    console.error(`policy: REFUSED — ${decision.reason}`);
    if (cfg.killSwitch)
      console.error("policy: kill switch is engaged; no sends will be built or signed.");
    return 2;
  }

  if (args.dryRun) {
    const rng = makeRng(args.seed);
    const plan = planSplit(args.amount, { rng });
    const sum = plan.parts.reduce((s, p) => s + p.amountLamports, 0n);
    console.log("=== chaff daemon — DRY RUN (no transactions signed) ===");
    console.log(`config:    ${resolve(args.config)}`);
    console.log(`recipient: ${recipient}`);
    console.log(`amount:    ${args.amount} lamports (${Number(args.amount) / 1e9} SOL)`);
    console.log(
      `rng:       ${args.seed ? `SeededRng("${args.seed}")` : "CsprngRng (crypto.randomBytes)"}`,
    );
    console.log(`parts:     ${plan.parts.length}`);
    console.log(`total:     ${sum} lamports (must equal ${args.amount})`);
    let acc = 0n;
    for (const p of plan.parts) {
      acc += p.amountLamports;
      const sol = Number(p.amountLamports) / 1e9;
      const round = p.amountLamports % 10_000_000n === 0n ? "ROUND!" : "non-round";
      console.log(
        `  #${p.index}  amount=${p.amountLamports} lamports (${sol.toFixed(9)} SOL)  delay=${p.delayHours}h  ${round}  running=${acc}`,
      );
    }
    console.log(
      `verify:    sum=${sum} ${sum === args.amount ? "== total OK" : "!= total BROKEN"}`,
    );
    return 0;
  }

  // --execute path: lazy-import so the dry-run path stays offline (no zolana/kit load).
  const { runExecute } = await import("./execute.js");
  return runExecute({
    configPath: resolve(args.config),
    amount: args.amount,
    recipient,
    seed: args.seed,
  });
}

main()
  .then((code) => process.exit(code))
  .catch((e) => {
    console.error(`fatal: ${(e as Error).message}`);
    process.exit(1);
  });
