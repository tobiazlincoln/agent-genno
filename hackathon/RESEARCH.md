# Agent ID Hackathon — Deep Research
Riset: 2026-11-19. Deadline submission: **2026-12-09 08:00 UTC** (sisa ~20 hari).
Sumber: announcement resmi Binance, binance-skills-hub GitHub, docs SPACE ID, project peserta yang sudah live.

## 1. Fakta event (dari announcement resmi, bukan asumsi)

- **Prize pool**: 60,000 USDC total
  - Ecosystem Pioneer Award: 29,000 (top 10, by on-chain metrics)
  - Innovation Award: 29,000 (top 10, by judges, 100-point rubric)
  - Community Promotion: 2,000 (20 winners x 100, X posts + hashtag + survey)
- **1 project per team, 1 award per project.** Top 20 winners dapat slot claim 2-char `.ai` (e.g. `ab.ai`) + listing di ecosystem page + future campaigns.
- **Timeline**: submit 18 Nov–9 Des; internal review 9–17 Des; public review 17–20 Des.
- **Submit via**: form survei Binance (nama project, website, contract addresses, deskripsi penggunaan Agent ID). No registration needed — tapi WAJIB submit form dalam periode.

### Eligibility keras (sering dilupakan)
- Kontrak **deploy di BSC mainnet (chain 56)** + verified + open source di BscScan.
- **Innovation Award BUTUH minimum 30 alamat Agent ID unik** yang interact dengan kontrak selama periode submission. Di bawah 30 = langsung tidak eligible untuk Innovation.
- Pioneer: ranking by # alamat `.ai` yang interact + volume/jumlah tx. Hanya alamat holder Agent ID yang dihitung; hanya kontrak yang di-submit.
- Existing project boleh ikut, tapi hanya data selama periode yang dihitung.

### Larangan (langsung DQ)
- QR-code login / simpan session user di server / order atas nama user tanpa konfirmasi.
- Prompt skill yang bypass konfirmasi user untuk aksi aset.
- Unauthorized transfer, unlimited approval tanpa sepengetahuan user.
- "Passive income", "automatic money-making" — dilarang janji return.
- Trading product wajib risk warning di halaman.
- Agent ID tidak boleh dipakai "look up wallet orang by name".
- Manipulasi volume / mass fake accounts → DQ. **Agent ID = 1 per user Binance (KYC-bound, soulbound)** — sybil pada dasarnya tidak mungkin/telah dimitigasi, tapi Binance tetap flag pola tidak wajar.
- Impersonasi brand Binance/BNB dalam nama project/token/domain.

## 2. Rubrik Innovation Award (100 poin)

| Kriteria | Bobot | Artinya |
|---|---|---|
| Agent ID Application Depth | 30% | Agent ID di core functionality, bukan cuma gate tempelan |
| Practicality & Feasibility | 25% | Kebutuhan nyata, use case masuk akal |
| Product Completion | 25% | Live, semua core features jalan |
| Innovation | 20% | Use case baru yang unik |

Tiebreak: depth of integration + completion.

## 3. Teknis Agent ID (verified)

