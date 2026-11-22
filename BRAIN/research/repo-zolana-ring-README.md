# zolana-ring

The cargo-generate template for a custom ring on the
[Solana Privacy Program](https://github.com/helius-labs/zolana). Transfers
inside a ring are confidential and every transfer carries a proof that the
ring's auditor key can open it.

## Use

```bash
zolana-ring new my-ring    # the operator binary, built from the zolana repo
# or directly
cargo generate --git https://github.com/helius-labs/zolana-ring
```

Generation runs in two stages. The template renders the ring's configuration,
`ring.toml` with the wizard's answers and the hosted devnet service defaults,
and a second `cargo generate` pass copies the ring source, `program/`, `sdk/`
and `test/`, from [zolana](https://github.com/helius-labs/zolana)
`custom-rings` at the pinned revision. The ring owns that source, `interface`
and `client` stay zolana crates because the services parse their layouts.

## The revision pin

The `zolana_revision` placeholder default is the zolana revision the deployed
devnet stack runs, one revision pins the copied source and the crate
dependencies together, a rotation bumps it here. `zolana-ring new
--zolana-rev` overrides it for development.
