# Helius Deep Dive — struktur, produk, open-source, API
Di-scan 21 Nov 2026 via tools/scan-helius.py. Sumber mentah di folder ini.

## 1. HELIUS = 2 bisnis

A. Infra-as-a-service (revenue core)
   - RPC + Gatekeeper edge (sub-ms), archival methods
   - LaserStream gRPC (48h replay, multi-region)
   - Sender tx landing (50 TPS, staked bandwidth dari validator #1)
   - Webhooks/WSS, DAS API, preprocessed tx, preconfs, shreds
   - Pricing: Free 1M cr / Dev $49 10M / Biz $499 100M / Pro $999 200M
     + dedicated nodes $2,900+, Shreds $800-1K/IP, +$100/100RPS (Pro)
   - Juga validator #1 Solana (staking biz)

B. Solana Privacy Rings (protocol, open source) — launch mainnet 10 Nov 2026
   - Repo induk: helius-labs/zolana (SPP programs, CLI, photon, prover, ops)
   - Default Ring: confidential (asset+amount encrypted, addresses PUBLIC)
     permissionless, self-custodial, no auditor
   - Custom Rings: program Solana kamu sendiri sbg ring_auth PDA.
     Bisa anonymous (sender+recipient hidden via relayer), policy rules,
     auditor visibility, roles: admin/policy authority/pauser/co-signer/
     auditor/members/curator/delegate. Rails: owner / anonymous / delegate.
     Repo: helius-labs/custom-privacy-rings (spec lengkap)

## 2. STACK TEKNIS Zolana

- On-chain: shielded-pool program `ring1GaLCuJnkUMVkX2JeZLTTX17wKsV4fZmPVzXANW`
- UTXO model (bukan account) — notes dalam Merkle trees + nullifiers
- ZK: Groth16 SNARK, gnark 0.16.3 (Go) atau Xark (Rust) utk custom circuits
- Trusted setup: ceremony 41 circuits, FINAL 2 Nov 2026, 15 kontribusi/sirkuit
  keys publik: github.com/helius-labs/spr-ceremony
- Prover: server-side GPU (Helius) ATAU lokal:
  * Browser: @heliuslabs/spr-web-prover (WASM threads + WebGPU, ~0.06-0.43s warm)
  * Mobile: spr_mobile Flutter, on-device prover "zopro" (GPU)
  * Node 24+: spr-web-prover/node
- Indexer: Photon (indexer ZK asli) + ring-indexer utk custom rings
  self-hostable: `cargo install photon-indexer`

## 3. SDK & API (jalur integrasi)

TS client:  @heliuslabs/spr@^0.9.0-alpha (+ @solana/kit)
Rust:       zolana-client / -interface / -program / -keypair / -transaction
CLI:        zolana (dev+operator), photon-indexer
Examples:   helius-labs/privacy-ring-examples (swap, timelock escrow — UNAUDITED, test keys)

Privacy indexer API (JSON-RPC, BETA):
  devnet:  https://devnet.helius-rpc.com/v1/spr/{method}?api-key=KEY
  mainnet: https://mainnet.helius-rpc.com/v1/spr/{method}?api-key=KEY
  local:   http://127.0.0.1:8784/{method}
  8 methods: getEncryptedUtxosByTags, getShieldedTransactionsByTags/Signature/
             Nullifiers, getMerkleProofs, getNonInclusionProofs,
             getNullifierQueueElements, getUserRecords
  → return ENCRYPTED payloads; wallet decrypt lokal (viewing key)
  Auth = Helius API key (credit-based, per plan)

## 4. INTEGRATION PATTERNS (dari docs)

- Embedded Private Wallet — untuk app tanpa key management sendiri
- Private Wallet integration — wallet provider dgn key mgmt sendiri
  (Privacy Interface: signing + encrypt/decrypt, STATELESS, cache lokal)
- Private On/Off-ramp — CEX/fiat processor → direct private balance
  LIVE PROOF: Crossmint onramp — field `delivery: "private"` → USDC kartu
  langsung ke encrypted balance (announced Breakpoint London)
- Custom Ring — enterprise compliance (auditor, policy lists, freeze)

## 5. ECOSYSTEM / X SIGNALS

- Launch tweet @Helius 10 Nov: ~499K views, "encryption at the speed of Solana"
- @HeliusPrivacy akun khusus (4.4K foll, dibuat Mei 2026 — direncanakan lama)
- Integrasi live pertama: Decrypt Money account (confidential transfers)
- Crossmint fiat→private onramp (field delivery:"private")
- Thesis CEO mert: "money should be private like messages"; positioning
  Solana = "default finance requires privacy", ZK matured via Zcash learnings
- Roadmap publik: Custom Rings (institusi dgn auditor), private swaps,
  lending, yield — "foundation", belum semua live

## 6. TRUST/ISK — yang harus diterima

- Prover enclave melihat AMOUNTS (bukan identity) saat build proof
- Program upgradeable; 2-of-5 multisig bisa pause (dari Rings.run disclosure)
- Photon indexer + prover = dependency tersentral (bisa self-host photon;
  prover lokal ada di web/mobile SDK — mitigasi ada)
- Confidential ≠ anonymous: sender+recipient PUBLIC di default ring
- Timing/amount-matching di deposit+withdraw tetap bocorkan pola
- SDK masih alpha (0.9.x); contoh program unaudited dgn insecure test keys

## 7. FIT UNTUK PROJECT KITA (build original)

Yang realistis di-build tanpa nulis ZK circuit sendiri:
- App layer pakai @heliuslabs/spr: private wallet, deposit/transfer/withdraw
- Private payments/treasury/tips dalam ecosystem token
- Private OTC/escrow via example pattern (perlu audit sendiri utk production)

Yang heavy: custom ZK program (swap/lending/escrow logic sendiri) =
circuit + trusted setup + audit. Custom Ring = enterprise path via Helius.

Biaya minimum: free API key buat devnet test; production butuh plan
(privacy methods dihitung credits — tabel pricing detail perlu dicek
di dashboard saat mau deploy mainnet).

## 8. ARSITEKTUR DALAM (dari spec — deep layer)

Komponen: SPP + ZK Swap Program + Ring Programs (1..N) + Photon + Ring RPC
+ Prover + Relayer(optional) + Forester(nullifier queue) + Merge Service + Registry

PRIMITIVE PALING PENTING untuk build original:
  "third-party programs run custom private logic in a separate ZKP over
   user-owned UTXOs that hold arbitrary `utxo_data`, authorized by the
   owner's signature"

= Solusinya: program KAMU verify proof atas aturan KAMU (escrow, vesting,
  swap logic), lalu delegasikan confidential transfer ke SPP/ring via CPI.
  Pola ini ada di example: swap/escrow program (gnark Go + xark Rust).

UX infra roles yang bisa di-operate orang lain (ecosystem gaps):
  - Relayer: bayar gas atas nama user (anon submit)
  - Merge service: consolidate UTXO fragmentasi tanpa signature per-merge
  - Registry: map solana-addr → shielded-addr (pay by address saja)
  - Forester: process nullifier queue (protocol ops)

## 9. COMPETITIVE MAP (Solana privacy, per Nov 2026)

| Solusi | Hides | Trust model | Status |
|---|---|---|---|
| Token-2022 CT | amounts only | native (auditor key) | live; pernah bug soundness mid-2025 |
| Privacy Cash | sender↔receiver | ZK + relayer | $400M+ volume, mixer-style |
| Umbra (Arcium) | sender↔receiver | MPC committee | viewing-key hierarchy |
| Arcium | arbitrary compute | MPC honest-majority | general private compute |
| HELIUS SPP | amounts (+ addresses di custom ring) | ZK + enclave prover + 2-of-5 pause | programmable, custom rings, open source |

Differentiator Helius: satu-satunya dgn *programmable* private escrows +
compliance rails built-in + infra giant di belakang. Paling selaras dgn
post-Tornado design: "privacy yang bisa selectively disclosed".

## 10. GAPS (belum ada yang build — opportunity)

- Private payroll/vesting/multisig (escrow pattern exists tapi belum jadi produk)
- Agentic commerce — LISTED resmi di use cases Helius ("agents transact
  privately"), belum ada yang bangun → connect ke agent ecosystem kita
- Consumer wallet — cuma example; belum ada wallet user-facing
- Analytics/dashboard ring (explorer privat ada: photon-explorer)
- Relayer-as-a-service, merge-service-as-service

## 11. BUILD PATHS untuk project original

PATH A — App layer (cepat, no ZK circuit):
  @heliuslabs/spr → private wallet + deposit/transfer/withdraw.
  Effort: hari-minggu. Cocok: private payments, treasury opsec, tips.

PATH B — Custom ZK program (moat nyata):
  tulis circuit aturan sendiri (vesting, escrow milestone, OTC deal),
  settle via SPP. Effort: minggu-bulan + trusted setup + audit.
  Cocok: produk dengan logic privat unik = differentiator defensible.

PATH C — Custom Ring (enterprise, paling berat):
  ring program sendiri dgn policy/auditor — untuk regulated use case.
  Perlu kerja sama langsung dgn Helius kemungkinan besar.

REKOMENDASI: A dulu (validasi + UX), B saat ada traction. C cuma kalau
target institusi. Ide terkuat = agentic private payments (kosong + align
dengan agent work kita + resmi di-list Helius).

## 12. SECURITY POSTURE (verified, dari repo+security.md)

Audits selesai: Certora (Okt 2026) + zkSecurity (Agu 2026) — SPP + circuits.
OtterSec: awaiting report. Custom Rings audit: expected Dec 2026.
Trusted setup ceremony (2 Nov): kontributor dari Blueshift, Solana
Foundation, Certora, OtterSec, zkSecurity, dan Zcash — 15 kontribusi/sirkuit.
PDFs di deep/*.pdf.

zkSecurity findings (dari PDF index — severity detail perlu baca PDF):
- gnark-fake-glv-underconstrained (circuit soundness — paling serius)
- spend-linkability, faerie-gold, anonymous-ring-recipient-count-leak
- bloom-filter-cycle/size, domain-separation-signature-algo
- merge-transact-output-tree-unbound, distinguishable-output-dummy-digest
Catatan: findings ini = audit bekerja, mayoritas privacy-leak edge cases
bukan loss-of-funds. Verify resolved di release notes kalau production.

On-chain verified: program ring1GaLCuJnkUMVkX2JeZLTTX17wKsV4fZmPVzXANW
executable=true, BPFLoaderUpgradeable → UPGRADEABLE confirmed.

## 13. ADOPSION METRIK (real numbers, Nov 21)

npm: helius-sdk 3.5.0 = 28,623 weekly DL (mature)
     @heliuslabs/spr 0.9.0-alpha = 1,675 weekly (early)
     spr-web-prover 0.7.0-alpha = 133 weekly (sangat early)
crates: photon-indexer 0.50.0 = 72,825 DL (mature ZK indexer)
        zolana-client 0.10.0 = 650 DL (early)
Kesimpulan: privacy SDK usage masih <6% dari helius-sdk — early mover
window TERBUKA. First-mover advantage real untuk app layer.

## 14. DEEP CRYPTO DETAIL (spec)

- Owner tagging: pubkey prefix di encrypted UTXO → sync cepat (trade-off:
  indexer tahu owner pubkey, bukan amount — ini kenapa confidential≠anon)
- Merge service: consolidate fragmentasi UTXO tanpa per-merge signature
- Zero-key notes (nullifier_secret=0): sender bisa hitung nullifier —
  edge case spend-linkability yang diaudit zkSec
- Registry: solana-addr → shielded-addr map on-chain (pay by address)
- Tree fees: per-tree fee schedule (set_tree_fees) — biaya operasi
  protocol-level, bukan per-app
- Deposit/withdraw = PUBLIC leak points; transfer in-ring = confidential;
  fiat on/off-ramp = yang paling privat (provider sees, chain tidak)

## 15. X SIGNALS (dari scan)

@HeliusPrivacy (4.4K) — dedicated privacy account, dibuat Mei 2026
Crossmint fiat→private onramp LIVE (field delivery:"private")
Decrypt Money = integrasi pertama real
mert thesis: privacy = precondition for default finance; positioning
Solana vs Zcash-style (compliant privacy, not mixer)

## 16. CORRECTIONS (22 Nov) — supersedes earlier sections where they conflict

- WRONG in sections 11/13: "agentic private payments: nobody has built it".
  Doei (doei.io, x402 + Privacy Rings agent wallet) and musebook "Lana"
  (rings.musebook.trade) exist. Live integrations per Helius blog/press:
  Decrypt, Ore, Aurora Intents, XMR20 wallet, Crossmint onramp. Announced as
  in progress (TokenPost): Backpack, DFlow, Jupiter, Squads. Compliance
  screening: Chainalysis, Elliptic. Helius also ships an embedded wallet (WaaS).
- WRONG in section 12: "zkSecurity findings mostly privacy edge cases".
  Read from the report (commit d052a2e, Aug): 2 HIGH — #00 unauthorized
  spending of P-256-owned UTXOs (gnark fake-GLV soundness bug, needs the
  private witness to exploit), #01 public private_tx_hash leaks the spent
  UTXO (breaks spend unlinkability). 2 MEDIUM, 3 LOW, 2 INFO. The report
  records a client fix only for #05. Fix status of #00/#01: UNVERIFIED.
  Out of scope: user registry program, specific rings, wallets.
- Certora (Sep 7 - Oct 13, commits 0125d8a -> bbdecee), report marked DRAFT:
  18 findings = 1 High, 3 Medium, 6 Low, 8 Info; 11 fixed, 7 acknowledged
  (L-02, L-04, L-05, I-01, I-03, I-05, I-07). No formal verification done.
  M-03 fix covers the default ring only; custom-ring merges remain unverified.
  Out of scope: SDKs, user registry, indexer, custom ring programs.
- STILL UNVERIFIED: program upgrade authority (the "2-of-5 multisig" figure
  comes from Rings.run's disclosure, not from chain data).
- The npm "<6% of helius-sdk" comparison is not an adoption measure; drop it.