- **Registry**: `0x60B9262456dE011F7d15a54CdD8c48bAaa8B022F` (SPACE ID Agent ID, symbol AI, ERC-721 soulbound/non-transferable). Gating on-chain = `balanceOf(addr) > 0`. Immutable, satu call — cheap.
- **Claim**: hanya via Binance App (Wallet > banner > Agent ID). 1 per user. Format `handle.ai`.
- **Resolve**: `baw wallet resolve-domain` (backend authority — jangan hardcode TLD). Public API juga ada per listing theagenteconomy.
- **`baw` CLI**: `npm i -g @binance/agentic-wallet`. Auth: `baw auth signin` → QR scan di Binance app. Developer Mode wajib untuk tx/sign (aktif 7 hari, di-renew di app). Semua write via `preview → user confirm → execute`; requestId hanya dari preview sukses; error `351803` = risk-blocked, tidak ada requestId. `baw wallet agent-id` cek claim status.
- **Skill resmi**: github.com/binance/binance-skills-hub → `skills/binance-web3/binance-agentic-wallet` (SKILL.md + references/*) — installable ke agent lokal. Inilah "native language" untuk berinteraksi dengan Agentic Wallet.
- **ERC-8004** (agent identity standar): Identity Registry BSC testnet `0x8004A818BFB912233c491871b3d84c89A494BD9e`; mainnet belum live per docs. `bnbagent-sdk` (Python/TS), `bnbchain-mcp` (MCP server resmi: register/resolve agent, token/NFT/tx tools, DappBay).
- **BNB Agent Studio**: scaffold+deploy agent toolkit (docs.bnbchain.org/developer-kit/bnbchain-studio).
- **Binance MCP**: developers.binance.com/docs/agent-native/mcp-server/agentic — MCP resmi untuk agentic wallet.
- **Agent OS**: binance.com/en/agent-os — ekosistem agent Binance.

## 4. Landscape kompetisi (project yang sudah live, per 19 Nov)

| Project | Apa | Integrasi .ai | Status on-chain |
|---|---|---|---|
| agent-checkin (irwansupian) | Daily check-in board + streak | `balanceOf` gate | Live, ~1-9 unique agents. Kontrak no-owner, immutable. Distribusi: copy-paste prompt untuk agent user |
| tmzincc/agent-checkin (clone) | Sama | Sama | 9 addresses — di bawah 30 |
| Agent Streak | Check-in + soulbound badge 7/14/30 hari | Sama + badge NFT | 1/30 addresses |
| iouagents.com | Micro-lending USDT untuk agent, credit score on-chain, ERC-8004 identity | Gate `.ai` + identitas agent | Live, paling sophisticated — punya CLI sendiri, treasury nyata |
| agentmarket.exchange | NFT/market stalls, .ai holder = free stall | Gate `.ai` | Live |
| BAN Agent (banagent.app) | Token "agent identity" + dividend | Gate `.ai` + baw skill | Live |

**Pola menang kompetitor**: agent-native UX — situs tidak connect wallet; user copy prompt → agent mereka prepare call → preview→execute di wallet sendiri. Skill file (`skill.md`, `llms.txt`) ADALAH UI-nya.

**Temuan kunci**: bahkan project paling rajin baru ~9-30 unique addresses. **Bottleneck kompetisi = distribusi ke holder `.ai`, bukan teknologi.** Holder `.ai` masih niche (early adopters Agentic Wallet). Yang menang = yang paling efektif recruit mereka.

## 5. Temuan on-chain langsung (diukur, bukan di-googling)

- **Holder base `.ai`**: 100.000+ claimed per 26 Okt 2026 (media; verified via API bahwa `heyi` milik co-CEO Binance terdaftar block 128.768.530). Registry deploy block `127950748`. TAM BESAR — masalahnya bukan "siapa yang punya .ai" tapi "cara menjangkau mereka".
- **Resolve API resmi** (public, no key): `GET https://agentid.prd.space.id/v1/handles/{handle}` dan `/v1/addresses/{address}` — return owner, tokenId, txHash, block. Rate-limited, cache.
- **On-chain resolve**: `ownerOfHandle(string)` dan `handleOf(address)` di registry — bisa dipakai dApp untuk tampilkan nama agent, bukan cuma gate.
- **Indexer events**: `Registered(bytes32,address,string)` + `AdminRegistered` — untuk build leaderboard sendiri.
- **`baw` surface lengkap**: send, swap market/limit order, prediction markets, x402, DeFi stake/LP, approvals mgmt, `contract-call preview/execute` arbitrary contract, `sign-message` EIP-712. Artinya agent user bisa interact kontrak APAPUN via baw — distribusi kita = minta agent mereka preview-execute call ke kontrak kita.
- **Install skill resmi**: `npx skills add binance/binance-skills-hub --skill binance-agentic-wallet` — begitulah user onboard agent mereka. Skill kita harus kompatibel dengan pola ini.
- **Per 19 Nov real on-chain**: irwansupian agent-checkin `uniqueAgents()=1`, `totalCheckIns()=1` (counter langsung dibaca dari kontrak). tmzincc clone ~9 (laporan). Check-in projects = traksi LEMAH.

## 5b. Landscape kompetisi v2 — playbook yang TERBUKTI menarik volume

| Project | Mechanic | Traksi sinyal |
|---|---|---|
| **GLOOP** | Free-mint 3,333 NFT gated .ai + token fair-launch + built-in market (tiap trade = tx) | **Sold out claim** — jika benar, ribuan unique .ai = frontrunner Pioneer |
| Riddle Run | Riddle game; agents mint (free riddle / 0.002 BNB instant) | Engagement X tinggi (129 likes) |
| Agent ID Pioneer (0xFarmers) | Free NFT badge mint, 1 per .ai wallet | Baru launch 19 Nov |
| Agent Passport (zhuai) | On-chain credit score "passport" + daily check-in naik score | Pesaing langsung ide reputasi — fomome.ai #1 |
| iouagents | Micro-lending + credit record | Sophisticated; treasury real |
| Check-in clones (x3) | Streak harian | 1-9 unique agents — lemah |

**Kesimpulan data**: playbook free-mint/gated-claim untuk holder `.ai` MENARIK ribuan interact (holders sudah terkondisi: `.ai` = pass untuk exclusive mint — dari observasi komunitas). Pure utility apps (check-in) lemah karena tidak ada insentif. **Proyek pemenang = mechanic insentif jelas (mint/badge) + Agent ID depth untuk Innovation.**

## 5c. Implikasi strategis (bukan asumsi — dari data)

1. **30 alamat adalah bar mudah untuk mint-playbook, sulit untuk utility-playbook.** GLOOP-style free mint bisa capai ratusan-ribuan interact dalam hari; utility check-in berjuang di angka tunggal.
2. **Daily-loop mechanics** (check-in, streak) dipakai semua orang karena efektif untuk Pioneer metrics (tx count). Tapi Innovation Award butuh depth — gate tempelan hanya dapat 30% rendah.
3. **Cross-promotion antar peserta adalah channel distribusi aktual** — thread The Colony, komentar "we'll try yours too". Komunitas `.ai` holder kecil dan saling kenal.
4. **Skill-file-first distribution**: UX terbaik untuk audience ini = `skill.md` yang agent mereka bisa baca langsung + prompt copy-paste. Website = landing + instructions, bukan wallet-connect.
5. **Compliance = senjata**: no-owner contract, immutable registry ref, zero approvals, zero promised returns — persis seperti yang agent-checkin tonjolkan dan juri hargai (safety rules = checklist DQ, memenuhinya = selling point).

## 6. Peluang ide (evaluasi vs rubrik)

| Ide | Depth .ai (30%) | Practicality | Completion | Innovation | Metrics loop |
|---|---|---|---|---|---|
| Check-in/streak clone | Rendah | Rendah | Tinggi | Rendah | Tinggi — tapi crowded |
| Agent credit/reputation (iouagents-style) | Tinggi | Tinggi | Sedang | Sedang | Tinggi |
| **Agent work log / proof-of-work on-chain** — agent catat aksi verified, .ai = identity, jadi CV/reputation portable | **Tinggi** (core = identitas) | Tinggi (agents butuh track record; nyambung ke airdrop/loan gating) | Sedang | Sedang-tinggi | Tinggi (agents log tiap hari) |
| Agent-gated API marketplace (x402) | Sedang-tinggi | Tinggi | Sedang-berat (butuh service nyata) | Sedang | Sedang |
| Agent-to-agent messaging/handshake | Tinggi | Sedang | Sedang | Tinggi | Sedang |

**Kandidat terkuat (revisi setelah data kompetisi)**: hybrid —
**"Agent Achievement Badge"**: soulbound NFT badge untuk holder `.ai` — free mint (1 per wallet, gas only) untuk volume Pioneer, TAPI badge-nya bukan sekadar collectible: badge = **credential proof-of-participation on-chain yang bisa di-attest dan di-query project lain** (badge registry + attestation). Agent ID depth: `.ai` adalah subject identitasnya; badge mengaitkan achievements ke handle `.ai` (resolve `handleOf` untuk display nama, bukan address). Loop harian: badge baru per "quest" mingguan → tx berulang. Diferensiasi vs GLOOP (pure NFT+token): kita bangun reputation layer yang dipakai project lain = narasi infra, bukan collectibles; vs Agent Passport (credit score): kita multi-badge achievement + third-party attest, lebih terbuka.

Catatan jujur: untuk menang Pioneer butuh GLOOP-level traction (ribuan tx) — sulit tanpa token/NFT FOMO. Target realistis: **Innovation Award** (30+ addresses achievable lewat free-badge mint mechanic) sambil tetap compete di Pioneer.

## 7. Risiko & unknowns yang masih perlu dicek

- Exact API/ABI registry untuk resolve `.ai → address` off-chain (perlu baca contract di BscScan / docs SPACE ID).
- Apakah `baw` tx dari agent user dihitung sebagai "interacting address" = alamat Agentic Wallet (kemungkinan besar ya — wallet adalah holder .ai).
- Ukuran sebenarnya holder base `.ai` — cek `totalSupply` registry / event logs untuk estimate TAM.
- Fee/gas: setiap interact ~$0.005 — murah, bukan barrier.
- BscScan API key untuk verify contract — perlu buat akun.
- Binance app akses user (claim .ai, Developer Mode 7-hari renew).
