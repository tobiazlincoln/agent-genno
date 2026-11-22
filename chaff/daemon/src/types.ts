export interface PlannedEvent {
  index: number;
  amountLamports: bigint;
  delayHours: number;
}

export interface SplitResult {
  totalLamports: bigint;
  parts: PlannedEvent[];
}

export interface PolicyConfig {
  killSwitch: boolean;
  dailyCapLamports: string;
  payeeAllowlist: string[];
}

export interface PolicyDecision {
  ok: boolean;
  reason?: string;
}

export interface WalletSnapshot {
  shieldedAddress: string;
  network: string;
  lastSyncedSlot: string;
  solBalanceLamports: string;
  syncedAt: string;
}

export interface ProbeResult {
  shimStillNeeded: boolean;
  teeOk: boolean;
  kill: boolean;
  reason?: string;
}
