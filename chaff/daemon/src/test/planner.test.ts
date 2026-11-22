import { test } from "node:test";
import { ok, strictEqual } from "node:assert";
import { planSplit } from "../planner.js";
import { SeededRng } from "../rng.js";

function serialize(parts: { amountLamports: bigint; delayHours: number }[]): string {
  return parts.map((p) => `${p.amountLamports}/${p.delayHours}`).join(",");
}

// Proof #3 core: same seed + same call order => identical schedule.
test("deterministic: same seed => identical schedule", () => {
  const total = 25_000_000n;
  const a = planSplit(total, { rng: new SeededRng("chaff-determinism") });
  const b = planSplit(total, { rng: new SeededRng("chaff-determinism") });
  strictEqual(serialize(a.parts), serialize(b.parts));
});

// Total preserved exactly across many seeds (stars-and-bars + de-round + safety net).
test("total preserved exactly across random seeds", () => {
  for (const seed of ["s1", "s2", "s3", "s4", "s5", "s6", "s7", "s8"]) {
    const r = planSplit(100_000_000n, { rng: new SeededRng(seed) });
    const sum = r.parts.reduce((s, p) => s + p.amountLamports, 0n);
    strictEqual(sum, 100_000_000n, `seed ${seed}: total ${sum} != 100000000`);
  }
});

// Shape contract: 3-5 parts, delays in 1..72h inclusive, every part non-round.
test("shape: 3-5 parts, delays 1..72h, non-round sizes", () => {
  const r = planSplit(50_000_000n, { rng: new SeededRng("shape") });
  ok(r.parts.length >= 3 && r.parts.length <= 5, `parts ${r.parts.length} out of 3..5`);
  for (const p of r.parts) {
    ok(p.delayHours >= 1 && p.delayHours <= 72, `delay ${p.delayHours} out of 1..72`);
    ok(
      p.amountLamports % 10_000_000n !== 0n,
      `part #${p.index} amount ${p.amountLamports} is a round multiple of 0.01 SOL`,
    );
  }
});
