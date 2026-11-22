# chaff/ — workspace Chaff

Folder ini untuk semua artefak khusus Chaff: data riset, tool eksekusi, dan (jika pernah
dibuka) build. Status saat ini: **gate K1 FAIL — build tidak dimulai**.

## Status gerbang (2026-11-22)

K1 — uji agregat matching (pre-registered di `chaff-session.json`, threshold terkunci):

| kondisi pass rule (7d / tol 1%) | hasil | butuh | verdict |
|---|---|---|---|
| (1) Chaff menurunkan unique aggregate-match ≥ 50% | real 18.7% → chaff 16.3% = −13.0% | ≥ 50% | FAIL |
| (2) Chaff menurunkan unique one-to-one ≥ 80% | real 29.6% → chaff 10.6% = −64.4% | ≥ 80% | FAIL |

Per `on_fail` yang sudah didaftarkan sebelum komputasi: premis produk (split withdraw
mengalahkan pengamat) **gugur**; task_2 (TECH-DESIGN, PoC devnet, landing page, dapp,
docker, e2e) TIDAK dimulai. Kerugian yang diakui: hanya waktu riset.

Temuan penting lain (interpretasi, bukan threshold): pada 7d, real aggregate-match
(18.7%) hanya +0.4pt di atas null (18.3%) — matching agregat sendiri hampir tak
membawa sinyal di pool tester-heavy ini; lantai kebetulan (round-amount clustering)
adalah yang membuat split tak bisa memotong 50%.

## Diagnostik post-hoc: null di atas parts (2026-11-22, `tools/null-on-parts.py`)

Bukan gate, tidak mengubah verdict. Pertanyaan: apakah user chaff masih membawa
SINYAL yang bisa dipelajari penyerang, di atas kebetulan?

| excess atas chance (7d) | real (belum dipecah) | chaffed (parts) |
|---|---|---|
| one-to-one unique | **+4.4 pt** (sinyal nyata) | **−0.7 pt** (≤ kebetulan) |
| aggregate unique | +0.4 pt (≈ nol) | +0.3 pt (≈ nol) |

Bacaan: kegagalan gate disebabkan lantai kebetulan pihak ketiga (nilai bulat orang
lain), bukan karena mekanisme Chaff gagal — sinyal yang bisa dipelajari dari user
chaff hilang total (4.4pt → ≤0). Sifatnya post-hoc: dukungan keputusan, bukan
konfirmasi; gate tetap FAIL dan re-run saat pool matang wajib sebelum klaim publik.

## Keputusan build (RECORDED OVERRIDE — 2026-11-22)

Pemilik produk memutuskan **melanjutkan build meski gate K1 FAIL**, dengan syarat:
- Klaim produk dibatasi: "nothing beyond chance learnable — diukur 2026-11-22 pada
  3 minggu data pool (8996 tx)". Tidak ada klaim "mengalahkan analisis agregat".
- Re-run gate (pre-registered ulang) wajib saat pool matang sebelum klaim publik
  yang lebih keras.
- Posisi produk: **privacy autopilot / hygiene layer untuk agent AI yang bertransaksi
  on-chain** — angka keputusan finansial tetap deterministik + CSPRNG; LLM tidak pernah
  melihat amount kecuali model lokal (prompt API = kebocoran metadata).
- Urutan: (1) PoC bukti bisa jalan → (2) landing/manifesto → (3) web/dapp,
  docker daemon, e2e. Tanpa PoC lolos, fase berikutnya tidak dimulai.
- **UPDATE 2026-11-22 (keputusan pemilik):** PoC dijalankan di **MAINNET** (bukan devnet),
  dana total dibatasi **0.1 SOL** dari wallet pemilik. Risiko diakui: SDK alpha 0.8.0-alpha,
  protokol upgradeable + pause 2-of-5 (UNVERIFIED), fix zkSec/Certora belum terverifikasi.
  Semua dana hanya berpindah antar wallet yang dikontrol sendiri; worst case = stuck, bukan hilang
  (kecuali risiko protokol di atas). Devnet tetap referensi di skrip via CHAFF_NETWORK=devnet.

## PoC progress (2026-11-22)

