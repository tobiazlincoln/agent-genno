# Roadmap Menang Agent ID Hackathon
Dibuat 2026-11-19. Deadline: 2026-12-09 08:00 UTC. Sisa 20 hari.
Target: minimal eligible Innovation (30+ alamat .ai) + competitive Pioneer metrics.

## Prinsip strategi
- Menang = distribusi + depth, bukan cuma kode. Dua-track paralel: BUILD (agent) dan DISTRIBUTION (manusia).
- GLM mengerjakan: kontrak, skill files, landing page, tests, docs. Manusia mengerjakan: wallet ops, Binance app, submit form, community outreach.
- Compliance diperlakukan sebagai fitur (immutable, no-owner, zero-approval, zero-promised-return) — ditulis eksplisit di README + submission.

## Phase 0 — Setup & validasi (Hari 0-2, 19-21 Nov)
- [ ] Manusia: claim `.ai` di Binance App (Wallet > banner > Agent ID). Install `baw` (`npm i -g @binance/agentic-wallet`), `baw auth signin`, enable Developer Mode.
- [ ] Manusia: buat akun BscScan → API key (untuk contract verification). Simpan di `.env`.
- [ ] Agent: cek `totalSupply` registry `0x60B9...022F` via BscScan API/RPC → estimate holder base `.ai`.
- [ ] Agent: baca ABI registry di BscScan → dokumentasikan resolve `.ai`/address.
- [ ] Agent: install + baca skill resmi `binance-skills-hub/binance-agentic-wallet` — standar format skill kita.
- [ ] Keputusan: pilih 1 konsep final (default: agent proof-of-work log). Tulis 1-page concept doc.
- Gate: `.ai` claimed, baw signed-in, dev mode on, konsep disetujui user.

## Phase 1 — MVP kontrak (Hari 2-6, 21-25 Nov)
- [ ] Foundry project di `hackathon/contracts/`: Solidity 0.8.x, registry immutable di constructor.
- [ ] Core: `logWork(bytes32 workHash, string tag)` gated `balanceOf(msg.sender) > 0`; events indexed; per-agent log; public counter; streak/day optional untuk tx loop.
- [ ] Tests Foundry: gate enforcement (non-.ai revert), idempotency, event correctness. Fork-test vs mainnet registry.
- [ ] Deploy testnet dulu (BSC testnet 97) → dry-run flow.
- [ ] Deploy mainnet → verify BscScan (sourcify/etherscan verify via forge). Open-source repo GitHub public.
- Gate: verified contract address di BSC mainnet, tests pass, README compliance checklist ditulis.

## Phase 2 — Agent UX & skill (Hari 6-9, 25-28 Nov)
- [ ] `skill.md` + `llms.txt` gaya baw-skill: preflight (wallet status, devMode, agent-id) → preview → confirm → execute. Zero hardcode sensitif; contract addresses dari file ini saja.
- [ ] Copy-paste prompt untuk user ("paste ke agent kamu") — pola distribusi agent-checkin.
- [ ] Landing page (static, GitHub Pages/Cloudflare Pages): apa itu, contract address, prompt, leaderboard public (baca events via RPC), risk note. Tanpa wallet-connect (agent-native).
- [ ] Read API sederhana: leaderboard + agent profile lookup (read-only RPC → JSON).
- Gate: end-to-end — user baru bisa "copy prompt → agent eksekusi → muncul di leaderboard" dalam <2 menit.

## Phase 3 — Distribusi (Hari 9-19, 28 Nov–8 Des) — INI YANG MENENTUKAN
- [ ] Daftar semua project peserta lain (Colony threads, hashtag X) → cross-promo: kita interact project mereka, minta mereka coba kita.
- [ ] X thread launch: #BinanceWalletHackathon #AgenticWallet — plus submit ke survey community award (bonus 100 USDC chance).
- [ ] Outreach langsung ke `.ai` holders yang visible di komunitas (Colony, replies tweet Binance).
- [ ] Onboarding friction removal: panduan 3-langkah di landing; FAQ; "works with any agent that has baw skill".
- [ ] Dashboard metrik: script monitor daily unique `.ai` interactors vs target 30+/100+.
- Gate harian: unique addresses naik setiap hari; pivot messaging kalau stagnan.

## Phase 4 — Polish & submit (Hari 18-20, 6-9 Des)
- [ ] Submission form: nama, website, contract addrs, deskripsi Agent ID depth (tulis untuk 30% rubrik).
- [ ] README final: arsitektur, compliance checklist, link BscScan verified, quickstart.
- [ ] Demo video/gif singkat untuk judges + X.
- [ ] Final compliance audit vs daftar larangan — checklist satu per satu.
- [ ] Cadangan: submit 1-2 hari sebelum deadline, jangan menunggu jam terakhir.

## Metrik sukses
- Minimum: 30 unique `.ai` addresses → eligible Innovation Award.
- Target: top-10 Pioneer → butuh jadi top-10 dari ~semua peserta dalam tx count + unique addresses.
- Stretch: rank 1-5 Pioneer/Innovation.

## Risiko & mitigasi
| Risiko | Mitigasi |
|---|---|
| <30 unique addresses | Start distribusi hari ke-9 MAX; join semua thread peserta; cross-promo reciprocal |
| Dev Mode baw expired (7 hari) | Reminder renew di app; dokumentasikan di FAQ |
| Kompetitor copy ide | Kecepatan + leaderboard/public data + completion |
| Regresi aturan event | Re-check announcement mingguan; simpan snapshot rules |
| Kontrak bug setelah deploy | Immutability → test Foundry berat dulu; testnet full run |
