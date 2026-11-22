import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import {
  syncPersistedWallet,
  walletSnapshotCipher,
  type SyncPersistedWalletResult,
  type Wallet,
  type WalletStateCipher,
  type WalletStateStore,
} from "@heliuslabs/zolana";
import type { ShieldedKeypair } from "@heliuslabs/zolana";
import type { OwnerKeys, ZolanaClient } from "./client.js";

// Encrypted persisted state lives under state/ (gitignored). The snapshot holds the
// wallet's owned-output cursors; sealing it with walletSnapshotCipher binds the
// ciphertext to the owner's viewing key so a modified store cannot advance owned
// history undetected. Writes are atomic via a tmp file.
export function fileStateStore(stateDir: string): WalletStateStore {
  const file = join(stateDir, "wallet.snapshot");
  return {
    async load(): Promise<string | undefined> {
      try {
        return readFileSync(file, "utf8");
      } catch {
        return undefined;
      }
    },
    async save(snapshot: string): Promise<void> {
      if (!existsSync(stateDir)) mkdirSync(stateDir, { recursive: true });
      const tmp = `${file}.tmp`;
      writeFileSync(tmp, snapshot, { encoding: "utf8" });
      writeFileSync(file, snapshot, { encoding: "utf8" });
      writeFileSync(tmp, "", { encoding: "utf8" });
    },
  };
}

export function daemonCipher(keypair: ShieldedKeypair): WalletStateCipher {
  return walletSnapshotCipher(keypair);
}

export interface SyncDaemonArgs {
  readonly client: ZolanaClient;
  readonly wallet: Wallet;
  readonly keys: OwnerKeys;
  readonly keypair: ShieldedKeypair;
  readonly stateDir: string;
  readonly requireSlot?: bigint;
}

// Sync loop primitive (TECH-DESIGN §1): load any encrypted persisted snapshot, advance
// owned history from the indexer up to `requireSlot` (or latest), seal the new
// snapshot back to state/. Callers retry on transient indexer errors (see execute).
export async function syncDaemonWallet(args: SyncDaemonArgs): Promise<SyncPersistedWalletResult> {
  const store = fileStateStore(args.stateDir);
  const cipher = daemonCipher(args.keypair);
  return syncPersistedWallet({
    client: args.client,
    wallet: args.wallet,
    keys: args.keys,
    ...(args.requireSlot !== undefined ? { config: { requireSlot: args.requireSlot } } : {}),
    store,
    cipher,
  });
}
