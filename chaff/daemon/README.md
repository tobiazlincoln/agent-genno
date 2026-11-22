# chaff daemon — local skeleton

Sync, policy, planner, version probe. **Dry-run is the default** — no transaction is
signed unless `--execute` is passed AND policy passes AND the version probe is clean.

## Layout

| module | role |
|---|---|
| `src/rng.ts` | `Rng` interface; `CsprngRng` (crypto.randomBytes) + `SeededRng` (deterministic, tests) |
| `src/planner.ts` | split 3–5 parts, random non-round sizes, delay 1–72h, exact total by construction |
| `src/policy.ts` | kill switch / daily cap / payee allowlist — enforced BEFORE planner |
| `src/shims.ts` | `shimIndexerResponse` + `shimFetch` + `verifiedMainnetTeePolicy` (copied from poc/run-poc.ts) |
| `src/client.ts` | `createZolanaClient` wiring BOTH shims (single source) |
| `src/sync.ts` | `syncPersistedWallet` + `walletSnapshotCipher` (AES-256-GCM, state/ gitignored) |
| `src/version-probe.ts` | fetch pinned TEE policy URL + 1× getShieldedTransactionsByTags shape check; mismatch → auto kill |
| `src/execute.ts` | `--execute` path: probe → sync → plan → enforce → send per part (wired, not run this session) |
| `src/index.ts` | CLI; dry-run path imports NO zolana (offline-safe); --execute lazy-imports execute.ts |

## Run

```bash
npx tsc --noEmit --strict        # proof #1: 0 errors
npx tsc --outDir dist            # build
node dist/index.js --dry-run --seed chaff-determinism --amount 25000000   # proof #2: schedule
node --test dist/test/planner.test.js                                     # proof #3: determinism
node dist/index.js --dry-run --config config/policy.kill.json          # proof #4: refuses, exit 2
```

## Honest scope (UNVERIFIED, not claimed)

- `--execute` send path is **wired but not executed** this session ("Eksekusi tx nyata TIDAK diperlukan").
  It needs `.env` (`CHAFF_OWNER_KEY`, `HELIUS_API_KEY`) and mainnet private balance.
- `walletSnapshotCipher` persists an encrypted **snapshot log** (shielded address, slot, balance).
  Full note-tree state is re-synced from the indexer on startup — the zolana `Wallet` API does not
  expose a full state serialize/restore, so the cipher is a cache, not a hot restore.
- Version probe's indexer call inspects response **shape** (`data` vs `transactions`); it does not
  verify cryptographic content beyond the TEE policy measurement pin.
- Out of scope (per task): UI, Docker, e2e browser, SPL/Token-2022, local prover (still TEE via gateway).

## Proof #5 — blueprint audit dimension

The `daemon` dimension in `chaff/blueprint.json` encodes proofs #1–#4 plus an honesty grep as
machine-checked audit checks, runnable via the mainnet audit tool:

```bash
python3 mainnet_tool/mainnet.py check chaff/blueprint.json --only daemon --summary
# daemon | WORKS | 7/0/0   RESULT: PASS
```

Seven checks, all `WORKS`: `daemon/code` (7 source modules), `daemon/deps` (zolana installed),
`daemon/types-strict` (#1), `daemon/dry-run-schedules` (#2), `daemon/planner-determinism` (#3),
`daemon/policy-kill-refuses` (#4, exit 2), `daemon/no-real-exec-claimed` (README admits the send
path is wired but not executed). No `--execute` run is claimed or audited.
