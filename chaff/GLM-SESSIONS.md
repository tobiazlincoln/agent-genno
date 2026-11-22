# CHAFF × GLM SESSIONS — prompt kit per pola workflow (coding plan Z.ai)

Satu prompt = satu pola sesi. Salin blok yang sesuai ke session GLM, kirim, selesai.
Semua perintah di dalamnya sudah DIVERIFIKASI jalan di workspace ini (22 Nov).

FAKTA KUNCI yang harus dipegang setiap sesi:
- Gerbang K1 = FAIL (pre-registered, `chaff/research/gate-summary.json`) — klaim produk
  wajib dibatasi; "angin kalah, saringan halus tidak" (lihat `chaff/PHILOSOPHY.md`).
- PoC mainnet SUKSES (register→deposit→transfer→withdraw fee-cut; signature di
  `chaff/README.md`), tapi itu jalur dasar — planner split/delay belum dibangun.
- Audit tool: `mainnet_tool/` — blueprint chaff: `chaff/blueprint.json` (AUDIT-ONLY,
  `init` otomatis ditolak).

═══════════════════════════════════════════════════════════════════
SESI 1 — STATUS / KICKOFF (tanpa mengubah apa pun)
═══════════════════════════════════════════════════════════════════

Kamu agent GLM di workspace /Users/tobiaz/Desktop/GLMagent, project chaff.
BACA dulu (urut): chaff/PHILOSOPHY.md, chaff/MEGA-PLAN.md, chaff/research/gate-summary.json.
Lalu jalankan audit:

  cd /Users/tobiaz/Desktop/GLMagent && python3 mainnet_tool/mainnet.py check chaff/blueprint.json --summary

Laporkan ke saya dalam bahasa sederhana:
1. verdict per dimensi (kutip dari output, jangan interpretasi bebas),
2. satu-satunya BROKEN dan apa artinya,
3. tabel fitur di MEGA-PLAN.md: mana yang JALAN / DESAIN / BELUM,
4. 3 opsi pekerjaan paling masuk akal berikutnya (dari data di atas, bukan opini).
ATURAN: sesi ini READ-ONLY — jangan edit file apa pun. Kalau ada klaim yang tidak
punya bukti di data, tulis UNVERIFIED.

═══════════════════════════════════════════════════════════════════
SESI 2 — IMPLEMENT SATU FITUR (kerja utama coding plan)
═══════════════════════════════════════════════════════════════════

Kamu agent GLM di workspace /Users/tobiaz/Desktop/GLMagent, project chaff.
BACA dulu: chaff/MEGA-PLAN.md (tabel fitur + next), chaff/TECH-DESIGN.md (desain),
chaff/PHILOSOPHY.md (batas klaim — gate K1 FAIL, jangan janjikan anonimitas).

TUGAS SESI INI: [SATU ITEM SAJA, contoh: implement visibility meter dasar di chaff/meter/
dari heuristik tools/rings-analyze.py — atau — implement policy engine di chaff/poc].

Aturan kerja:
1. SATU item per sesi. Tidak ada refactor di luar item. Tidak menulis fitur lain.
2. Evidence-first: setiap langkah harus meninggalkan bukti (output command, tx signature,
   file test). Klaim "selesai" tanpa bukti = tidak selesai.
3. Jangan menjalankan init pada chaff/blueprint.json (audit-only, akan ditolak).
4. Jangan menyentuh folder di luar chaff/, mainnet_tool/reports/, dan .cache milik tool.
5. Secret (.env, key) tidak boleh di-commit atau dicetak.
6. Gagal 2x pada langkah yang sama: STOP, diagnosis, lapor — jangan loop.

SELESAI? buktikan:
  cd /Users/tobiaz/Desktop/GLMagent && python3 mainnet_tool/mainnet.py check chaff/blueprint.json --summary
Laporkan: apa yang berubah (dengan diff ringkas), output bukti, dan verdict audit.
Kalau itemmu menambah fitur baru, TAMBAHKAN check-nya ke chaff/blueprint.json supaya
audit berikutnya mengukurnya (pola check: lihat dimensions di blueprint yang sama).

═══════════════════════════════════════════════════════════════════
SESI 3 — DEBUG / PERBAIKAN BROKEN
═══════════════════════════════════════════════════════════════════

Kamu agent GLM di workspace /Users/tobiaz/Desktop/GLMagent, project chaff.
Konteks: ada yang BROKEN/gagal: [tempel error atau nama check].

Langkah:
1. Jalankan audit dan ambil evidence persisnya:
   cd /Users/tobiaz/Desktop/GLMagent && python3 mainnet_tool/mainnet.py check chaff/blueprint.json
   Baca seksi detail check yang BROKEN — evidence-nya menyebut file:baris penyebab.
