# CHAFF MEGA-PLAN — master plan & audit fitur per fitur (2026-11-22)

Referensi: `chaff-session.json` (gate), `chaff/README.md` (override), `chaff/TECH-DESIGN.md`
(desain teknis), `BRAIN/PRODUCT.md` (produk 3 layar), `BRAIN/research/*` (riset).
Status gerbang: **gate K1 FAIL → RECORDED OVERRIDE** (klaim dibatasi, re-run wajib).

## 0. Status besar

**PoC MAINNET: BERHASIL PENUH.** Register ×2 (sponsored) → deposit → private transfer →
withdraw fee-cut, semua signature mainnet nyata tercatat di `chaff/README.md` § PoC progress.
Fee-cut terbukti angka: recipient public 0.005 + 0.025 − 0.000015 fee = 0.029985 SOL eksak.
Kendala teknis terbesar (SDK alpha vs API ter-deploy) sudah dijawab dengan 2 shim terdokumentasi.

## 1. Audit fitur per fitur

| # | Fitur | Status | Bukti / Lokasi | Next |
|---|---|---|---|---|
| 1 | Register (owner + sponsored recipient) | **JALAN (mainnet)** | SIG 2mQurEKK…, 5VcfLCWj… | — |
| 2 | Deposit SOL → private balance | **JALAN (mainnet)** | SIG 4mrmeciV…, finalized slot 472286300 | SPL/Token-2022 (v1.1) |
| 3 | Private transfer | **JALAN (mainnet)** | SIG 2vKKud2t… | multi-transfer, split |
| 4 | Withdraw fee-cut (feePayer=recipient) | **JALAN (mainnet)** | SIG 3foY54er…; saldo eksak 29985000 | — |
| 5 | Helius gateway indexer/prover | **JALAN** | /v1/spr HTTP 200 semua method | monitor kredit free tier |
| 6 | Version shim (indexer + TEE policy) | **JALAN, DISKLOSUR** | `shimIndexerResponse` + `verifiedMainnetTeePolicy` di run-poc.ts | hapus saat SDK menyusul API; T1 daemon |
| 7 | Visibility meter | **BELUM** | heuristik ada: tools/rings-analyze.py match_counts | port ke `chaff/meter`, backtest |
| 8 | Policy engine (cap, payee, kill switch) | **DESAIN SELESAI** | TECH-DESIGN §7 | implement di daemon |
| 9 | Planner split/delay/merge | **DESAIN SELESAI** | TECH-DESIGN §1.3 | deterministik + CSPRNG + test |
| 10 | Version probe harian (T1) | **DESAIN SELESAI** | TECH-DESIGN §4; shim membuktikan kebutuhan | implement |
| 11 | Pre-check nullifier capacity (T3) | **DESAIN SELESAI** | TECH-DESIGN §5 | implement |
| 12 | Local prover default + TEE fallback | **PARSIAL** | TEE prover jalan; local proving belum diuji | uji `proofDataSource:"client"` |
| 13 | Backtest | **PARSIAL** | tools/rings-aggregate.py + null-on-parts.py (gate K1) | backtest meter: kandidat per event historis |
| 14 | Backend (daemon lokal) | **BELUM** | skeleton di TECH-DESIGN §1 | fase 2 |
| 15 | Frontend / UI / UX (3 layar) | **BELUM** | spesifikasi PRODUCT.md §3 | fase 3 |
| 16 | User flow | **SPESIFIKASI ADA** | PRODUCT.md §3: saldo → kirim(meter) → autopilot | validasi dgn prototype |
| 17 | Konsep narasi / manifesto | **BAHAN ADA** | NAMING.md (Rivest 1998 chaffing & winnowing), PRODUCT.md §1-7 | tulis MANIFESTO.md + landing copy |
| 18 | Workflow (event lifecycle) | **DESAIN ADA** | PRODUCT.md §4: SPLIT/DELAY/ROUTE/MERGE/POLICY | impl di planner |
| 19 | Framework pilihan | **PUTUSKAN** | rekomendasi: daemon Node TS (SDK native); web: Next.js + wagmi/viem? TIDAK — @solana/kit + React | lihat §3 |
| 20 | Docker | **BELUM** | daemon = 1 proses Node + state dir | Dockerfile + compose (validator utk e2e) |
| 21 | E2E test | **BELUM** | run-poc.ts bisa jadi seed e2e | playwright + devnet/localnet |
| 22 | Agent interface (AI) | **DESAIN SELESAI** | TECH-DESIGN §8; LLM tanpa amount | intent parser v2 |
| 23 | Keamanan key | **JALAN (PoC)** | .env gitignored + hook; keychain v1 daemon | OS-keychain integrasi |

