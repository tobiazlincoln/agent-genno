# CHAFF — RISK SIMULATION & CRITICAL DEEP-DIVE (22 Nov 2026)

Metode: setiap risiko ditulis sebagai SIMULASI KONKRET (apa yang terjadi, bukan "mungkin
masalah"), lalu dinilai: KILLER (membunuh produk) vs MANAGEABLE (bisa direkayasa keluar).
Sumber angka: data 25k+ transaksi yang kita kumpulkan, audit Certora/zkSecurity, SDK repo.

====================================================================
BAGIAN 1 — RISIKO YANG MEMBUNUH (kalau tidak dijawab, jangan build)
====================================================================

## K1. Analisis agregat mengalahkan split (KILLER — risiko inti)

Eksperimen bocor kita menguji pencocokan SATU-deposit-vs-SATU-withdraw. Tapi penyerang
yang serius (Iris sudah komersial) bisa pakai pencocokan AGREGAT: jumlah total deposit
dari alamat A dalam 24 jam ≈ jumlah total withdraw ke alamat B dalam 24 jam.

SIMULASI: Chaff membelah withdraw 5 SOL jadi 1.87 + 2.03 + 1.09 dalam 6 jam. Penyerang
menjumlahkan semua withdraw ke B hari itu: 5.0 — dan menjumlahkan deposit A: 5.02.
Split kita tidak menyembunyikan TOTAL, hanya memecahnya.

Konsekuensi: split saja TIDAK CUKUP. Desain harus: (a) jendela waktu jauh lebih panjang
dan acak (hari, bukan jam), (b) amount shaping termasuk membiarkan sebagian dana
BERTAHAN di pool antar-event (settlement delay yang disengaja), (c) sinkronisasi ke
jam-jam sibuk pool supaya kandidat tercampur aktivitas orang lain.
STATUS: belum terukur. Ekstensi wajib eksperimen bocor: uji AGREGAT matching sebelum
satu baris kode produk ditulis. Kalau agregat matching menang mudah, premis produk gugur.

## K2. Paradox cold-start: privacy butuh kerumunan (KILLER jangka pendek)

"1 dari 40+ kandidat" hanya mungkin kalau ada 40 deposit serupa di jendela waktu itu.
Total deposit Rings sejak launch: $1,02M. Ini bukan Tornado Cash 2021.

SIMULASI hari peluncuran: 200 install, 60% isi 0.01–0.1 SOL (persis perilaku sekarang).
Visibility meter jujur menampilkan MERAH: "1 dari 2 kandidat". Pengguna uninstall:
"bukannya privat kok".

Konsekuensi: produk harus HONEST meter (angka nyata, bukan greenwashing) + strategi
timing: jadwalkan event di jam sibuk pool (data jam sibuk sudah bisa dihitung dari
tx.jsonl kita), dan positioning awal bukan "anonim" tapi "tidak lagi trivially
cocok" — penurunan sinyal, bukan kehilangan jejak total.

## K3. Helius bisa membangun ini sendiri (KILLER strategis)

Leak-nya ada di docs resmi mereka; mitigasi resmi mereka cuma "pakai onramp". Wallet-kit
mereka satu SDK release dari "hygiene mode". Kami cuma lapisan tipis di atas SDK
mereka, dan SDK-nya masih alpha (0.8–0.9, baru saja rename spr→zolana TANPA peringatan).

SIMULASI: 3 bulan setelah kami launch, Helius menambah autoSplit ke wallet-kit gratis.
Moat kami: kecepatan (6+ bulan head start), cross-protocol v2 (satu autopilot untuk
Rings + Privacy Cash + Light + Token-2022 CT — "hygiene layer untuk SEMUA rel privasi
Solana", itu yang tidak akan Helius bangun karena mereka menjual Rings), dan brand
kejujuran (meter yang tidak membohongi).
STATUS: keputusan v2 harus cross-protocol sejak hari pertama arsitekturnya.

## K4. Pause protokol & upgrade authority (KILLER eksternal, tak termitigasi)

Program upgradeable; disclosure Rings.run: 2-of-5 multisig bisa pause. Certora I-03:
ring authority bisa withdraw via public settlement; I-02: ring deposits bisa drain
SPL yang dikontrol ring_auth (fixed, tapi pola risikonya nyata).

SIMULASI: tekanan regulasi → pause → SEMUA saldo privat user Chaff tidak bisa diakses.
Kami tidak bisa apa-apa di layer app. Mitigasi satu-satunya: DISKLOSUR di onboarding
("dana di pool milik protokol, bukan Chaff; protokol bisa di-pause oleh multisig 2-of-5")
+ dokumentasi jalur darurat manual via wallet resmi Helius.

====================================================================
BAGIAN 2 — KENDALA TEKNIK (MANAGEABLE, tapi tiap satu butuh jawaban desain)
====================================================================

## T1. Churn SDK alpha + pinning versi protokol
SDK mensyaratkan versi circuit/pins cocok dengan protokol yang ter-deploy. Renamed
mid-beta. SATU mismatch = daemon sync gagal diam-diam untuk seluruh user.
→ Desain: health check harian (probe circuit version vs repo release), auto-update
  daemon, kill-switch otomatis + notifikasi user saat mismatch, BUKAN mencoba prove.

## T2. Fee reserve: user yang menyetor 100% SOL akan TERJEBAK
Withdraw tetap butuh SOL untuk fee dari wallet publik. SIMULASI: user deposit semua
SOLnya → withdraw gagal bayar fee → panik.
→ Aturan keras: Chaff SELALU menahan buffer fee (mis. 0.05 SOL) di saldo publik,
  tombol "move to private" menolak amount yang menghabiskan buffer.

## T3. Kapasitas nullifier & L-03 (acknowledged Certora)
Output bisa masuk tree dengan kapasitas nullifier habis → spend TERBLOKIR sementara.
Split agresif mempercepat habisnya kapasitas (tiap spend = nullifier; tiap nullifier
PDA = rent 0.0007 SOL yang baru dikembalikan forester belakangan).
→ Pre-check kapasitas tree via indexer SEBELUM menjadwalkan split; cap jumlah bagian
  (mis. maks 5/event); merge di jam sepi.

## T4. Compute units & fragmentasi UTXO
Tx sampel kita: ~145k dari 450k CU. Banyak input UTXO = CU naik; transfer multi-bagian
bisa gagal CU. Fragmentasi dari split menumpuk.
→ Merge otomatis saat pool sepi; batasi input per transfer; retry dengan prioritas fee.

## T5. Prover: TEE Helius MELIHAT amounts (Certora eksplisit: "hosted prover receives
private witnesses")
Ironi fatal kalau tidak ditangani: produk penyembunyi jumlah yang membocorkan jumlah
ke prover pihak ketiga. Local proving ada (web/mobile SDK, 0.06–0.43s warm) tapi
daemon background + local proving = kompleksitas baterai/reliabilitas.
→ Keputusan v1: local proving default, remote TEE hanya fallback dengan DISKLOSUR
  eksplisit saat fallback dipakai. Ini fitur kejujuran, bukan kelemahan.

## T6. Indexer & rate limit
Sync butuh Privacy API indexer (Helius). Free tier 10 RPS/1M kredit. Daemon multi-user
jam sibuk → 429 (kita alami sendiri: 1.400+ retry saat koleksi data).
→ Failover multi-provider, self-host Photon sebagai opsi (berat, $49/mo dev tier lebih
  murah daripada ops Photon), backoff eksponensial.

## T7. Keamanan device: daemon memegang key
SIMULASI: laptop user kena malware; Chaff unlocked; malware pakai policy cap harian
untuk menguras bertahap.
→ Policy bukan fitur bonus tapi KONTROL WAJIB: cap harian default rendah, payee
  allowlist, kill switch, notifikasi tiap event, dan key terenkripsi OS-keychain.

====================================================================
BAGIAN 3 — SIMULASI MINGGU PELUNCURAN (narasi konkret)
====================================================================

HARI 1 — 200 install. 60% isi dana kecil (0.01–0.1 SOL, persis perilaku eksisting).
Meter jujur: MERAH ("1 dari 2 kandidat"). Tweet marah: "bukannya private".
→ Harus dijawab SEBELUM launch: ekspektasi = "turun dari trivially-linked ke
  statistically-hard", bukan anonimitas. Landing page wajib menampilkan angka
  kandidat rata-rata LIVE dari data on-chain.

HARI 2 — user deposit 100% SOL, withdraw gagal (fee). Tiket support panik.
→ T2 harus shipped di v1, bukan v1.1.

HARI 3 — Helius rilis breaking change SDK (preseden: rename spr→zolana tanpa notice).
Setengah armada daemon error sync.
→ T1: version probe + auto-update + graceful degrade ("protected transfers paused,
  funds safe").

HARI 4 — kapasitas nullifier tree X rendah; transfer user gagal dengan error obscure.
→ T3 pre-check + pesan human-readable.

HARI 5 — Iris publish thread: "defeating splitters with aggregate sums".
→ K1 harus SUDAH dijawab sebelum launch (riset agregat + desain jendela panjang).
  Kalau belum, jangan launch.

MINGGU 2 — pasar crash lagi; TVL privacy turun; retensi?
→ Produk harus berguna bahkan di throughput rendah: value minimal = meter + edukasi
  + policy engine (berguna meski cover tipis).

====================================================================
BAGIAN 4 — URUTAN YANG BENAR SEBELUM BUILD
====================================================================

1. TUNGGU laporan bocor final (collector jalan).
2. EKSTENSI eksperimen: uji AGREGAT matching (K1). Ini gerbang terakhir premis.
3. Hanya jika lolos: desain teknis v1 (fee reserve, version probe, nullifier check,
   local prover, policy engine) — semua kendala di atas punya jawaban desain.
4. Parallel: verifikasi fix zkSec #00/#01 (belum diverifikasi siapa pun).

Kalau (2) gagal: Chaff tidak jadi — dan kita baru kehilangan waktu riset, bukan produk.
