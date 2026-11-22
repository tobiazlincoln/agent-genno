# mainnet_tool

Builder + auditor untuk project crypto/web3, jaringan apapun.
Satu file Python, stdlib saja, tidak menyentuh folder lain.

## Jaringan terdaftar (chainId & RPC diverifikasi live, 22 Nov 2026)

| network | family | chain id | gas | explorer | public rpc |
|---|---|---|---|---|---|
| `solana` | solana | - | SOL | solscan.io | api.mainnet-beta.solana.com |
| `eth` | evm | 1 | ETH | etherscan.io | ethereum-rpc.publicnode.com |
| `bsc` | evm | 56 | BNB | bscscan.com | bsc-rpc.publicnode.com |
| `robinhood` | evm | 4663 | ETH | robinhoodchain.blockscout.com | rpc.mainnet.chain.robinhood.com |
| `elysium` | evm | 1339 | LAVA | blockscout.elysiumchain.tech | rpc.elysiumchain.tech |
| `evm` | evm | (isi sendiri) | - | - | blueprint wajib isi `build.vars.RPC_URL` + `CHAIN_ID` |

Catatan penting:
- **Tabrakan nama "Elysium"**: yang terdaftar = Vulcan Forged (1339/LAVA). Ada chain lain
  bernama Elysium dari Kinetiq (99901, gas HYPE, HyperEVM L2) — untuk itu pakai chain `evm`
  + rpc/chainId sendiri, dan selalu verifikasi dengan `eth_chainId` sebelum signing.
- **Robinhood public RPC menolak User-Agent python** — tool ini sudah pakai UA browser;
  kalau pakai library lain dan dapat 403, itu sebabnya. Untuk produksi pakai Alchemy
  (rekomendasi resmi Robinhood).
- Auto-check `mainnet-onchain` memverifikasi chain id yang benar per jaringan
  (salah network = BROKEN, bukan UNVERIFIED).

Dibangun dari pola yang sudah terbukti: `lord.py` (ops deterministik: file/grep/rpc/run),
`codetool.py` (scaffold dari template + check), `glm-audit.py` (disiplin usage + laporan jujur).

## Quickstart (untuk team)

```bash
cd mainnet_tool
python3 mainnet.py selftest            # selalu dulu di mesin baru
python3 mainnet.py doctor             # cek node/python/git/docker/gh
python3 mainnet.py networks            # registry bawaan (networks.json — bisa diedit)
python3 mainnet.py networks --find robinhood   # cari chain EVM APA PUN (ethereum-lists, 2899 chain)
python3 mainnet.py init examples/blueprint-elysium.json --git
python3 mainnet.py check examples/blueprint-elysium.json
```

## Apa yang baru di v2 (rebuild)

- **registry jaringan eksternal** (`networks.json`): tambah chain tanpa edit Python.
  `networks --find <nama>` mencari di dataset open source ethereum-lists/chains
  (chainid.network) dan mencetak snippet siap salin — VERIFIKASI `eth_chainId` dulu.
- **template eksternal** (`templates/<family>/`): file nyata; scaffold kini menyertakan
  test, .gitignore, CI (GitHub Actions), Dockerfile — dan lulus `npm test` nyata.
- **`doctor`**: onboarding team — cek environment dalam satu perintah.
- **rpc check mengukur latency** (evidence: `[123ms]`).
- **NEXT ACTIONS**: laporan otomatis membuat daftar perbaikan dari temuan BROKEN.
- `init --git` menambah git init + LICENSE MIT.

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
