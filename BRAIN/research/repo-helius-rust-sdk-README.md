# Helius SDK
An asynchronous Helius Rust SDK for building the future of Solana

## Documentation
The latest documentation can be found [here on docs.rs](https://docs.rs/helius/latest/helius/)

## Changelog
See [CHANGELOG.md](https://github.com/helius-labs/helius-rust-sdk/blob/dev/CHANGELOG.md) for the full release history.

## Contributions
Interested in contributing to the Helius Rust SDK? Read the following [contributions guide](https://github.com/helius-labs/helius-rust-sdk/blob/dev/CONTRIBUTIONS.md) before opening up a pull request!

## Installation
To start using the Helius Rust SDK in your project, add it as a dependency via `cargo`. Open your project's `Cargo.toml` and add the following line under `[dependencies]`:
```toml
helius = "x.y.z"
```
where `x.y.z` is your desired version. Alternatively, use `cargo add helius` to add the dependency directly via the command line. This will automatically find the latest version compatible with your project and add it to your `Cargo.toml`.

Remember to run `cargo update` regularly to fetch the latest version of the SDK.

### TLS Options
The Helius Rust SDK uses the native TLS implementation by default via:
```toml
[dependencies]
helius = "x.y.z"
```

However, the SDK also supports `rustls`. Add the following to your `Cargo.toml` to use `rustls` instead of the native TLS implementation:
```toml
[dependencies]
helius = { version = "x.y.z", default-features = false, features = ["rustls"] }
```

Using `rustls` may be preferred in environments where OpenSSL is not available or when a pure Rust TLS implementation is desired. However, it may not support all the same features as the native TLS implementation

## Usage
### Quick Start
The SDK provides a [`Helius`](https://github.com/helius-labs/helius-rust-sdk/blob/dev/src/client.rs) instance that can be configured with an API key and a given Solana cluster. Developers can generate a new API key on the [Helius Developer Dashboard](https://dev.helius.xyz/dashboard/app). This instance acts as the main entry point for interacting with the SDK by providing methods to access different Solana and RPC client functionalities.

There are three simple constructors and a builder for advanced configuration:

| Constructor | Use Case |
|---|---|
| `Helius::new(api_key, cluster)` | Basic RPC operations with Helius endpoints |
| `Helius::new_async(api_key, cluster)` | Full-featured: async Solana client + WebSocket + confirmed commitment |
| `Helius::new_with_url(url)` | Custom RPC endpoint (no API key required) |
| `HeliusBuilder::new()` | Advanced configuration (custom timeouts, TLS, etc.) |

### `Helius::new()` — Basic Client
The simplest way to get started. Creates a client for standard Helius RPC operations. This constructor is **synchronous**:
```rust
use helius::Helius;
use helius::error::Result;
use helius::types::{Cluster, GetAssetRequest, GetAssetResponseForAsset};

#[tokio::main]
async fn main() -> Result<()> {
    let helius = Helius::new("YOUR_API_KEY", Cluster::MainnetBeta)?;

    let request = GetAssetRequest {
        id: "F9Lw3ki3hJ7PF9HQXsBzoY8GyE6sPoEZZdXJBsTTD2rk".to_string(),
        display_options: None,
    };

    let response: Result<Option<GetAssetResponseForAsset>> = helius.rpc().get_asset(request).await;

    match response {
        Ok(Some(asset)) => println!("Asset: {:?}", asset),
        Ok(None) => println!("No asset found."),
        Err(e) => println!("Error retrieving asset: {:?}", e),
    }

    Ok(())
}
```

### `Helius::new_async()` — Full-Featured Client
The recommended constructor for production applications. Includes async Solana RPC, WebSocket streaming, and confirmed commitment level:
```rust
use helius::Helius;
use helius::types::Cluster;

#[tokio::main]
async fn main() {
    let helius = Helius::new_async("YOUR_API_KEY", Cluster::MainnetBeta)
        .await
        .expect("Failed to create client");

    // Async Solana RPC
    let async_client = helius.async_connection().expect("Async client available");

    // Enhanced WebSocket streaming
    let ws = helius.ws().expect("WebSocket available");
}
```

### `Helius::new_with_url()` — Custom RPC Endpoint
Use your own RPC node, a third-party provider, or localhost for development. No API key required. This constructor is **synchronous**:
```rust
use helius::Helius;

fn main() {
    // Custom RPC provider
    let helius = Helius::new_with_url("https://my-rpc-provider.com/")
        .expect("Failed to create client");

    // Local development
    let local = Helius::new_with_url("http://localhost:8899")
        .expect("Failed to create client");
}
```

### `HeliusBuilder` — Advanced Configuration
For fine-grained control over the client configuration, use the builder pattern:
```rust
use helius::HeliusBuilder;
use helius::types::Cluster;
use solana_commitment_config::CommitmentConfig;
use std::time::Duration;

#[tokio::main]
async fn main() {
    // Custom RPC with API key and specific commitment
    let helius = HeliusBuilder::new()
        .with_api_key("YOUR_API_KEY").unwrap()
        .with_cluster(Cluster::MainnetBeta)
        .with_async_solana()
        .with_commitment(CommitmentConfig::confirmed())
        .build()
        .await
        .expect("Failed to build client");

    // Custom URL with separate API and RPC endpoints
    let helius = HeliusBuilder::new()
        .with_custom_url("https://rpc.example.com/").unwrap()
        .with_custom_api_url("https://api.example.com/").unwrap()
        .with_api_key("optional-key").unwrap()
        .build()
        .await
        .expect("Failed to build client");

    // Custom HTTP client with timeouts
    let http_client = reqwest::Client::builder()
        .timeout(Duration::from_secs(30))
        .build()
        .unwrap();

    let helius = HeliusBuilder::new()
        .with_api_key("YOUR_API_KEY").unwrap()
        .with_cluster(Cluster::MainnetBeta)
        .with_http_client(http_client)
        .with_websocket(Some(5), Some(15)) // custom ping/pong timeouts
        .build()
        .await
        .expect("Failed to build client");

    // Send RPC rebates to a wallet (adds rebate-address=<wallet> to the RPC URL).
    // The address is validated, so replace the placeholder with your base58 wallet address first
    let helius = HeliusBuilder::new()
        .with_api_key("YOUR_API_KEY").unwrap()
        .with_cluster(Cluster::MainnetBeta)
        .with_rebate_address("YOUR_WALLET_ADDRESS").unwrap()
        .build()
        .await
        .expect("Failed to build client");
}
```

### `HeliusFactory`
The SDK also comes equipped with `HeliusFactory`, a factory for creating instances of `Helius`. This factory allows for a centralized configuration and creation of `Helius` clients so work can be done across multiple clusters at the same time. Using a factory simplifies client code and enhances maintainability by ensuring that all `Helius` clients are configured consistently. It has the following functionality:
- A [`new` method](https://github.com/helius-labs/helius-rust-sdk/blob/a79a751e1a064125010bdb359068a366d635d005/src/factory.rs#L21-L36) used to create a new `HeliusFactory` capable of producing `Helius` clients. Note this method does not create a `reqwest` client
- A [`with_client` method](https://github.com/helius-labs/helius-rust-sdk/blob/a79a751e1a064125010bdb359068a366d635d005/src/factory.rs#L38-L53) used to provide a given `HeliusFactory` created with the `new` method its own `reqwest` client
- A [`create` method](https://github.com/helius-labs/helius-rust-sdk/blob/a79a751e1a064125010bdb359068a366d635d005/src/factory.rs#L55-L94) used to create multiple `Helius` clients in a thread-safe manner

### Embedded Solana Client
The `Helius` client has an embedded [Solana client](https://docs.rs/solana-client/latest/solana_client/rpc_client/struct.RpcClient.html) that can be accessed via `helius.connection().request_name()` where `request_name()` is a given [RPC method](https://docs.rs/solana-client/latest/solana_client/rpc_client/struct.RpcClient.html#implementations). A full list of all Solana RPC HTTP methods can be found [here](https://solana.com/docs/rpc/http).

For asynchronous operations, use `Helius::new_async()` or `HeliusBuilder` with `.with_async_solana()`. The async client can be accessed via `helius.async_connection()?.some_async_method().await?` where `some_async_method()` is a given async RPC method.

### Enhanced WebSockets
Use `Helius::new_async()` or `HeliusBuilder` with `.with_websocket(None, None)` to create a client with WebSocket support. This enables our [Enhanced WebSocket methods](https://www.helius.dev/docs/enhanced-websockets) [`transactionSubscribe`](https://www.helius.dev/docs/enhanced-websockets/transaction-subscribe) and [`accountSubscribe`](https://www.helius.dev/docs/enhanced-websockets/account-subscribe)

### Pre Confirmations (`preconfSubscribe`)
Pre Confirmations are Helius's lowest-latency transaction stream: scheduled transactions are delivered over WebSocket **before** they are shredded. A pre-confirmation is an **early signal, not a guarantee** — a streamed transaction may still fail to land. Coverage is **not continuous**: it scales with the share of stake forwarding scheduled transactions to Helius, so expect gaps. Pricing is credit-based (10 credits per notification message), the same model as other Helius WebSocket subscriptions.

Served from the Gatekeeper endpoint (`wss://beta.helius-rpc.com`). Despite the `beta` host name this is not a beta product — it is where Pre Confirmations launch during the Gatekeeper migration.

Use the standalone [`PreconfClient`](src/preconf.rs):

```rust
use futures_util::StreamExt;
use helius::preconf::PreconfClient;

let (client, mut stream) = PreconfClient::connect_with_api_key("your_api_key").await?;
while let Some(event) = stream.next().await {
    // event: { version, slot, transaction_index, status, transaction, transaction_bytes }
    println!("v{} slot={} index={} status={:?}", event.version, event.slot, event.transaction_index, event.status);
}
client.shutdown().await?;
```

`preconfSubscribe` takes no filter parameters — it streams **all** scheduled transactions. Notifications are **binary** frames (the subscribe ack is a JSON text frame); the layout is little-endian `version:u8 | slot:u64_le | transaction_index:u64_le | status:u8 | transaction wire bytes`, where the transaction is legacy, v0, or v1 and is decoded with `wincode` (`bincode` cannot read v1). The leading `version` byte is checked first (currently `1`); unknown versions are dropped. `status` is exposed as the `PreconfStatus` enum (`Failed = 0`, `Success = 1`, `Unknown = 2`). Each notification exposes the decoded `VersionedTransaction` plus the raw `transaction_bytes`. See [`examples/websockets/preconf_subscribe.rs`](examples/websockets/preconf_subscribe.rs).

### Parsed Streams
[Parsed Streams](https://www.helius.dev/docs/parsed-streams) pushes decoded transactions in real time, filtered on the server by program, instruction name, account, or account role. It is the streaming counterpart to Parsed Events and the successor to enhanced transaction webhooks; notifications use the same transfer, summary, and decoded-instruction types as Parsed Events. Available on all plans at 1 credit per delivered event. Create a client with `helius.parsed_streams()?` (requires an API key; mainnet only) or the standalone `ParsedStreamsClient::new(api_key)`, with types in `helius::types::parsed_streams`.

```rust
use futures_util::StreamExt;
use helius::types::parsed_streams::ParsedTransactionFilter;

let streams = helius.parsed_streams()?;
let mut subscription = streams
    .parsed_transaction_subscribe(
        ParsedTransactionFilter {
            programs: Some(vec!["JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4".to_string()]),
            ..Default::default()
        },
        None,
    )
    .await?;

while let Some(notification) = subscription.next().await {
    let value = notification?.value;
    for &i in value.matched_indexes.as_deref().unwrap_or_default() {
        let instruction = &value.instructions[i];
        println!("{} {:?}", value.transaction.signature, instruction.instruction_name);
    }
}
```

- `parsed_transaction_subscribe(filter, options)` - Subscribes with a filter (`programs`, `instruction_names`, `accounts.include`, `accounts.roles`, `include_failed`, `include_cpi`). `options.details` is `Full` (the default: the whole transaction plus `matched_indexes`) or `Matched` (only the matching instructions). Returns a `Stream` of `Result<ParsedTransactionNotification>`; dropping it unsubscribes
- `raw_transaction_subscribe(filter)` - Same, with `raw` details: matching instructions as base58 data only
- `parsed_transaction_unsubscribe(subscription_id)` - Unsubscribes by current id
- `close()` - Closes the connection and ends every subscription

Delivery is **at most once**: the server doesn't replay what confirmed while a connection was down, and it closes connections routinely (10 minutes without a match, deploys, network edge recycling). The client reconnects with backoff and resubscribes every filter on its own; `ParsedStreamsOptions::with_on_reconnect` reports the close code and the last slot delivered so you can backfill the gap from RPC. A subscription ends with an error rather than silently dropping data when it can't be kept alive: a policy close from the server (code 1008, sent when the client falls more than 2048 notifications behind or the API key or plan changes; the error includes the server's reason), 10,000 unread notifications in the client, a filter rejected on resubscribe, or reconnect attempts exhausted. Client messages are paced to the server's 10-per-second limit, and each connection holds up to 25 subscriptions. The client pings every 30 seconds, since the server drops a connection the client hasn't written to for 5 minutes, and treats 60 seconds without a frame (pongs included) as a dead connection. See [`examples/parsed_streams/subscribe.rs`](examples/parsed_streams/subscribe.rs).

### Examples
More examples of how to use the SDK can be found in the [`examples`](https://github.com/helius-labs/helius-rust-sdk/tree/dev/examples) directory.

## Error Handling
### Common Error Codes
You may encounter several error codes when working with the Helius Rust SDK. Below is a table detailing some of the common error codes along with additional information to aid with troubleshooting:

| Error Code | Error Message             | More Information                                                                           |
|------------|---------------------------|---------------------------------------------------------------------------------------------|
| 401        | Unauthorized              | This occurs when an invalid API key is provided or access is restricted |
| 429        | Too Many Requests         | This indicates that the user has exceeded the request limit in a given timeframe or is out of credits |
| 5XX        | Internal Server Error     | This is a generic error message for server-side issues. Please contact Helius support for assistance |

If you encounter any of these errors:
- Refer to [`errors.rs`](https://github.com/helius-labs/helius-rust-sdk/blob/dev/src/error.rs) for a list of all possible errors returned by the `Helius` client
- Refer to the [Helius documentation](https://www.helius.dev/docs/) for further guidance
- Reach out to the Helius support team for more detailed assistance

### Result Type Alias
The SDK also has [a handy type alias for `Result`](https://github.com/helius-labs/helius-rust-sdk/blob/c24bdf3179998895e73fe455d38bd7faa2c50df5/src/error.rs#L147-L148) where `Result<(some type), HeliusError>` and be simplified to `Result<(some type)>`

## Methods
Our SDK is designed to provide a seamless developer experience when building on Solana. We've separated the core functionality into various segments:

### DAS API
- [`get_asset`](https://www.helius.dev/docs/api-reference/das/getasset) - Gets an asset by its ID
- [`get_asset_batch`](https://www.helius.dev/docs/api-reference/das/getassetbatch) - Gets multiple assets by their ID
- [`get_asset_proof`](https://www.helius.dev/docs/api-reference/das/getassetproof) - Gets a merkle proof for a compressed asset by its ID
- [`get_asset_proof_batch`](https://www.helius.dev/docs/api-reference/das/getassetproofbatch) - Gets multiple asset proofs by their IDs
- [`get_assets_by_owner`](https://www.helius.dev/docs/api-reference/das/getassetsbyowner) - Gets a list of assets owned by a given address
- [`get_assets_by_authority`](https://www.helius.dev/docs/api-reference/das/getassetsbyauthority) - Gets a list of assets of a given authority
- [`get_assets_by_creator`](https://www.helius.dev/docs/api-reference/das/getassetsbycreator) - Gets a list of assets of a given creator
- [`get_assets_by_group`](https://www.helius.dev/docs/api-reference/das/getassetsbygroup) - Gets a list of assets by a group key and value
- [`search_assets`](https://www.helius.dev/docs/api-reference/das/searchassets) - Gets assets based on the custom search criteria passed in
- [`get_signatures_for_asset`](https://www.helius.dev/docs/api-reference/das/getsignaturesforasset) - Gets transaction signatures for a given asset
- [`get_token_accounts`](https://www.helius.dev/docs/api-reference/das/gettokenaccounts) - Gets information about all token accounts for a specific mint or owner
- [`get_nft_edition`](https://www.helius.dev/docs/api-reference/das/getnfteditions) - Gets all the NFT editions  associated with a specific master NFT

### ZK Compression
- [`get_compressed_account`](https://www.helius.dev/docs/api-reference/zk-compression/getcompressedaccount) - Gets a compressed account by its address or hash
- [`get_compressed_account_proof`](https://www.helius.dev/docs/api-reference/zk-compression/getcompressedaccountproof) - Gets a Merkle proof for a compressed account
- [`get_compressed_accounts_by_owner`](https://www.helius.dev/docs/api-reference/zk-compression/getcompressedaccountsbyowner) - Gets all compressed accounts owned by a given address
- [`get_compressed_balance`](https://www.helius.dev/docs/api-reference/zk-compression/getcompressedbalance) - Gets the balance of a compressed account
- [`get_compressed_balance_by_owner`](https://www.helius.dev/docs/api-reference/zk-compression/getcompressedbalancebyowner) - Gets the total compressed SOL balance across all accounts owned by a given address
- [`get_compressed_mint_token_holders`](https://www.helius.dev/docs/api-reference/zk-compression/getcompressedminttokenholders) - Lists all holders of a specific compressed token mint
- [`get_compressed_token_account_balance`](https://www.helius.dev/docs/api-reference/zk-compression/getcompressedtokenaccountbalance) - Gets the token balance of a compressed token account
- [`get_compressed_token_accounts_by_delegate`](https://www.helius.dev/docs/api-reference/zk-compression/getcompressedtokenaccountsbydelegate) - Gets all compressed token accounts delegated to a specific address
- [`get_compressed_token_accounts_by_owner`](https://www.helius.dev/docs/api-reference/zk-compression/getcompressedtokenaccountsbyowner) - Gets all compressed token accounts owned by a specific address
- [`get_compressed_token_balances_by_owner`](https://www.helius.dev/docs/api-reference/zk-compression/getcompressedtokenbalancesbyowner) - Gets all token balances for compressed accounts owned by an address
- [`get_compressed_token_balances_by_owner_v2`](https://www.helius.dev/docs/api-reference/zk-compression/getcompressedtokenbalancesbyownerv2) - Enhanced version of `get_compressed_token_balances_by_owner` with additional iteration support
- [`get_compression_signatures_for_account`](https://www.helius.dev/docs/api-reference/zk-compression/getcompressionsignaturesforaccount) - Gets transaction signatures associated with a compressed account
- [`get_compression_signatures_for_owner`](https://www.helius.dev/docs/api-reference/zk-compr