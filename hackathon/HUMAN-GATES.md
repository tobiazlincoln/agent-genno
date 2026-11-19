# Human Gates — yang harus dijalankan manusia

## p1-testnet (opsional dry-run sebelum mainnet)
1. Dapatkan testnet BNB: faucet https://testnet.bnbchain.org (butuh 0.02+ BNB tBNB).
2. Buat wallet baru untuk deployer (JANGAN pakai wallet utama), simpan key di `.env` sebagai `PRIVATE_KEY=0x...` (`.env` gitignored).
3. Jalankan:
   ```
   cd hackathon/contracts
   export PATH="$HOME/.foundry/bin:$PATH"
   export PRIVATE_KEY=0x...
   export REGISTRY=<alamat mock registry testnet, atau deploy MockRegistry dulu>
   forge script script/Deploy.s.sol --rpc-url https://data-seed-prebsc-1-s1.binance.org:8545 --broadcast
   ```

## p3-mainnet (GATE WAJIB untuk eligibility)
1. Pastikan `hackathon/contracts` sudah push ke GitHub public (open source requirement).
2. Isi `.env`: `PRIVATE_KEY` (deployer dengan BNB gas, ~0.01 BNB cukup), `BSCSCAN_API_KEY` (buat akun di bscscan.com).
3. Deploy + verify:
   ```
   cd hackathon/contracts
   export PRIVATE_KEY=0x... BSCSCAN_API_KEY=...
   forge script script/Deploy.s.sol --rpc-url https://bsc-dataseed.binance.org --broadcast --verify --chain 56
   ```
4. Cek di BscScan: source code verified, owner permissions = none (no owner).
5. Update `<CONTRACT_ADDRESS>` di: `hackathon/skill.md`, `hackathon/llms.txt`, `hackathon/site/index.html`.

## p4-distribute
1. Submit via form Binance (link di hackathon-session.json) — fields: nama project, website (GitHub Pages/Cloudflare Pages dari hackathon/site), contract address, deskripsi Agent ID usage (tulis untuk rubrik 30% depth: badge terikat identitas .ai, attest, handleOf display).
2. X thread: #BinanceWalletHackathon #AgenticWallet + copy-paste prompt untuk user.
3. Cross-promo dengan peserta lain (Colony threads, replies).
4. Monitor harian: `scripts/hackathon-metrics.sh <CONTRACT_ADDRESS>` — target 30+ unique agents.

## Deadline: 2026-12-09 08:00 UTC. Submit maksimal 7 Des.
