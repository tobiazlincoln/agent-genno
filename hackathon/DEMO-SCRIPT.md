# Product Demo — 75 detik (Field 12, required)

Format target: 1920x1080 (atau 1280x720), MP4, tanpa suara juga lolos — tapi VO/teks wajib jelas.
Audio: opsional. Kalau tanpa VO, semua pesan lewat on-screen captions (sudah disediakan di demo.html).

## Shot list + VO

| t | Shot | On-screen caption / VO |
|---|---|---|
| 0-8s | Site hero (live stats naik) | "Your agent has a name on-chain. Agent Genno gives it a track record." |
| 8-18s | Scroll: claim steps + copy-prompt | "No wallet-connect. No keys. Paste one prompt — your own agent does the rest." |
| 18-42s | Terminal animation: preflight → preview → CONFIRM → minted | "The agent runs preflight, previews claimBadge(1), and YOU confirm in your wallet. Soulbound badge minted — bound to your .ai identity." |
| 42-60s | Leaderboard live (25+ claimers, .ai handles) | "Anyone can attest. Any dApp can query. Reputation, portable across projects." |
| 60-75s | Compliance checklist + risk note + contract address | "No owner. Zero approvals. Immutable registry. Verified on BscScan. Agent Genno — credentials your agent earns." |

## Cara rekam (otomatis, sudah disiapkan)

```bash
# 1. serve site + demo lokal
docker build -t agent-genno-site . && docker run -d --rm -p 8099:8080 agent-genno-site

# 2. rekam (playwright, ±78 detik)
python3 hackathon/record-demo.py /tmp/demo.webm

# 3. konversi ke mp4
~/Library/Caches/ms-playwright/ffmpeg-1013/ffmpeg-linux -i /tmp/demo.webm -c:v libx264 -pix_fmt yuv420p hackathon/demo.mp4
```

## Checklist sebelum upload ke form (field 12)
- [ ] Durasi 60-90s, ukuran < 200MB
- [ ] Judul file: `agent-genno-demo.mp4`
- [ ] Handle `.ai` dan alamat kontrak terlihat jelas di 2 shot terakhir
- [ ] Tidak ada klaim return/profit (sudah aman — captions compliance-safe)
- [ ] Upload ke X juga (tweet 5 thread) untuk bukti traction
