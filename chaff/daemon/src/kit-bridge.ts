// Thin, loosely-typed bridge to the @solana/kit functions the daemon needs to sign
// and send transactions. The kit package ships partial .d.ts (only the `exports`
// types field resolves under NodeNext), so each symbol is fetched by name at module
// load and asserted. This keeps tsc --strict happy without depending on kit's full
// type surface; runtime behaviour is identical to chaff/poc/run-poc.ts, which
// imports the same symbols directly.
import * as SolanaKit from "@solana/kit";

const k = SolanaKit as unknown as Record<string, unknown>;

function need<T>(name: string): T {
  const found = k[name];
  if (typeof found !== "function") throw new Error(`kit-bridge: @solana/kit missing "${name}"`);
  return found as T;
}

export type SendAndConfirm = (transaction: unknown, options?: unknown) => Promise<void>;

export const createKeyPairSignerFromPrivateKeyBytes: (
  privateKeyBytes: Uint8Array,
) => Promise<unknown> = need("createKeyPairSignerFromPrivateKeyBytes");

export const signTransactionWithSigners: (
  signers: unknown[],
  transaction: unknown,
) => Promise<unknown> = need("signTransactionWithSigners");

export const getSignatureFromTransaction: (transaction: unknown) => string = need(
  "getSignatureFromTransaction",
);

export const sendAndConfirmTransactionFactory: (config: {
  rpc: unknown;
  rpcSubscriptions: unknown;
}) => SendAndConfirm = need("sendAndConfirmTransactionFactory");

// Base58 string -> bytes. kit's getBase58Encoder() returns an Encoder<string> whose
// encode() maps a base58 string to its underlying bytes (chaff/poc uses the same to
// decode CHAFF_OWNER_KEY).
export function decodeBase58(value: string): Uint8Array {
  const encoder = need<
    () => { encode: (v: string) => Uint8Array; decode: (v: Uint8Array) => string }
  >("getBase58Encoder")();
  return encoder.encode(value);
}