## 2. Kebutuhan API & resource

- **Helius API key (WAJIB, ada):** RPC + indexer Photon + prover Nitro via `mainnet.helius-rpc.com/v1/spr`.
  Free tier 1M kredit/10 RPS — cukup 1 wallet PoC; daemon multi-user butuh paid.
- **RPC publik fallback:** ada tapi indexer/prover 403 tanpa key (terverifikasi).
- **Helius devnet SOL:** faucet browser-only (Cloudflare) — devnet tersimpan sebagai fallback dev.
- **GitHub:** helius-labs/zolana (SDK, alpha — churn T1), photon indexer (self-host opsi $49/mo),
  privacy-ring-examples (UNAUDITED — dilarang utk dana nyata, aturan task_2).
- **HuggingFace:** TIDAK dibutuhkan untuk v1. Kebutuhan model hanya jika layer LLM agent dilokalkan
  (Whisper/Llama on-device) — fase v2, dan tetap "LLM tidak melihat amount".

## 3. Framework & stack (keputusan)

- **Daemon/backend:** Node.js 24 + TypeScript + @heliuslabs/zolana + @solana/kit (sudah terbukti di PoC).
- **Frontend:** React + Vite, komunikasi ke daemon via localhost HTTP/WS (UI tipis, daemon pegang key).
- **Backtest/riset:** Python (numpy) — tools/rings-* sudah pola ini.
- **E2E:** Vitest (unit planner/policy) + Playwright (UI) + localnet `zolana dev` (belum ada di npm — pakai devnet keypair khusus test).
- **Docker:** multi-stage Node slim; volume state terenkripsi; TIDAK menyimpan key di image.

## 4. Roadmap (urutan, gate per fase)

- **Fase 1 — selesai:** gate riset + override + PoC mainnet (fitur 1-6).
- **Fase 2 — daemon (2-3 minggu):** sync persisten (syncPersistedWallet + cipher), policy engine,
  planner split/delay sederhana, meter v1 (kandidat per event, data rings-collect), version probe,
  pre-check nullifier. Semua CLI dulu.
- **Fase 3 — web/UI (2 minggu):** 3 layar PRODUCT.md (saldo / kirim+meter / autopilot), meter MERAH-
  KUNING-HIJAU jujur, disklusi onboarding (pause protokol, kebocoran level protokol).
- **Fase 4 — manifest & landing:** copy dari PRODUCT.md §1 ("jaga jumlah uangmu jadi urusanmu sendiri"),
  lineage Rivest, batasan jujur §7, meter LIVE dari data on-chain (janji K2 RISK-SIMULATION).
- **Fase 5 — Docker + e2e + agent-iface:** compose, Playwright suite, intent API untuk agent AI.
- **Fase 6 — v2 cross-protocol:** hygiene layer untuk Privacy Cash/Token-2022 CT (moat strategis K3).

## 5. Brainstorming / ide & audit risiko per fitur

- **Meter jujur = moat brand** (K2): tampilkan "1 dari N kandidat" LIVE; kalau MERAH, bilang MERAH.
- **Settlement delay:** biarkan sebagian dana bertahan antar-event (jawaban K1 versi desain — uji dulu
  dengan null-on-parts.py sebelum jadi fitur).
- **Jam sibuk pool** dari tx.jsonl: planner jadwalkan merge/split di jam ramai supaya tercampur.
- **Backtest meter:** replay historis "kalau kamu transfer di jam X, kandidat = N" — fitur edukasi + bukti.
- **Agent payments** = segmen pertama (Doei dst. tanpa privasi); ini diferensiasi, bukan fitur agen-agen.
- **Risiko yang tidak bisa diselesaikan:** pause protokol 2-of-5 (UNVERIFIED), zkSec #01/L-05 —
  disklusi wajib di onboarding, bukan disembunyikan.
- **Jangan build:** mixer, token, custodial, timelock escrow unaudited (aturan sesi).

## 6. Definisi selesai (hard evidence)

- Setiap klaim "jalan" butuh output nyata (signature / angka / test hijau). UNVERIFIED ditulis eksplisit.
- Gate ulang pre-registered sebelum klaim publik efektivitas.
- Secret tidak pernah masuk git (hook + gitignore terverifikasi).