**Terbukti di mainnet (signature nyata, semua ter-finalize):**
1. `SIG fund-recipient` — owner → recipient 0.005 SOL (ogBV8XPS…DY3jB)
2. `SIG register owner` (2mQurEKK…8Wv)
3. `SIG register recipient` sponsored oleh owner (5VcfLCWj…bpz)
4. `SIG deposit` 0.05 SOL → private balance (4mrmeciV…WoGU) — **finalized** slot 472286300, err=null

**BLOCKER:** `WALLET_SYNC ← CLIENT_INDEXER ← API_HTTP` — indexer Photon dan prover Nitro
(cloudfront, README SDK) mengembalikan **HTTP 403 "Request blocked"** (CloudFront WAF)
untuk SEMUA request tanpa api-key (terverifikasi curl + Node fetch, mainnet & devnet).
README SDK eksplisit: "A client needs a Helius API key". Dengan api-key Helius, jalur
yang didukung SDK: `solanaRpcUrl = https://mainnet.helius-rpc.com/?api-key=KEY` — resolver
endpoint otomatis meminjamkan namespace `/v1/spr` ke indexer & prover (endpoint.js).

**State dana:** private balance owner 0.05 SOL ada DI DALAM pool Rings (aman; bisa
di-withdraw via wallet resmi jika perlu). Private transfer + withdraw menunggu key.

## PoC MAINNET: SELESAI (2026-11-22, run final)

Helius API key didapat. Dua shim VERSION SHIM ditambahkan (T1):
1. `shimIndexerResponse` — indexer `/v1/spr` mengembalikan `data:[{signature, events[]|outputs[]}]`
   + `paginationToken`; SDK 0.8.0-alpha mengharapkan `transactions`/`matches` flat. Decode OK
   terverifikasi langsung terhadap codec SDK.
2. `verifiedMainnetTeePolicy` — file TEE policy kini `{release:{payload,signatures}, freshness}`
   (skema signature baru tak terdokumentasi; verifikasi ed25519 atas 9+ varian pesan gagal semua).
   Pendekatan: PCR measurements DI-EMBED di kode (sumber: URL pinned Helius via HTTPS;
   sha256(payload)==release_sha256 dalam freshness terverifikasi); file ditolak bila measurements
   berubah. Attestasi enclave (PCR/nonce/HPKE) tetap diverifikasi SDK. DISKLOSUR: bukti ed25519
   "file ini ditandatangani Helius" dilewati — dikompensasi embed + HTTPS pinned URL.

**Hasil run final (semua mainnet, re-entrant):**
- deposit skip (saldo privat 0.05 sudah on-chain) → transfer 0.01 → withdraw 0.025 fee-cut.
- SIG private-transfer: 2vKKud2t2Gt8CqxELm6PnH9p63dcca4aWvxXRZGBCUDNYVRbuWhzYNpYaP7YaD6ooH3xpJaYDWCQtZKhpfLvTCKn
- SIG withdraw-fee-cut: 3foY54erFeZXeTpR9oqxSJStf5KVeg1tmNU9WEK8aWXNiydpvyJcY4PeMvr8ZjyhjHaayb33iofznz1c2xX4y2kz
- Verifikasi angka: owner private 50M − 10M − 25M = 15M ✓; recipient public 5M + 25M − 15k fee = 29,985,000 ✓ (fee-cut).

Master plan & audit fitur: `chaff/MEGA-PLAN.md`.

## Isi folder

- `research/AGGREGATE-REPORT.md` — snapshot laporan gerbang (kanonik:
  `BRAIN/research/rings/AGGREGATE-REPORT.md`).
- `research/gate-summary.json` — angka gerbang dalam format mesin.
- `tools/rings-aggregate.py` — snapshot tool gate (kanonik: `tools/rings-aggregate.py`,
  sumber data `BRAIN/research/rings/tx.jsonl`, tanpa network).

## Jika gate pernah dibuka lagi

Threshold di `chaff-session.json` section `gate` tidak boleh diubah setelah komputasi.
Ulang komputasi: `python3 tools/rings-aggregate.py` (butuh numpy; data lokal).
Keputusan untuk tetap build meski gate FAIL adalah keputusan eksplisit pemilik produk —
harus dicatat di sini siapa kapan mengambilnya, bukan keputusan otomatis agent.
