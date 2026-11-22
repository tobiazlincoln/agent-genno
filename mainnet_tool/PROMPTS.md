# PROMPTS SIAP TEMPEL — untuk team (awam friendly)

Cara pakai: buka AI agent apa pun (Devin / Claude Code / GLM), salin satu blok di bawah,
isi bagian dalam [kurung siku], tempel, kirim. Tidak perlu hafal perintah apa pun —
AI-nya yang menjalankan tool. Semua prompt sudah berisi aturan pengaman.

═══════════════════════════════════════════════════════════════════
PROMPT 1 — BUAT PROJECT BARU
═══════════════════════════════════════════════════════════════════

Jalankan tool mainnet di /Users/tobiaz/Desktop/GLMagent/mainnet_tool untuk membuat
project baru dengan data ini:

- nama project: [NAMA, tanpa spasi, contoh: my-token-app]
- jaringan: [solana / eth / bsc / robinhood / elysium]
- deskripsi satu kalimat: [contoh: onchain registry untuk tiket]

Langkah kamu:
1. Baca mainnet_tool/README.md dulu.
2. Salin mainnet_tool/examples/blueprint-elysium.json jadi [NAMA].json di folder itu,
   lalu edit isinya: name, chain, desc, dan root sesuai nama project.
3. Jalankan: python3 mainnet_tool/mainnet.py init [NAMA].json --git
   (jalankan dari dalam folder mainnet_tool).
4. Jalankan: python3 mainnet_tool/mainnet.py check [NAMA].json --summary
5. Laporkan ke saya: file apa saja yang terbuat, dan daftar hal yang masih BROKEN
   (itu checklist, bukan error).

Aturan: jangan mengedit file di luar folder project dan mainnet_tool. Jangan commit
secret atau .env. Kalau ada langkah yang gagal 2x, berhenti dan lapor apa errornya.

═══════════════════════════════════════════════════════════════════
PROMPT 2 — CEK STATUS PROJECT (paling sering dipakai)
═══════════════════════════════════════════════════════════════════

Di /Users/tobiaz/Desktop/GLMagent/mainnet_tool, jalankan audit untuk project
[NAMA] (blueprint: [NAMA].json):

python3 mainnet_tool/mainnet.py check [NAMA].json --summary

Lalu jelaskan hasilnya ke saya dalam bahasa sederhana:
- mana yang sudah hijau (WORKS),
- mana yang BROKEN dan apa artinya untuk user,
- apa 3 langkah konkret berikutnya.
Kalau saya mau detail, jalankan tanpa --summary dan tunjukkan seksi NEXT ACTIONS.

════════════════════════════════════════════════════════════════════
PROMPT 3 — MELANJUTKAN PEKERJAAN (hemat, untuk agent mahal)
═══════════════════════════════════════════════════════════════════

Kerjakan lanjutan project [NAMA]. Jangan eksplorasi repo dari nol:

1. Baca mainnet_tool/reports/[NAMA]-CONTEXT.md — itu sumber kebenaran: semua klaim
   di sana sudah terverifikasi, ada next actions di dalamnya.
2. Kalau file itu tidak ada atau isinya lebih tua dari pekerjaan terakhir, jalankan dulu:
   python3 mainnet_tool/mainnet.py context [NAMA].json
3. Kerjakan HANYA item paling atas di NEXT ACTIONS.
4. Selesai? Jalankan: python3 mainnet_tool/mainnet.py check [NAMA].json --summary
   Laporkan: apa yang berubah dari BROKEN jadi WORKS, dengan evidence.

Aturan: satu item per sesi. Tidak ada refactor di luar item. Klaim "selesai" hanya
boleh kalau audit menunjukkan hijau.

═══════════════════════════════════════════════════════════════════
PROMPT 4 — MENAMBAH JARINGAN BARU (selain yang terdaftar)
═══════════════════════════════════════════════════════════════════

Saya mau pakai jaringan [NAMA CHAIN, contoh: avalanche] di tool mainnet
(/Users/tobiaz/Desktop/GLMagent/mainnet_tool):

1. Jalankan: python3 mainnet_tool/mainnet.py networks --find [NAMA CHAIN]
2. Dari hasilnya, pilih yang MAINNET (bukan testnet), catat chain id dan RPC-nya.
3. VERIFIKASI dengan memanggil eth_chainId ke RPC itu — chain id yang dikembalikan
   HARUS sama dengan claim dataset. Kalau beda, berhenti dan lapor.
4. Kalau cocok: tambahkan entri ke mainnet_tool/networks.json (family: "evm",
   rpc, chain_id, currency, explorer) dengan nama key [NAMA CHAIN].
5. Uji: python3 mainnet_tool/mainnet.py networks lalu buat blueprint kecil dengan
   chain itu dan jalankan check --only mainnet-onchain. Laporkan hasilnya.

═══════════════════════════════════════════════════════════════════
PROMPT 5 — ADA ERROR / DEBUG
═══════════════════════════════════════════════════════════════════

Tool mainnet di /Users/tobiaz/Desktop/GLMagent/mainnet_tool error/gagal saat
[situasi: contoh "init project X" / "check project X"].

1. Baca pesan errornya sepenuhnya — tool ini sengaja memberi pesan error yang
   menjelaskan apa yang kurang; mulai dari sana, jangan nebak.
2. Jalankan python3 mainnet_tool/mainnet.py selftest untuk memastikan tool-nya
   sendiri sehat.
3. Kalau selftest FAIL atau error berlanjut setelah 1x perbaikan masuk akal:
   STOP. Laporkan ke saya: perintah persis yang dijalankan, output error persis,
   dan isi file blueprint yang dipakai. Jangan mengulang-ulang percuma.