2. Baca file itu di sekitar baris itu. Diagnosis akar masalah SEBELUM mengubah apa pun.
3. Perbaiki minimal (surgical). Tidak boleh "sekalian" refactor.
4. Bukti perbaikan: jalankan ulang check (perintah sama, --summary cukup). BROKEN harus
   hilang ATAU kamu jelaskan kenapa tidak (ada BROKEN yang jujur — mis. frontend belum
   dibangun — itu bukan bug, itu status).
ATURAN: hipotesis tanpa data = tulis UNVERIFIED. Gagal 2x → STOP dan lapor.

═══════════════════════════════════════════════════════════════════
SESI 4 — RISET / EKSPERIMEN BARU (pola gerbang pre-registered)
═══════════════════════════════════════════════════════════════════

Kamu agent GLM di workspace /Users/tobiaz/Desktop/GLMagent, project chaff.
Konteks wajib: gate K1 sudah FAIL (chaff/research/gate-summary.json) dan itu harus
dijujuri — baca chaff/PHILOSOPHY.md bagian "batas jujur" sebelum merancang apa pun.

EKSPERIMEN: [contoh: uji ulang agregat matching dengan window 7-30 HARI dan
settlement delay, memakai chaff/tools/rings-*.py + BRAIN/research/rings/tx.jsonl].

Aturan pola gerbang (dari chaff-session.json — terbukti bekerja):
1. TULIS dulu aturan lolos/gagal + threshold SEBELUM komputasi (pre-registered),
   simpan di chaff/research/<nama>-gate.json.
2. Data dulu, kesimpulan kemudian. Semua angka dari data nyata (tx.jsonl / RPC),
   bukan asumsi. Sumber data dicatat.
3. Null model / pembanding acak WAJIB kalau mengklaim "berbeda dari kebetulan".
4. Hasil: report chaff/research/<NAMA>-REPORT.md dengan tabel real-vs-null dan
   verdict PASS/FAIL terhadap aturan yang kamu tulis di (1). Threshold TIDAK BOLEH
   diubah setelah melihat hasil.
5. Kalau FAIL: itu hasil yang sah. Tulis jujur. Kerugian = waktu riset saja.

═══════════════════════════════════════════════════════════════════
SESI 5 — NARASI / DOKUMENTASI (jaga konsistensi filosofi)
═══════════════════════════════════════════════════════════════════

Kamu agent GLM di workspace /Users/tobiaz/Desktop/GLMagent, project chaff.
BACA dulu: chaff/PHILOSOPHY.md (poros: visibilitas tanpa legibilitas; sekam vs biji;
"Winnow nothing"; batas jujur), lalu file yang akan diedit: [README.md / TECH-DESIGN.md
/ landing / MATERIAL LAIN].

ATURAN NARASI (tidak bisa ditawar):
1. Semua klaim harus tertaut ke data: gate-summary.json, laporan riset, signature
   PoC. Tidak ada klaim kemampuan yang tidak terukur.
2. Batas jujur WAJIB ikut: "angin kalah (signal→chance), saringan halus tidak
   (ratio-grid 57pt)" — jangan dipotong demi pemasaran.
3. Kata terlarang tanpa data: "anonim", "tidak terlacak", "terbukti menyembunyikan".
   Kata yang benar: "tercampur tak terbedakan", "illegible bagi penampi kasual".
4. Setelah edit, jalankan:
   cd /Users/tobiaz/Desktop/GLMagent && python3 mainnet_tool/mainnet.py check chaff/blueprint.json --only concept-narasi,ideas-brainstorm
   Konsistensi filosofi harus tetap WORKS. Kalau jadi BROKEN, narasimu melenceng.

═══════════════════════════════════════════════════════════════════
SESI 6 — HANDOFF / CONTEXT PACK (untuk model mahal, hemat kredit)
═══════════════════════════════════════════════════════════════════

Kamu agent GLM di workspace /Users/tobiaz/Desktop/GLMagent.
Tugas: siapkan handoff untuk AI mahal (Claude dll) supaya tidak eksplorasi ulang.

1. Jalankan:
   cd /Users/tobiaz/Desktop/GLMagent && python3 mainnet_tool/mainnet.py context chaff/blueprint.json
2. Baca mainnet_tool/reports/CHAFF-CONTEXT.md yang dihasilkan, periksa isinya akurat
   terhadap chaff/MEGA-PLAN.md dan gate-summary.json.
3. Kalau ada yang usang/kurang, perbaiki blueprint-nya (bukan laporan — laporan
   dihasilkan ulang dari blueprint).
4. Output sesi: file context final + satu paragraf ringkasan untuk saya.

CATATAN: context pack berisi fakta terverifikasi + next actions + instruksi untuk
agent penerima ("jangan eksplorasi ulang"). Itu penghemat token terbesar kita.
