# CHAFF — PRODUCT DEFINITION (v1, 22 Nov 2026)

Aturan file ini: setiap klaim harus bisa dijelaskan TANPA kata — rings, UTXO, ZK,
nullifier, heuristic, fingerprint. Kalau butuh istilah itu, berarti definisinya belum selesai.

## 1. Satu pekerjaan (the job)

**"Jaga jumlah uangmu jadi urusanmu sendiri."**

Di Solana semua orang bisa melihat siapa membayar siapa. Privacy Rings menyembunyikan
jumlahnya. Tapi cara orang memakainya (deposit dan withdraw yang polos) bisa membocorkan
jumlah itu kembali. Chaff adalah autopilot yang memastikan jumlahmu benar-benar tetap
tersembunyi.

Versi 5 kata: "your amounts stay yours."
Versi satu kalimat: "a private wallet that watches how you move money, so watchers can't."

## 2. Model mental: uang tunai + jam bank

Dua analogi yang sudah dipahami semua orang, tidak perlu diajari:

1. **Uang tunai.** Saat bayar tunai, tidak ada yang tahu isi dompetmu atau dari mana
   uangmu berasal. Saldo publik Solana = rekening koran yang ditempel di dinding.
   Chaff = berperilaku tunai.
2. **Jam bank, bukan kriptografi.** User sudah paham transfer cepat vs lambat dari
   perbankan (wire vs ACH). Chaff memakai pemahaman itu:
   - mode INSTANT: sampai detik ini, terlihat jumlahnya (untuk transfer kecil, siapa peduli)
   - mode PROTECTED: sampai dalam beberapa jam, jumlahnya tidak bisa disimpulkan
   Trade-off-nya dinyatakan sebagai WAKTU — bukan sebagai sains. User memilih seperti
   memilih kirim uang bank, bukan memilih algoritma.

## 3. Yang dilihat user (seluruh produk = 3 layar)

**Layar saldo.** Dua angka: public balance, private balance. Satu tombol besar:
"move to private" (dan "cash out"). Tidak ada jadwal split, tidak ada parameter —
semua otomatis di belakang.

**Layar kirim.** Amount + penerima + INDICATOR VISIBILITAS sebelum kirim:
- MERAH: "transfer ini bisa dicocokkan: 1 dari 1 kandidat" (contoh: withdraw dengan
  amount pas persis, 10 menit setelah deposit)
- KUNING: "1 dari 7 kandidat serupa"
- HIJAU: "1 dari 40+ kandidat — praktis tidak bisa disimpulkan"
Angka kandidat dihitung dari data on-chain nyata (heuristik yang sama dengan
eksperimen bocor kita). Ini fitur khas Chaff: spellcheck privasi SEBELUM kirim,
bukan laporan sesudah kebocoran.

**Layar autopilot.** Satu toggle: "auto-protect my transfers" (default ON).
Ketika ON, user memilih mode INSTANT atau PROTECTED per transfer. Sisanya tidak
kelihatan. Satu baris kecil menjelaskan konsekuensi: "protected transfers finish
within 24h, like a bank transfer."

Yang tidak pernah dilihat user: pembagian amount, jeda, jam eksekusi, merge UTXO,
pemilihan prover. Itu urusan mesin — seperti user TCP yang tidak perlu tahu retransmission.

## 4. Apa yang Chaff lakukan di belakang (untuk docs, bukan user)

1. SPLIT: satu aksi besar jadi beberapa transaksi kecil, ukuran acak non-bulat.
2. DELAY: jeda acak antar bagian, tersebar di jam-jam berbeda.
3. ROUTE: peringatkan pola bunuh diri (withdraw ke alamat yang = alamat deposit,
   amount pas persis, withdraw menyusul deposit dalam menit).
4. MERGE: rapikan pecahan UTXO di jam sepi.
5. POLICY: cap harian, payee list, kill switch — batas kerusakan kalau device dicuri.

Biaya semua itu ~0,00009 SOL per transaksi — tidak terasa.

## 5. Apa yang Chaff BUKAN (sama pentingnya dengan apa yang ia)

1. **BUKAN alat anonimitas.** Alamat terlihat. Siapa transaksi dengan siapa tetap
   publik di ring default. Kalau kebutuhannya "putuskan jejak ke wallet bersih",
   itu produk lain (Privacy Cash). Chaff menyembunyikan BERAPA, bukan SIAPA.
2. **BUKAN mixer.** Tidak pernah menyentuh dana orang lain. Tidak ada pool milik
   Chaff. User menandatangani semua transaksinya sendiri, di devicenya.
3. **BUKAN token / investasi.** Software dengan biaya pemakaian. Tidak ada janji return.
4. **BUKAN protokol baru.** Dibangun di atas Solana Privacy Rings (Helius). Kalau
   Rings mati, Chaff mati — dan itu ditulis terbuka.
5. **BUKAN pelarian dari compliance.** Untuk institusi ada jalur auditor di custom
   rings. Chaff = privasi jumlah untuk individu, bukan kantong gelap.

## 6. Janji teknis yang tepat (satu paragraf, untuk whitepaper)

Pada ring default, pengamat melihat SIAPA bertransaksi dengan SIAPA, tapi tidak
BERAPA. Namun jumlah deposit dan withdraw bersifat publik; tanpa perlindungan,
pencocokan amount-waktu merekonstruksi jumlah yang berpindah secara privat
(median gap yang kami ukur: 137 detik; 15,4% withdraw kembali ke alamat depositnya).
Chaff membentuk event publik pengguna — jumlah, jumlah bagian, waktu, pola —
sehingga rekonstruksi tersebut gagal secara statistik. Yang tersisa untuk
pengamat: "orang ini memakai privasi" — tanpa angka.

## 7. Batas yang kita akui (harus tampil di produk, bukan tersembunyi)

- Kebocoran level protokol (zkSec #01, Certora L-05) di luar jangkauan client.
- User harus menjalankan aplikasi agar transfer PROTECTED selesai (seperti download
  manager) — ini konsekuensi desain, bukan bug.
- Eksperimen bocor final belum selesai; klaim efektivitas angka pasti menunggu itu.

## 8. Uji kebingungan (harus lolos semua)

- "Apa ini wallet?" → Ya, wallet privat dengan autopilot. (Janganhindari kata wallet —
  user butuh jangkar familiar. Chaff ADALAH wallet; autopilot adalah bedanya.)
- "Bedanya sama mixer?" → Mixer mencampur dana orang banyak; Chaff hanya menjadwalkan
  transaksimu sendiri.
- "Sama Privacy Cash?" → Mereka memutus jejak SIAPA; kami menjaga rahasia BERAPA.
- "Kok lama sampainya?" → Sama seperti transfer bank: cepat = terlihat, terlindungi = beberapa jam.
- "Kena hack dong app-nya?" → Key tidak pernah keluar device; cap harian membatasi kerusakan.
