# CHAFF — TECH DESIGN v1 (2026-11-22)

Status: gate K1 FAIL (tercatat), build dilanjutkan via RECORDED OVERRIDE di `chaff/README.md`.
Batas klaim: "nothing beyond chance learnable" (diukur 2026-11-22, 8996 tx, 3 minggu pool).
Semua keputusan finansial otonom = deterministik + CSPRNG, bukan LLM.

## 1. Arsitektur: daemon lokal, bukan web page

Chaff = proses lokal (Node.js 24, TypeScript) di device user, memegang:
- spending key (Ed25519 seed) — terenkripsi OS-keychain, tidak pernah keluar device;
- shielded keypair (zolana `ShieldedKeypair`, seed sama dengan spending key);
- wallet state (`serializeWallet`) — terenkripsi `walletSnapshotCipher`, at-rest.

Modul:
1. `sync` — indexer (Photon) + RPC, cursors persisten (`syncPersistedWallet`).
2. `meter` — visibility meter (S5): estimasi kandidat sebelum kirim, dari data on-chain.
3. `planner` — split/delay/merge scheduler. Deterministik + CSPRNG (`crypto.randomBytes`),
   TIDAK LLM. Output: daftar event (amount, waktu, jenis tx) yang bisa diaudit ulang.
4. `executor` — build+submit tx zolana; retry dengan prioritas fee; pre-check (S4, S6).
5. `policy` — kontrol wajib (S7): cap harian, payee allowlist, kill switch, notifikasi.
6. `agent-iface` — antarmuka untuk agent AI / operator (S8).

Desain delayed execution: blockhash expired ~60s → daemon yang memegang key menjalankan
event sesuai jadwal (opsi 6a DESIGN-INVESTIGATION). Tidak ada escrow/timelock unaudited.

## 2. Prover: local default, TEE fallback dengan disclosure

- Default: **local proving** (`proofDataSource` mode client / `LocalKeys`) — witness (amount)
  tidak pernah keluar device. 0.06–0.43s warm per bukti.
- Fallback: remote TEE (Nitro enclave, policy pinned `SignedTeePolicy.forNetwork`) HANYA jika
  local prove gagal (device lemah, bug). Saat fallback aktif: **disclosure eksplisit ke user —
  "prover remote melihat amount transaksi ini"** — ditampilkan sebelum eksekusi, dicatat di log
  lokal. Ini fitur kejujuran, bukan kelemahan.
- Policy TEE diambil dari release yang di-review (bukan dari respons prover itu sendiri).

## 3. Fee model: fee-cut-from-withdrawal, TANPA buffer

- `feePayer = recipient` pada withdraw/split ("Sponsored fees" SDK; terbukti di mainnet:
  413/1361 SOL withdraw memakai pola ini — verified_facts).
- Konsekuensi: fee dipotong dari jumlah yang diterima. `amount < fee + dust` → DITOLAK
  saat itu juga dengan pesan human-readable, bukan ditahan buffer.
- Fee per tx ~87,532 lamports median (ukuran sendiri); rent nullifier PDA ~706,120 lamports,
  dikembalikan forester belakangan — ditampilkan sebagai "refundable".

## 4. Version probe harian (T1)

SDK alpha; rename spr→zolana tanpa peringatan adalah preseden. Daemon harian:
1. Probe versi circuit/pin vs release terbaru (GitHub releases + `client.confirmTransaction`
   health). Bandingkan dengan versi yang di-pin daemon.
2. Mismatch → kill-switch otomatis: "protected transfers paused, funds safe", notifikasi.
   TIDAK mencoba prove dengan pin lama.

## 5. Pre-check kapasitas nullifier (T3, Certora L-03)

Sebelum menjadwalkan split: cek kapasitas tree via indexer; cap bagian per event (maks 5);
merge di jam sepi (jam sibuk pool dihitung dari tx.jsonl via `tools/rings-*.py`).
Kapasitas rendah → jadwalkan merge dulu, pesan human-readable, bukan error obscure.

