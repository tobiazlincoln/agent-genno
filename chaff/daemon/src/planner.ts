import type { Rng } from "./rng.js";
import type { PlannedEvent, SplitResult } from "./types.js";

const MIN_PART_LAMPORTS = 1000n;
const ROUND_UNIT = 10_000_000n; // 0.01 SOL — parts must NOT be a round multiple of this (legibility signal)
const DEN_64 = 1n << 64n;
const MIN_DELAY_HOURS = 1;
const MAX_DELAY_HOURS = 72;

export interface PlannerDeps {
  rng: Rng;
}

function readU64(b: Uint8Array): bigint {
  let v = 0n;
  for (let i = 0; i < 8; i++) v |= BigInt(b[i]) << (8n * BigInt(i));
  return v;
}

// Split totalLamports into 3-5 parts via random BigInt cut points (stars-and-bars over
// the remainder after a per-part floor). Cut points are random fractions of the remainder
// scaled by a 64-bit random numerator, so part sizes are arbitrary (non-round) bigints.
// Total is preserved EXACTLY by construction (sum of gaps == remainder). A de-round guard
// perturbs any part that happens to be a round multiple of 0.01 SOL, stealing from the
// largest other part to preserve the total. Injectable RNG => deterministic under a seed.
export function planSplit(totalLamports: bigint, deps: PlannerDeps): SplitResult {
  if (totalLamports <= 0n) throw new Error("planner: total must be positive");
  const partCount = 3 + deps.rng.int(3); // 3..5
  if (totalLamports < MIN_PART_LAMPORTS * BigInt(partCount))
    throw new Error(`planner: total ${totalLamports} too small for ${partCount} parts (min ${MIN_PART_LAMPORTS} each)`);

  const remainder = totalLamports - MIN_PART_LAMPORTS * BigInt(partCount);
  const cuts: bigint[] = [];
  for (let i = 0; i < partCount - 1; i++) {
    cuts.push((remainder * readU64(deps.rng.bytes(8))) / DEN_64);
  }
  cuts.sort((a, b) => (a < b ? -1 : a > b ? 1 : 0));
  for (let i = 1; i < cuts.length; i++) {
    if (cuts[i] <= cuts[i - 1]) cuts[i] = cuts[i - 1] + 1n; // dedupe (2^64 collision ~ never)
  }
  const bounds = [0n, ...cuts, remainder];

  const parts: PlannedEvent[] = [];
  for (let i = 0; i < partCount; i++) {
    const amount = MIN_PART_LAMPORTS + (bounds[i + 1] - bounds[i]);
    const delayHours = MIN_DELAY_HOURS + deps.rng.int(MAX_DELAY_HOURS - MIN_DELAY_HOURS + 1); // 1..72 inclusive
    parts.push({ index: i + 1, amountLamports: amount, delayHours });
  }

  deRound(parts, deps.rng);

  // safety net: exact total correction on the last part (0n in practice)
  const sum = parts.reduce((s, p) => s + p.amountLamports, 0n);
  const diff = totalLamports - sum;
  if (diff !== 0n) parts[parts.length - 1].amountLamports += diff;

  const finalSum = parts.reduce((s, p) => s + p.amountLamports, 0n);
  if (finalSum !== totalLamports)
    throw new Error(`planner: total mismatch ${finalSum} != ${totalLamports}`);
  return { totalLamports, parts };
}

function deRound(parts: PlannedEvent[], rng: Rng): void {
  for (let i = 0; i < parts.length; i++) {
    if (parts[i].amountLamports % ROUND_UNIT === 0n) {
      const perturb = 1n + BigInt(rng.int(Number(ROUND_UNIT - 1n))); // 1..(ROUND_UNIT-1)
      parts[i].amountLamports += perturb;
      let target = -1;
      let best = 0n;
      for (let j = 0; j < parts.length; j++) {
        if (j === i) continue;
        if (parts[j].amountLamports > best) {
          best = parts[j].amountLamports;
          target = j;
        }
      }
      if (target === -1 || parts[target].amountLamports - perturb < MIN_PART_LAMPORTS)
        throw new Error("planner: de-round could not preserve total");
      parts[target].amountLamports -= perturb;
    }
  }
}
