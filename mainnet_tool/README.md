# mainnet_tool

Builder + auditor untuk project crypto/web3, jaringan apapun (solana / evm / web).
Satu file Python, stdlib saja, tidak menyentuh folder lain.

Dibangun dari pola yang sudah terbukti: `lord.py` (ops deterministik: file/grep/rpc/run),
`codetool.py` (scaffold dari template + check), `glm-audit.py` (disiplin usage + laporan jujur).

## Quickstart (untuk team)

```bash
cd mainnet_tool

# 1. lihat chain yang didukung
python3 mainnet.py list-chains

# 2. lihat contoh blueprint
python3 mainnet.py show blueprint-solana.json

# 3. scaffold project baru dari blueprint (menulis HANYA ke target di blueprint)
python3 mainnet.py init examples/blueprint-solana.json

# 4. audit 15 dimensi (evidence-based; tulis laporan ke mainnet_tool/reports/)
python3 mainnet.py check examples/blueprint-solana.json

# 5. verifikasi tool-nya sendiri (jalankan dulu ini di mesin baru)
python3 mainnet.py selftest
```

## Blueprint JSON — 15 dimensi

Setiap project punya satu blueprint (`spec: mainnet-tool/1`). Bagian `project` menentukan
nama/chain/network/root; `build` menentukan scaffold; `dimensions` menimpa check bawaan
untuk dimensi mana pun. Check bawaan sudah ada untuk semua 15 dimensi ini — blueprint
tinggal menambah yang spesifik project:

| dimensi | pertanyaan bawaan |
|---|---|
| backtest | eksperimen berjalan & terukur? |
| backend | entrypoint + dependensi terpasang? |
| frontend | ada frontend? |
| ui-ux | UI dibuat & diuji? (manual) |
| user-experience | alur pengguna terdefinisi? |
| user-flow | dokumentasi end-to-end? |
| concept-narasi | one-liner produk tertulis? |
| workflow | scripts install->test->build? |
| framework | lockfile / registry? |
| docker | container siap? |
| implementasi | artefak jalan (log/build)? |
| mainnet-onchain | target on-chain hidup? (isi rpc check) |
| api-kebutuhan | endpoint eksternal tersedia? |
| resource-github-hf | repo GitHub / model HF aktif? |
| fitur-berfungsi | fitur per fitur: jalan/belum + brainstorm |

## Tipe check

`files` (glob; expect all/any/none_exist) · `grep` (pattern, path, min/max_count) ·
`command` (shell, expect_exit; pola destruktif DITOLAK) · `http` (url, expect_status) ·
`rpc` (JSON-RPC url/method/params, expect_fields — solana & evm sama-sama JSON-RPC) ·
`github` (repo, expect_active_within_days) · `huggingface` (kind, id) · `docker` ·
`manual` (selalu UNVERIFIED — kejujuran, bukan kelemahan).

## Aturan absolute mode

1. Verdict hanya dari evidence yang ditangkap. Tanpa evidence = UNVERIFIED.
2. `init` menolak target yang sudah ada isinya (kecuali `--force`).
3. Tool menulis hanya ke `mainnet_tool/.cache`, `mainnet_tool/reports/`, dan target di blueprint.
4. Command destruktif ditolak otomatis.
5. Setiap laporan mencatat jumlah network call (fresh vs cached) — biaya transparan.

## Verdict

`WORKS` semua check lolos dengan bukti · `BROKEN` ada check gagal (evidence menunjukkan kenapa) ·
`UNVERIFIED` tidak bisa dicek mesin / manual · `N/A` artefak memang tidak diharapkan.
Exit code 1 kalau ada BROKEN — cocok untuk CI.

## Perilaku audit pada scaffold baru (disengaja)

Scaffold yang baru di-`init` akan menunjukkan BROKEN di beberapa dimensi — itu fitur, bukan bug:
audit berfungsi sebagai checklist progress. Urutan menyalakannya:

1. `npm install` di folder project -> framework jadi WORKS (lockfile ada)
2. tambahkan test -> backtest jadi WORKS
3. `npm run build` -> implementasi jadi WORKS (dist/ ada)
4. isi dimensi spesifik di blueprint (onchain rpc, api, github/hf, fitur) -> menyesuaikan project

Kalau project memang tidak punya frontend (CLI/backend), timpa dimensi `frontend` di blueprint
dengan check `{"type": "docker", "expect": "none"}` atau manual.