## 6. Visibility meter (fitur khas; heuristik = eksperimen bocor kita)

Sebelum kirim, meter menampilkan estimasi kandidat dari data on-chain nyata:
- MERAH: "1 dari 1 kandidat" (withdraw pas setelah deposit same-address, amount bulat)
- KUNING / HIJAU: "1 dari N kandidat serupa" (N dari distribusi amount di jendela W).
Implementasi: port `match_counts` + null model `tools/rings-analyze.py` ke modul `meter`,
dataset di-refresh berkala via `tools/rings-collect.py`. Meter tidak pernah membohongi
(angka nyata; K2: kalau pool sepi, meter MERAH — itu benar).

## 7. Policy engine (T7 — kontrol kerusakan, bukan fitur bonus)

- Cap harian default RENDAH (di-set saat onboarding, bukan nanti).
- Payee allowlist; payee baru butuh konfirmasi eksplisit.
- Kill switch: menghentikan semua event terjadwal; dana tetap aman di pool (withdraw manual).
- Notifikasi per event. Key di OS-keychain; state wallet terenkripsi.

## 8. Agent interface + batasan LLM

Chaff adalah autopilot untuk agent AI yang bertransaksi on-chain (posisi: hygiene layer;
agent-pay kontrol sendiri sudah crowded — VERDICTS.md — yang kosong adalah privasinya).
- `agent-iface`: intent `transfer{recipient, amount, mode: INSTANT|PROTECTED}` → policy
  engine → planner → executor. Agent eksternal TIDAK PERNAH pegang key.
- **LLM tidak pernah melihat amount** kecuali model lokal on-device. Prompt ke API eksternal
  = kebocoran metadata (ironi T5). Keputusan finansial (split size, jadwal, merge) =
  deterministik + CSPRNG, audit-replayable. LLM hanya: intent parsing, penjelasan meter,
  negosiasi policy — semua tanpa amount.

## 9. Yang tidak diperbaiki Chaff (disklusi terbuka, onboarding)

- Kebocoran level protokol: zkSec #01 private_tx_hash, Certora L-05 cache selection — fix
  belum terverifikasi independen. Out of scope client.
- Pause protokol: program upgradeable, pause 2-of-5 (klaim Rings.run, UNVERIFIED). Dana di
  pool milik protokol, bukan Chaff. Jalur darurat: withdraw manual via wallet resmi.
- Deposit dari dana publik inherently terlihat; onramp = satu-satunya fix penuh.
- Registry mengumumkan siapa bisa menerima transfer privat.

## 10. PoC (bukti bisa jalan, sebelum UI apa pun)

Urutan wajib (task_2): register → deposit → private transfer → withdraw fee-cut
(feePayer = recipient) — semua signature on-chain tertulis di output.
Lokasi: `chaff/poc/` (TypeScript, @heliuslabs/zolana + @solana/kit). Secret TIDAK
di-commit: key file di .gitignore. Contoh unaudited TIDAK dipakai dengan dana nyata.
**Jaringan: MAINNET (keputusan pemilik 2026-11-22), dana dibatasi 0.1 SOL** — devnet
tersedia via CHAFF_NETWORK=devnet (faucet script-access diblokir Cloudflare; RPC airdrop
ditutup, lihat README). Skala mainnet: owner 0.09 SOL (register + deposit 0.05 + transfer
0.01 + withdraw 0.025), recipient 0.005 SOL (fee payer withdraw); registrasi recipient
di-sponsori owner.

## 11. Roadmap setelah PoC

1. Landing + manifesto (lineage Rivest 1998 "chaffing and winnowing"; lower-case, no hype).
2. Daemon + meter hidup; web/dapp membungkus daemon lokal.
3. Docker untuk daemon; e2e test (playwright) + test deterministik planner.
4. Re-run gate pre-registered ulang saat pool matang → baru klaim publik lebih keras.
