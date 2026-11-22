import { createHash, randomBytes } from "node:crypto";

export interface Rng {
  int(maxExclusive: number): number;
  bytes(n: number): Uint8Array;
}

function assertRange(maxExclusive: number, n: number): void {
  if (maxExclusive <= 0 || !Number.isSafeInteger(maxExclusive))
    throw new Error(`rng: invalid bound ${maxExclusive}`);
  void n;
}

// Production CSPRNG backed by crypto.randomBytes. Rejection-sampled for uniformity.
export class CsprngRng implements Rng {
  int(maxExclusive: number): number {
    assertRange(maxExclusive, 0);
    const limit = Math.floor(0x100000000 / maxExclusive) * maxExclusive;
    let x = 0;
    do {
      x = randomBytes(4).readUInt32LE(0);
    } while (x >= limit);
    return x % maxExclusive;
  }
  bytes(n: number): Uint8Array {
    if (n <= 0 || !Number.isSafeInteger(n)) throw new Error(`rng: invalid n ${n}`);
    return randomBytes(n);
  }
}

// Deterministic PRNG for tests: SHA-256 counter keystream from a string seed.
// Same seed + same call order => identical byte stream, so identical schedules.
export class SeededRng implements Rng {
  private cursor = 0;
  constructor(private readonly seed: string) {}
  private block(i: number): Buffer {
    return createHash("sha256").update(`${this.seed}:${i}`).digest();
  }
  private take(n: number): Buffer {
    const out = Buffer.alloc(n);
    let written = 0;
    while (written < n) {
      const blockIdx = Math.floor(this.cursor / 32);
      const off = this.cursor % 32;
      const blk = this.block(blockIdx);
      const need = Math.min(32 - off, n - written);
      blk.copy(out, written, off, off + need);
      written += need;
      this.cursor += need;
    }
    return out;
  }
  int(maxExclusive: number): number {
    assertRange(maxExclusive, 0);
    const limit = Math.floor(0x100000000 / maxExclusive) * maxExclusive;
    let x = 0;
    do {
      x = this.take(4).readUInt32LE(0);
    } while (x >= limit);
    return x % maxExclusive;
  }
  bytes(n: number): Uint8Array {
    if (n <= 0 || !Number.isSafeInteger(n)) throw new Error(`rng: invalid n ${n}`);
    return new Uint8Array(this.take(n));
  }
}
