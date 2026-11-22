# Helius TypeScript SDK

[![Version](https://img.shields.io/npm/v/helius-sdk)](https://www.npmjs.org/package/helius-sdk)
![Downloads](https://img.shields.io/npm/dm/helius-sdk)

The Helius TypeScript SDK provides access to Helius APIs and enhanced Solana RPC functionality, making building on Solana as easy as possible.

### Agent Account Sign Up

The SDK ships two signup helpers on `helius.auth`:

- `signup(opts)` — authenticates the wallet, detects existing projects, and returns either `kind: "already_subscribed"`, `kind: "upgrade_required"`, or `kind: "payment_required"` with a hosted-checkout link the user opens in a browser.
- `signupAndPay(opts)` — same as `signup`, plus auto-pays USDC + memo from the local keypair and polls activation. On poll timeout returns `kind: "pending"` with the `txSignature` so callers can resume later.

```ts
import { makeAuthClient } from "helius-sdk/auth/client";

const auth = makeAuthClient();
const { secretKey } = await auth.generateKeypair();

const result = await auth.signup({
  secretKey,
  plan: "agent",
  email: "you@example.com",
  firstName: "Jane",
  lastName: "Doe",
});

if (result.kind === "payment_required") {
  console.log("Pay here:", result.paymentLink.paymentUrl);
}
```

See [`examples/auth/signup.ts`](./examples/auth/signup.ts) and [`examples/auth/signupAndPay.ts`](./examples/auth/signupAndPay.ts) for full flows.

> **For AI Agents:** You can create a Helius account and generate an API key programmatically using the helius-cli. See the [agent signup guide](https://www.helius.dev/docs/api-reference/helius-cli.md) or [helius-cli agent file](https://dashboard.helius.dev/agents.md) for complete details.

## Documentation

API reference documentation is available at [helius.dev/docs](https://www.helius.dev/docs).

For detailed SDK API docs (auto-generated from source), see the [TypeDoc Reference](https://helius-labs.github.io/helius-sdk/).

See the [CHANGELOG](https://github.com/helius-labs/helius-sdk/blob/main/CHANGELOG.md) for version history and release notes.

LaserStream gRPC streaming is not part of this SDK. Use the standalone [`helius-laserstream`](https://www.npmjs.com/package/helius-laserstream) package instead.

## Contributions

Interested in contributing? Read the following [contributions guide](https://github.com/helius-labs/helius-sdk/blob/main/CONTRIBUTING.md) before opening a PR.

## Installation

Using pnpm (recommended):

```shell
pnpm add helius-sdk
```

Using npm:

```shell
npm install helius-sdk
```

Using yarn:

```shell
yarn add helius-sdk
```

## Usage

The package needs to be configured with your account's API key, which is available in the [Helius Dashboard](https://dashboard.helius.dev/).

```ts
import { createHelius } from "helius-sdk";

(async () => {
  const apiKey = ""; // From Helius dashboard
  const helius = createHelius({ apiKey });

  try {
    const assets = await helius.getAssetsByOwner({
      ownerAddress: "owner_address_goes_here",
      page: 1,
      limit: 50,
      sortBy: { sortBy: "created", sortDirection: "asc" },
    });

    console.log("Fetched assets:", assets);
  } catch (error) {
    console.error("Error:", error);
  }
})();
```

### Custom RPC transport (retries, failover)

`createHelius` accepts a `transport` hook that lets you augment or replace the default RPC transport, following [`@solana/kit`'s custom-transport pattern](https://github.com/anza-xyz/kit#custom-rpc-transports). The hook receives the SDK's fully configured transport (Helius URL with your API key, SDK headers, and request-id stamping) and returns the transport the client will use for **all** JSON-RPC calls — standard Solana RPC and DAS/Helius methods alike.

```ts
import { createHelius, type RpcTransport } from "helius-sdk";

const helius = createHelius({
  apiKey,
  transport: (defaultTransport: RpcTransport): RpcTransport => async (request) => {
    // Retry up to 3 times with exponential backoff
    let lastError: unknown;
    for (let attempt = 0; attempt < 3; attempt++) {
      try {
        return await defaultTransport(request);
      } catch (error) {
        lastError = error;
        await new Promise((r) => setTimeout(r, 2 ** attempt * 100));
      }
    }
    throw lastError;
  },
});
```

For per-method policies, read the method name off the request: `(request.payload as { method: string }).method`.

To replace the transport entirely (e.g., failover to a non-Helius endpoint), ignore the provided default: `transport: () => myCustomTransport`. See [`examples/helius/customTransport.ts`](examples/helius/customTransport.ts) for a full example.

> **Note:** The hook covers JSON-RPC traffic only. WebSocket subscriptions (`helius.ws`) and the REST sub-clients (`webhooks`, `parsedEvents`, `enhanced`, `wallet`, `admin`, `auth`) do not go through this transport.

### Using `@solana/kit` helpers

Standard Solana RPC methods on `helius` (and `helius.raw`) send automatically, so they are not a `@solana/kit` `Rpc`. To pass the client to kit helpers or other libraries that expect one, use `helius.kitRpc`, the standard kit `Rpc` on the same JSON-RPC transport:

```ts
import { fetchEncodedAccount } from "@solana/kit";

const account = await fetchEncodedAccount(helius.kitRpc, address);
const slot = await helius.kitRpc.getSlot().send();
```

Don't pass `helius` or `helius.raw` to kit helpers: the request is sent immediately, and the helper then fails when it calls `.send()`.

See [`examples/helius/kitRpc.ts`](examples/helius/kitRpc.ts) for a full example.

### Larger transactions with version 1

Agave 4.2 raises the maximum transaction size from 1,232 to 4,096 bytes ([SIMD-0296](https://github.com/solana-foundation/solana-improvement-documents/blob/main/proposals/0296-larger-transactions.md)). That size is only available in the version 1 transaction format ([SIMD-0385](https://github.com/solana-foundation/solana-improvement-documents/blob/main/proposals/0385-transaction-v1.md)). Legacy and v0 transactions are unaffected and remain the default.

Opt in by passing `version: 1`:

```typescript
const smart = await helius.tx.createSmartTransaction({
  signers: [feePayerSigner],
  instructions: [transferIx],
  version: 1,
});
```

Version 1 moves the compute-unit limit and priority fee out of `ComputeBudgetProgram` instructions and into the transaction header, so a v1 transaction is *smaller* on the wire than the v0 equivalent even before you use the extra room. The SDK handles this for you — do not pass compute-budget instructions yourself, as they are no-ops on v1 that still consume bytes and compute units.

The header also carries the loaded-accounts-data-size limit, and SIMD-0385 treats an absent field as a request for **0 bytes** — a transaction that fails account loading outright — rather than the 64 MiB default legacy and v0 enjoy. The SDK always sets it on v1 (64 MiB unless you pass `loadedAccountsDataSizeLimit` to request less, which reserves less under the v1 cost model). If you assemble v1 messages by hand, `createTxMessage` pre-sets the data-size limit to the 64 MiB maximum (override it with kit's `setTransactionMessageLoadedAccountsDataSizeLimit`); you must still set the compute-unit limit and priority fee yourself with `setTransactionMessageComputeUnitLimit` and `setTransactionMessagePriorityFeeLamports`.

Because v1 pays a **total** priority fee in lamports rather than a per-compute-unit rate, the result reports both:

```typescript
smart.priorityFee;         // microLamports per CU, the rate the SDK settled on
smart.priorityFeeLamports; // total lamports the transaction pays
```

You can budget against either. `priorityFeeCap` caps the per-CU rate; `priorityFeeLamportsCap` caps the absolute spend:

```typescript
const smart = await helius.tx.createSmartTransaction({
  signers: [feePayerSigner],
  instructions: [transferIx],
  version: 1,
  priorityFeeLamportsCap: 50_000, // Never spend more than 50k lamports on priority
});
```

#### Version 1 constraints

Version 1 **does not support address lookup tables**. Every account must be listed inline, and the SDK throws if an instruction sources an account from a lookup table. Use version 0 if you depend on them.

The format also caps a transaction at 64 instructions, 64 unique addresses, 12 signatures, and 255 accounts per instruction. At 4,096 bytes the full address list usually fits inline anyway.

The SDK checks the size limit before requesting any signature, so an oversized transaction fails locally rather than on submission.

### Migrating to `helius-sdk` 2.0.0

The Helius Node.js SDK has been rewritten from the ground up in version 2.0.0 to use [`@solana/kit` (i.e., Kit)](https://www.npmjs.com/package/@solana/kit) under the hood, replacing the dependency on `@solana/web3.js` versions higher than 1.73.2.

We've gone to great lengths to ensure that the developer experience remains largely the same, with minimal impact on existing code. The API methods and namespaces are designed to be intuitive and an improvement on previous versions, so migrating to the latest version is relatively straightforward. There are a plethora of examples found in the `examples` directory, organized by namespace, to aid in this migration.

For more detailed migration help, refer to the following [migration guide](https://github.com/helius-labs/helius-sdk/blob/main/MIGRATION.md)

For general help with Kit, please refer to [Kit's new documentation site](https://www.solanakit.com/)

## Handling errors

When the API returns a non-success status code (4xx or 5xx response), an error message will be thrown:

```ts
try {
  const assets = await helius.getAssetsByOwner({
    ownerAddress: "owner_address_goes_here",
    page: 1,
    limit: 50,
    sortBy: { sortBy: "created", sortDirection: "asc" },
  });

  console.log("Fetched assets:", assets);
} catch (error) {
  console.error("Error:", error);
}
```

### Common Error Codes

When working with the Helius SDK, you may encounter several error codes. Below is a table detailing some of the common error codes along with additional information to help you troubleshoot:

| Error Code | Error Message         | More Information                                                                                       |
| ---------- | --------------------- | ------------------------------------------------------------------------------------------------------ |
| 401        | Unauthorized          | This occurs when an invalid API key is provided or access is restricted due to RPC rules.              |
| 429        | Too Many Requests     | This indicates that the user has exceeded the request limit in a given timeframe or is out of credits. |
| 5XX        | Internal Server Error | This is a generic error message for server-side issues. Please contact Helius support for assistance.  |

If you encounter any of these errors, refer to the Helius documentation for further guidance, or reach out to the Helius support team for more detailed assistance.

## Using the Helius SDK

Our SDK is designed to give you a seamless experience when building on Solana. We've separated the core functionality into various segments. Examples for individual methods can be found in the `examples` directory, with examples organized by namespace.

[**DAS API**](https://www.helius.dev/docs/das-api)

Comprehensive and performant API for tokens, NFTs, and compressed NFTs on Solana. Available on the `helius` namespace.

- [`getAsset()`](https://www.helius.dev/docs/api-reference/das/getasset): Get an asset by its ID.
- [`getAssetBatch()`](https://www.helius.dev/docs/api-reference/das/getassetbatch): Get multiple assets by their IDs (up to 1k).
- [`getAssetProof()`](https://www.helius.dev/docs/api-reference/das/getassetproof): Get a Merkle proof for a compressed asset by its ID.
- [`getAssetProofBatch()`](https://www.helius.dev/docs/api-reference/das/getassetproofbatch): Get Merkle proofs for a set of compressed assets by their IDs.
- [`getAssetsByAuthority()`](https://www.helius.dev/docs/api-reference/das/getassetsbyauthority): Get a list of assets with a specific authority.
- [`getAssetsByCreator()`](https://www.helius.dev/docs/api-reference/das/getassetsbycreator): Get a list of assets created by an address.
- [`getAssetsByGroup()`](https://www.helius.dev/docs/api-reference/das/getassetsbygroup): Get a list of assets by a group key and value. This endpoint is very useful for getting the mint list for NFT Collections.
- [`getAssetsByOwner()`](https://www.helius.dev/docs/api-reference/das/getassetsbyowner): Get a list of assets owned by an address. This is the fastest way to get all the NFTs and fungible tokens that are owned by a wallet on Solana.
- [`getNftEditions()`](https://www.helius.dev/docs/api-reference/das/getnfteditions): Get information about all the edition NFTs for a specific master NFT.
- [`getTokenAccounts()`](https://www.helius.dev/docs/api-reference/das/gettokenaccounts): Get information about all token accounts for a specific mint or a specific owner.
- [`searchAssets()`](https://www.helius.dev/docs/api-reference/das/searchassets): Search for assets by a variety of parameters. This is very useful for token-gating.

**RPC V2 Methods**

Enhanced RPC methods, available only with Helius.

- [`getProgramAccountsV2()`](https://www.helius.dev/docs/api-reference/rpc/http/getprogramaccountsv2): Enhanced version of `getProgramAccounts` with cursor-based pagination and `changedSinceSlot` support for efficiently querying large sets of accounts owned by specific Solana programs with incremental updates.
- `getAllProgramAccounts()`: Auto-paginates through all program accounts. Use with caution on larger programs.
- [`getTokenAccountsByOwnerV2()`](https://www.helius.dev/docs/api-reference/rpc/http/gettokenaccountsbyownerv2): An enhanced version of `getTokenAccountsByOwner` with cursor-based pagination and `changedSinceSlot` support to incrementally retrieve SPL token accounts owned by a given mint.
- `getAllTokenAccountsByOwner()`: Auto-paginates all token accounts for a given owner.
- [`getTransactionsForAddress()`](https://www.helius.dev/docs/rpc/gettransactionsforaddress): Get transaction history for an address with advanced filtering by slot, time, and bidirectional sorting options. Supports both signature-only and full transaction details. Optionally include transactions from associated token accounts.
- [`getTransfersByAddress()`](https://www.helius.dev/docs/rpc/gettransfersbyaddress): Get parsed token and native SOL transfer history for an address with filters by mint, time, amount, counterparty, direction, and cursor pagination.

**Historical Accounts (Beta)**

Read accounts as they were at a past slot, or immediately after a specific transaction within that slot. Mainnet only, from slot 444959999 onward.

- `getHistoricalAccountInfo()`: Get an account at a past slot or transaction, with `lastUpdatedAt` pointing to the write that produced that state.
- `getHistoricalTokenAccountsByOwner()`: Get the SPL Token and Token-2022 accounts a wallet owned at a past slot or transaction, optionally for one mint or token program, with cursor pagination.

[**Staking**](https://www.helius.dev/docs/staking/how-to-stake-with-helius-programmatically)

The easiest way to stake with Helius programmatically. Available on the `helius.staking` namespace.

- `createStakeTransaction()`: Generate a transaction to create + delegate a new stake account to the Helius validator.
- `createUnstakeTransaction()`: Generate a transaction to deactivate a stake account.
- `createWithdrawTransaction()`: Generate a transaction to withdraw lamports from a stake account (after cooldown).
- `getStakeInstructions()`: Return only the instructions for creating and delegating a stake account.
- `getUnstakeInstruction()`: Return the instruction to deactivate a stake account.
- `getWithdrawInstruction()`: Return the instruction to withdraw lamports from a stake account.
- `getWithdrawableAmount()`: Determine how many lamports are withdrawable (with optional rent-exempt inclusion).
- `getHeliusStakeAccounts()`: Return all stake accounts delegated to the Helius validator for a given wallet.

[**Transactions**](https://docs.helius.dev/solana-rpc-nodes/sending-transactions-on-solana#sending-smart-transactions)

Simply create, send, and land transactions as fast as possible. Available on the `helius.tx` namespace.

- `getComputeUnits()`: Fetches the total compute units the transaction provided is expected to consume
- `broadcastTransaction()`: Broadcasts a fully signed transaction (object or serialized) and polls for its confirmation.
- `pollTransactionConfirmation()`: Polls a transaction to check whether it has been confirmed
- `createSmartTransaction()`: Creates a smart transaction with the provided configuration
- `sendSmartTransaction()`: Builds and sends an optimized transaction
- `sendTransaction()`: Wrapper for [`sendTransaction` RPC call](https://www.helius.dev/docs/api-reference/rpc/http/sendtransaction) that includes support for a `validatorAcls` parameter (i.e., JSON-based allow and deny lists).
- `sendTransactionWithSender()`: Ultra-low latency Solana transaction submission via [Helius Sender](https://www.helius.dev/docs/sending-transactions/sender). Routes across multiple high-speed pathways and enters a priority auction; tip more to land first. Two tiers: **Sender Max** (`swqosOnly: false`, 0.001 SOL minimum tip) and **SWQOS-only** (`swqosOnly: true`, 0.000005 SOL minimum tip).
- `sendBundleWithSender()`: Submits an ordered bundle of pre-signed transactions (max 5) atomically over Sender Max via the `sendBundle` method, then tracks landing per-signature with `getSignatureStatuses`. At least one transaction in the bundle must carry the 0.001 SOL Sender Max minimum tip.

**[MEV Protect](https://www.helius.dev/docs/sending-transactions/mev-protect)** routes transactions away from validators statistically linked to sandwich attacks. It's off by default. Turn it on for a whole client with `createHelius({ apiKey, mevProtect: true })`: every send through that client is protected, including `sendTransaction`, `sendSmartTransaction`, `broadcastTransaction`, and both Sender helpers. Or set it per call on the Sender helpers, which overrides the client setting:

```ts
await helius.tx.sendTransactionWithSender({ ...args, region: "Default", mevProtect: true });
await helius.tx.sendBundleWithSender(signedTxs, { mevProtect: true });
```

Only a small fraction of stake is excluded, so the effect on landing rate is small; for the most latency-sensitive flows, measure with and without it first.

[**Priority Fee API**](https://github.com/helius-labs/helius-sdk/blob/main/examples/EXAMPLES_OVERVIEW.md#helper-methods)

Estimate optimal priority fees for Solana transactions. Available on the `helius` namespace.

- [`getPriorityFeeEstimate()`](https://github.com/helius-labs/helius-sdk/blob/main/examples/EXAMPLES_OVERVIEW.md#getpriorityfeeestimate): Returns an estimated priority fee based on a set of predefined priority levels (percentiles).

[**Parsed Events API**](https://www.helius.dev/docs/parsed-events)

Parse transactions into decoded instructions, transfers, and summaries using Helius's IDL catalog (3,600+ programs). Mainnet only. Available on the `helius.parsedEvents` namespace.

- [`parseTransactions()`](https://www.helius.dev/docs/api-reference/parsed-events/transactions): Parses up to 100 transaction signatures. Each result carries a `parserStatus`, so a missing transaction comes back as an item-level error instead of failing the request. 10 credits per request.
- [`getTransactionHistory()`](https://www.helius.dev/docs/api-reference/parsed-events/transaction-history): Returns parsed transaction history for an address with slot and block-time bounds, paginated with `paginationToken`. Only successful transactions unless you pass `status: "any"` or `"failed"`; `tokenAccounts` adds transactions that touch only the address's token accounts. 10 credits per request.
-