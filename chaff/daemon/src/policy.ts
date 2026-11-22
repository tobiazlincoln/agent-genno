import { readFileSync } from "node:fs";
import type { PolicyConfig, PolicyDecision } from "./types.js";

export class PolicyEngine {
  constructor(private readonly cfg: PolicyConfig) {}

  get killSwitch(): boolean {
    return this.cfg.killSwitch;
  }
  get dailyCapLamports(): bigint {
    return BigInt(this.cfg.dailyCapLamports);
  }
  get payeeAllowlist(): readonly string[] {
    return this.cfg.payeeAllowlist;
  }

  // Enforced BEFORE the planner runs. Any refusal halts the flow with a clear reason.
  enforce(args: {
    recipient: string;
    amountLamports: bigint;
    spentTodayLamports: bigint;
  }): PolicyDecision {
    if (this.cfg.killSwitch)
      return { ok: false, reason: "kill switch is ON — all sends refused" };
    if (!this.cfg.payeeAllowlist.includes(args.recipient))
      return { ok: false, reason: `payee ${args.recipient.slice(0, 8)}… not in allowlist` };
    const cap = BigInt(this.cfg.dailyCapLamports);
    if (args.spentTodayLamports + args.amountLamports > cap)
      return {
        ok: false,
        reason: `daily cap exceeded: spent ${args.spentTodayLamports} + this ${args.amountLamports} > cap ${cap} lamports`,
      };
    return { ok: true };
  }
}

export function loadPolicyConfig(path: string): PolicyConfig {
  const raw = JSON.parse(readFileSync(path, "utf8")) as PolicyConfig;
  if (typeof raw.killSwitch !== "boolean")
    throw new Error(`policy: killSwitch must be boolean in ${path}`);
  if (typeof raw.dailyCapLamports !== "string")
    throw new Error(`policy: dailyCapLamports must be string (bigint-safe) in ${path}`);
  if (!Array.isArray(raw.payeeAllowlist))
    throw new Error(`policy: payeeAllowlist must be array in ${path}`);
  return raw;
}
