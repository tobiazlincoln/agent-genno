# Chaff landing — prompt scene (gaya noir / shadow illustration, post-apokaliptik robotik)

**Scene 1 = video. Scene 2–7 = gambar statis** yang dianimasikan di web dengan zoom dan gerak kamera. Tiap blok sudah lengkap (style + cast + inti + negative): **copy satu blok penuh per scene**. Kolom negative terpisah? Pindahkan baris NEGATIVE ke sana.

## Aturan agar zoom di web mulus

1. Titik zoom tiap gambar (lensa, air, bulan, kerumunan, hatch) **harus tepat di tengah frame**. Ini sudah ditulis di prompt sebagai IMPORTANT.
2. Generate gambar resolusi tertinggi yang tersedia (minimal 2560×1440), karena zoom sampai 1.9× akan mengambil bagian tengah saja.
3. Frame terakhir video scene 1 (orb memenuhi layar) jadi dasar crossfade ke scene 2. Gambar scene 2 sebaiknya diberi referensi gambar scene 1 jika model mendukung.
4. Jika gambar sudah dibuat: upload ulang bersama prompt dan tambahkan `Keep the exact look, characters and composition of the reference.` bila hanya perlu penyesuaian.
5. Opsional untuk parallax: minta tiap gambar dipisah jadi 2–3 layer (background, tengah, foreground) lewat editor/AI cutout. Tanpa layer pun zoom + pan tetap jalan.

## Peta layout (berlaku untuk semua scene, desktop 16:9)

```
┌──────────────────────────────────────────────┐
│ CHAPTER (kiri atas)   LOGO (tengah)  SOUND EN│  y 0–12%   strip HUD, gambar harus gelap
│                                          │ V │
│              ZONA FOKUS ZOOM             │ E │  kolom teks vertikal: x 82–94%, y 15–80%
│              (lingkaran tengah,          │ R │
│               radius ±18%)               │ T │
│ 01/07                                    │   │  counter: kiri 22% x bawah 25%
└──────────────────────────────────────────────┘
```
- Teks adalah overlay HTML (tidak ikut di-zoom), jadi area teks pada gambar harus tenang dan gelap agar terbaca. Teks putih; tambahkan gradien hitam 30% di tepi bila perlu.
- **Mobile (portrait):** gambar di-crop tengah (hanya ±34–40% lebar yang terlihat), jadi semua objek penting dikunci di 40% tengah. Di mobile teks vertikal pindah jadi teks horizontal di bawah, counter di atas.
- Prompt tiap scene sudah memuat TEXT-SAFE COMPOSITION dan penempatan subjeknya. Model gambar tidak selalu patuh; cek hasilnya terhadap peta ini, dan bila meleset, geser dengan outpainting atau crop.

## Cast tetap (tempel di awal prompt jika karakter mulai melenceng)

```
Recurring cast (keep identical in every scene): THE COURIER = a small semi-robotic AI agent in a long tattered hooded cloak, black silhouette, slim segmented limbs and exposed mechanical frame visible at the hands and neck, one thin glowing cold-blue visor slit instead of a face, trailing cables and a pale-grey cloth strip blowing like a scarf, always carrying THE ORB = a softly glowing amber sphere with swirling inner texture like a small planet; THE WATCHER = a colossal derelict surveillance machine shaped like a giant head, grey stippled metal, cracked casing, hanging cables, two large round camera lenses like glasses that reflect scenes like mirrors, half-buried in ruins; HUSKS = small identical scrap-drone decoys like paper-thin moths, each with a dim amber glimmer.
```

## Scene 1 — PROLOGUE: Satu pembayaran — VIDEO 6 s

```
Dark noir shadow illustration, hand-drawn ink and stipple engraving look with heavy film grain and soft noise gradients, mostly pure black and charcoal with white-grey stippled highlights, flat silhouettes against misty glowing haze, deep midnight-blue moonlight as the only cool tone (#0B1F4A), and ONE warm amber glowing orb (#FFB347) as the only warm color in the frame, cinematic 16:9, 2.5D parallax depth, slow smooth camera push-in, layered foreground and background depth, post-apocalyptic ruined futuristic megacity: collapsed skyscrapers, broken elevated highways, dead antenna towers, faint flickering holographic remnants in cold blue, exposed cables and circuitry drawn in ink and stipple, modern sci-fi machinery worn and abandoned, subtle floating dust specks, quiet melancholic mood, hand-painted look, no text, no logos.

Recurring cast (keep identical in every scene): THE COURIER = a small semi-robotic AI agent in a long tattered hooded cloak, black silhouette, slim segmented limbs and exposed mechanical frame visible at the hands and neck, one thin glowing cold-blue visor slit instead of a face, trailing cables and a pale-grey cloth strip blowing like a scarf, always carrying THE ORB = a softly glowing amber sphere with swirling inner texture like a small planet; THE WATCHER = a colossal derelict surveillance machine shaped like a giant head, grey stippled metal, cracked casing, hanging cables, two large round camera lenses like glasses that reflect scenes like mirrors, half-buried in ruins; HUSKS = small identical scrap-drone decoys like paper-thin moths, each with a dim amber glimmer.

SCENE: Wide establishing shot at night: a long collapsed elevated highway with broken pillars and ruined skyscraper silhouettes fading into mist, midnight-blue moonlight and faint dead holograms. THE COURIER walks small and alone along the broken road carrying THE ORB, its amber glow lighting the cracked asphalt. Slow push-in following the courier, parallax mist. Final 1.5 seconds: camera zooms smoothly into THE ORB until its glowing surface fills the entire frame.

TEXT-SAFE COMPOSITION: keep the top 12% strip, the bottom-left corner (left 22% by bottom 25%) and a right-side vertical column (x 82% to 94%, y 15% to 80%) as calm, dark, low-detail areas with no bright shapes, because UI text will be overlaid there. Keep the main subject and focal point centered; keep every key element inside the central 40% of the frame width so it survives a portrait phone crop. Upper-center 30% of the frame is empty misty sky for the title. THE COURIER is small at x 30-45%, y 60-75%. Horizon low.

NEGATIVE: photorealistic, 3D render, CGI, glossy plastic, neon, bright saturated colors, rainbow, clean pristine sci-fi, bright daylight cityscape, anime face details, detailed human faces, text, letters, numbers, watermark, logo, flicker, jump cut, morphing artifacts, camera shake, camera moving backward, bright white background
```

**Teks web:** Chapter "PROLOGUE", "01/07". Teks vertikal: "Satu pembayaran, satu jejak." Judul "Chaff" kecil di tengah atas.

**Penempatan teks:** Judul 'Chaff' besar di tengah atas (y 18–30%), teks vertikal di kolom kanan. Kurir di kiri-tengah.

**Gerak kamera di web:** Video di-scrub oleh scroll. Poster = frame pertama (tampil saat loading).

## Scene 2 — THE WATCHER: Semua terlihat — GAMBAR

```
Dark noir shadow illustration, hand-drawn ink and stipple engraving look with heavy film grain and soft noise gradients, mostly pure black and charcoal with white-grey stippled highlights, flat silhouettes against misty glowing haze, deep midnight-blue moonlight as the only cool tone (#0B1F4A), and ONE warm amber glowing orb (#FFB347) as the only warm color in the frame, single still frame, cinematic 16:9 composition, layered foreground and background depth, post-apocalyptic ruined futuristic megacity: collapsed skyscrapers, broken elevated highways, dead antenna towers, faint flickering holographic remnants in cold blue, exposed cables and circuitry drawn in ink and stipple, modern sci-fi machinery worn and abandoned, subtle floating dust specks, quiet melancholic mood, hand-painted look, no text, no logos.

Recurring cast (keep identical in every scene): THE COURIER = a small semi-robotic AI agent in a long tattered hooded cloak, black silhouette, slim segmented limbs and exposed mechanical frame visible at the hands and neck, one thin glowing cold-blue visor slit instead of a face, trailing cables and a pale-grey cloth strip blowing like a scarf, always carrying THE ORB = a softly glowing amber sphere with swirling inner texture like a small planet; THE WATCHER = a colossal derelict surveillance machine shaped like a giant head, grey stippled metal, cracked casing, hanging cables, two large round camera lenses like glasses that reflect scenes like mirrors, half-buried in ruins; HUSKS = small identical scrap-drone decoys like paper-thin moths, each with a dim amber glimmer.

SCENE: The colossal derelict surveillance head THE WATCHER rising from ruins, centered, staring down at the viewer. Its two large round lenses reflect tiny images of THE COURIER carrying THE ORB and thin data lines drawn between them like a web. Collapsed towers behind, a faint cold-blue scanning beam. Menacing but quiet. IMPORTANT: the LEFT lens must be clearly centered in the frame and contain a bright amber reflection, because the web zooms into the exact center.

TEXT-SAFE COMPOSITION: keep the top 12% strip, the bottom-left corner (left 22% by bottom 25%) and a right-side vertical column (x 82% to 94%, y 15% to 80%) as calm, dark, low-detail areas with no bright shapes, because UI text will be overlaid there. Keep the main subject and focal point centered; keep every key element inside the central 40% of the frame width so it survives a portrait phone crop. THE WATCHER fills the center 50% of the width; ruins and darkness on the far left and far right edges.

NEGATIVE: photorealistic, 3D render, CGI, glossy plastic, neon, bright saturated colors, rainbow, clean pristine sci-fi, bright daylight cityscape, anime face details, detailed human faces, text, letters, numbers, watermark, logo, motion blur, multiple panels, comic frame border, bright white background
```

**Teks web:** Chapter "WATCHER", "02/07". Teks vertikal: "Setiap transaksi meninggalkan jejak. Jumlah, waktu, dan pola bisa dicocokkan."

**Penempatan teks:** Teks vertikal di kolom kanan (gelap). Tidak ada teks di tengah (kepala Watcher).

**Gerak kamera di web:** Masuk: scale 1.35 → 1.0 (menjauh sedikit) dari amber. Selama scroll: pan lambat ke tengah + zoom 1.0 → 1.6, transform-origin di lensa kiri. Parallax: layer reruntuhan bergerak 0.3×, kepala 0.6×.

## Scene 3 — SPLIT: Pecah — GAMBAR

```
Dark noir shadow illustration, hand-drawn ink and stipple engraving look with heavy film grain and soft noise gradients, mostly pure black and charcoal with white-grey stippled highlights, flat silhouettes against misty glowing haze, deep midnight-blue moonlight as the only cool tone (#0B1F4A), and ONE warm amber glowing orb (#FFB347) as the only warm color in the frame, single still frame, cinematic 16:9 composition, layered foreground and background depth, post-apocalyptic ruined futuristic megacity: collapsed skyscrapers, broken elevated highways, dead antenna towers, faint flickering holographic remnants in cold blue, exposed cables and circuitry drawn in ink and stipple, modern sci-fi machinery worn and abandoned, subtle floating dust specks, quiet melancholic mood, hand-painted look, no text, no logos.

Recurring cast (keep identical in every scene): THE COURIER = a small semi-robotic AI agent in a long tattered hooded cloak, black silhouette, slim segmented limbs and exposed mechanical frame visible at the hands and neck, one thin glowing cold-blue visor slit instead of a face, trailing cables and a pale-grey cloth strip blowing like a scarf, always carrying THE ORB = a softly glowing amber sphere with swirling inner texture like a small planet; THE WATCHER = a colossal derelict surveillance machine shaped like a giant head, grey stippled metal, cracked casing, hanging cables, two large round camera lenses like glasses that reflect scenes like mirrors, half-buried in ruins; HUSKS = small identical scrap-drone decoys like paper-thin moths, each with a dim amber glimmer.

SCENE: Two giant segmented robotic hands with exposed cables cradling an ornate oval fluted basin of dark still water, tiny sparks around it, seen from slightly above. In the water float four glowing amber pearls of clearly different sizes, drifting apart. Black void around. IMPORTANT: the dark water in the exact center of the basin must be the largest calm area, because the web zooms into it.

TEXT-SAFE COMPOSITION: keep the top 12% strip, the bottom-left corner (left 22% by bottom 25%) and a right-side vertical column (x 82% to 94%, y 15% to 80%) as calm, dark, low-detail areas with no bright shapes, because UI text will be overlaid there. Keep the main subject and focal point centered; keep every key element inside the central 40% of the frame width so it survives a portrait phone crop. The robotic hands stay within x 10% to 80%; the right-side column stays black void.

NEGATIVE: photorealistic, 3D render, CGI, glossy plastic, neon, bright saturated colors, rainbow, clean pristine sci-fi, bright daylight cityscape, anime face details, detailed human faces, text, letters, numbers, watermark, logo, motion blur, multiple panels, comic frame border, bright white background
```

**Teks web:** Chapter "SPLIT", "03/07". Teks vertikal: "Satu pembayaran dipecah 3–5 bagian. Ukuran acak, tidak bulat. Total tetap persis."

**Penempatan teks:** Teks vertikal di kolom kanan (void hitam). Angka '3–5' besar boleh di kiri-atas di bawah chapter (y 18–30%).

**Gerak kamera di web:** Masuk: crossfade dari scene 2 sambil scale 0.8 → 1.0. Scroll: zoom 1.0 → 1.7 menuju pusat air; mutiara (layer terpisah, opsional) bergeser pelan menjauh satu sama lain.

## Scene 4 — DELAY: Tunda — GAMBAR

```
Dark noir shadow illustration, hand-drawn ink and stipple engraving look with heavy film grain and soft noise gradients, mostly pure black and charcoal with white-grey stippled highlights, flat silhouettes against misty glowing haze, deep midnight-blue moonlight as the only cool tone (#0B1F4A), and ONE warm amber glowing orb (#FFB347) as the only warm color in the frame, single still frame, cinematic 16:9 composition, layered foreground and background depth, post-apocalyptic ruined futuristic megacity: collapsed skyscrapers, broken elevated highways, dead antenna towers, faint flickering holographic remnants in cold blue, exposed cables and circuitry drawn in ink and stipple, modern sci-fi machinery worn and abandoned, subtle floating dust specks, quiet melancholic mood, hand-painted look, no text, no logos.

Recurring cast (keep identical in every scene): THE COURIER = a small semi-robotic AI agent in a long tattered hooded cloak, black silhouette, slim segmented limbs and exposed mechanical frame visible at the hands and neck, one thin glowing cold-blue visor slit instead of a face, trailing cables and a pale-grey cloth strip blowing like a scarf, always carrying THE ORB = a softly glowing amber sphere with swirling inner texture like a small planet; THE WATCHER = a colossal derelict surveillance machine shaped like a giant head, grey stippled metal, cracked casing, hanging cables, two large round camera lenses like glasses that reflect scenes like mirrors, half-buried in ruins; HUSKS = small identical scrap-drone decoys like paper-thin moths, each with a dim amber glimmer.

SCENE: Night sky over an endless misty wasteland of rusted towers and dead pylons. Four separate amber orbs on four different winding paths across the land, each with a faint amber trail, small courier-agent silhouettes walking beside them. Giant thin concentric rings of satellites and stars overhead like a clock, a large pale moon low in the center of the frame. IMPORTANT: the pale moon must be centered and large, because the web zooms into it.

TEXT-SAFE COMPOSITION: keep the top 12% strip, the bottom-left corner (left 22% by bottom 25%) and a right-side vertical column (x 82% to 94%, y 15% to 80%) as calm, dark, low-detail areas with no bright shapes, because UI text will be overlaid there. Keep the main subject and focal point centered; keep every key element inside the central 40% of the frame width so it survives a portrait phone crop. Pale moon centered; the sky above and to the right is dark and nearly empty; landscape confined to the lower 35%.

NEGATIVE: photorealistic, 3D render, CGI, glossy plastic, neon, bright saturated colors, rainbow, clean pristine sci-fi, bright daylight cityscape, anime face details, detailed human faces, text, letters, numbers, watermark, logo, motion blur, multiple panels, comic frame border, bright white background
```

**Teks web:** Chapter "DELAY", "04/07". Teks vertikal: "Ditunda 1–72 jam. Setiap bagian berjalan sendiri."

**Penempatan teks:** Teks vertikal di kolom kanan (langit gelap). Jam/hitung mundur '1–72 jam' kecil di kiri-atas.

**Gerak kamera di web:** Scroll: pan horizontal pelan (translateX ±4%) + zoom 1.0 → 1.8 menuju bulan. Cincin bintang (layer terpisah, opsional) berputar mengikuti scroll.

## Scene 5 — CHAFF: Sekam — GAMBAR

```
Dark noir shadow illustration, hand-drawn ink and stipple engraving look with heavy film grain and soft noise gradients, mostly pure black and charcoal with white-grey stippled highlights, flat silhouettes against misty glowing haze, deep midnight-blue moonlight as the only cool tone (#0B1F4A), and ONE warm amber glowing orb (#FFB347) as the only warm color in the frame, single still frame, cinematic 16:9 composition, layered foreground and background depth, post-apocalyptic ruined futuristic megacity: collapsed skyscrapers, broken elevated highways, dead antenna towers, faint flickering holographic remnants in cold blue, exposed cables and circuitry drawn in ink and stipple, modern sci-fi machinery worn and abandoned, subtle floating dust specks, quiet melancholic mood, hand-painted look, no text, no logos.

Recurring cast (keep identical in every scene): THE COURIER = a small semi-robotic AI agent in a long tattered hooded cloak, black silhouette, slim segmented limbs and exposed mechanical frame visible at the hands and neck, one thin glowing cold-blue visor slit instead of a face, trailing cables and a pale-grey cloth strip blowing like a scarf, always carrying THE ORB = a softly glowing amber sphere with swirling inner texture like a small planet; THE WATCHER = a colossal derelict surveillance machine shaped like a giant head, grey stippled metal, cracked casing, hanging cables, two large round camera lenses like glasses that reflect scenes like mirrors, half-buried in ruins; HUSKS = small identical scrap-drone decoys like paper-thin moths, each with a dim amber glimmer.

SCENE: A foggy field filled with hundreds of identical small scrap-drone HUSKS drifting in the wind, each carrying a dim amber glimmer, so four real orbs are indistinguishable from the swarm. THE WATCHER's cold scanning beam crosses the field from the upper left and fades into nothing. IMPORTANT: the densest cluster of glimmers must be in the exact center of the frame, because the web zooms into it.

TEXT-SAFE COMPOSITION: keep the top 12% strip, the bottom-left corner (left 22% by bottom 25%) and a right-side vertical column (x 82% to 94%, y 15% to 80%) as calm, dark, low-detail areas with no bright shapes, because UI text will be overlaid there. Keep the main subject and focal point centered; keep every key element inside the central 40% of the frame width so it survives a portrait phone crop. Densest glimmers at the exact center; fog and darkness at the right column; the bottom-center strip (y 85-95%, x 30-70%) stays calm and dark.

NEGATIVE: photorealistic, 3D render, CGI, glossy plastic, neon, bright saturated colors, rainbow, clean pristine sci-fi, bright daylight cityscape, anime face details, detailed human faces, text, letters, numbers, watermark, logo, motion blur, multiple panels, comic frame border, bright white background
```

**Teks web:** Chapter "CHAFF", "05/07". Teks vertikal: "Di tengah keramaian, tak ada yang bisa dipelajari di atas kebetulan." Catatan kecil: "Diukur 2026-11-22, 3 minggu data pool (8.996 tx)." Jangan klaim mengalahkan analisis agregat (gate K1 FAIL, lihat chaff/README.md).

**Penempatan teks:** Teks vertikal di kolom kanan; catatan kecil data pool di strip bawah-tengah.

**Gerak kamera di web:** Scroll: zoom 1.0 → 1.8 ke pusat kerumunan. Sekam (layer PNG terpisah) hanyut pelan dengan CSS sehingga terasa hidup tanpa video.

## Scene 6 — ARRIVE: Tiba — GAMBAR

```
Dark noir shadow illustration, hand-drawn ink and stipple engraving look with heavy film grain and soft noise gradients, mostly pure black and charcoal with white-grey stippled highlights, flat silhouettes against misty glowing haze, deep midnight-blue moonlight as the only cool tone (#0B1F4A), and ONE warm amber glowing orb (#FFB347) as the only warm color in the frame, single still frame, cinematic 16:9 composition, layered foreground and background depth, post-apocalyptic ruined futuristic megacity: collapsed skyscrapers, broken elevated highways, dead antenna towers, faint flickering holographic remnants in cold blue, exposed cables and circuitry drawn in ink and stipple, modern sci-fi machinery worn and abandoned, subtle floating dust specks, quiet melancholic mood, hand-painted look, no text, no logos.

Recurring cast (keep identical in every scene): THE COURIER = a small semi-robotic AI agent in a long tattered hooded cloak, black silhouette, slim segmented limbs and exposed mechanical frame visible at the hands and neck, one thin glowing cold-blue visor slit instead of a face, trailing cables and a pale-grey cloth strip blowing like a scarf, always carrying THE ORB = a softly glowing amber sphere with swirling inner texture like a small planet; THE WATCHER = a colossal derelict surveillance machine shaped like a giant head, grey stippled metal, cracked casing, hanging cables, two large round camera lenses like glasses that reflect scenes like mirrors, half-buried in ruins; HUSKS = small identical scrap-drone decoys like paper-thin moths, each with a dim amber glimmer.

SCENE: A quiet cliff path at dawn-blue night. A small sealed bunker hatch in a ruined concrete wall, lit by one dim status light, the hatch slightly open with a steady amber glow inside. THE COURIER stands at the side, small, finished. Faint husks fading into mist behind. IMPORTANT: the glowing hatch opening must be in the exact center of the frame, because the web zooms into it.

TEXT-SAFE COMPOSITION: keep the top 12% strip, the bottom-left corner (left 22% by bottom 25%) and a right-side vertical column (x 82% to 94%, y 15% to 80%) as calm, dark, low-detail areas with no bright shapes, because UI text will be overlaid there. Keep the main subject and focal point centered; keep every key element inside the central 40% of the frame width so it survives a portrait phone crop. THE COURIER at x 28-40%, y 55-70%; glowing hatch at the exact center; dark concrete wall fills the right.

NEGATIVE: photorealistic, 3D render, CGI, glossy plastic, neon, bright saturated colors, rainbow, clean pristine sci-fi, bright daylight cityscape, anime face details, detailed human faces, text, letters, numbers, watermark, logo, motion blur, multiple panels, comic frame border, bright white background
```

**Teks web:** Chapter "ARRIVE", "06/07". Teks vertikal: "Tiba di penerima. Tanpa jejak yang mudah dicocokkan."

**Penempatan teks:** Teks vertikal di kolom kanan (dinding beton gelap).

**Gerak kamera di web:** Scroll: zoom 1.0 → 1.9 ke celah hatch yang bercahaya, lalu layar memutih-amber singkat (opacity overlay 0 → 0.6) sebagai jembatan ke scene 7.

## Scene 7 — AUTOPILOT: Agen & kebijakan — GAMBAR

```
Dark noir shadow illustration, hand-drawn ink and stipple engraving look with heavy film grain and soft noise gradients, mostly pure black and charcoal with white-grey stippled highlights, flat silhouettes against misty glowing haze, deep midnight-blue moonlight as the only cool tone (#0B1F4A), and ONE warm amber glowing orb (#FFB347) as the only warm color in the frame, single still frame, cinematic 16:9 composition, layered foreground and background depth, post-apocalyptic ruined futuristic megacity: collapsed skyscrapers, broken elevated highways, dead antenna towers, faint flickering holographic remnants in cold blue, exposed cables and circuitry drawn in ink and stipple, modern sci-fi machinery worn and abandoned, subtle floating dust specks, quiet melancholic mood, hand-painted look, no text, no logos.

Recurring cast (keep identical in every scene): THE COURIER = a small semi-robotic AI agent in a long tattered hooded cloak, black silhouette, slim segmented limbs and exposed mechanical frame visible at the hands and neck, one thin glowing cold-blue visor slit instead of a face, trailing cables and a pale-grey cloth strip blowing like a scarf, always carrying THE ORB = a softly glowing amber sphere with swirling inner texture like a small planet; THE WATCHER = a colossal derelict surveillance machine shaped like a giant head, grey stippled metal, cracked casing, hanging cables, two large round camera lenses like glasses that reflect scenes like mirrors, half-buried in ruins; HUSKS = small identical scrap-drone decoys like paper-thin moths, each with a dim amber glimmer.

SCENE: A quiet underground control chamber. A small calm robotic sentinel in the same cloaked style as THE COURIER (the autopilot) sits at a tall console with three controls: a switch, a round gauge, and a gate latch, faint blue holographic abstract glyphs only. One soft amber pulse leaves through the gate latch. Stable wide composition with empty dark space on the LEFT third of the frame for text.

TEXT-SAFE COMPOSITION: keep the top 12% strip, the bottom-left corner (left 22% by bottom 25%) and a right-side vertical column (x 82% to 94%, y 15% to 80%) as calm, dark, low-detail areas with no bright shapes, because UI text will be overlaid there. Keep the main subject and focal point centered; keep every key element inside the central 40% of the frame width so it survives a portrait phone crop. Console and sentinel sit at x 45% to 78%; the LEFT third (x 6-38%, y 28-75%) is an empty dark wall for a headline and buttons; the right column stays dark.

NEGATIVE: photorealistic, 3D render, CGI, glossy plastic, neon, bright saturated colors, rainbow, clean pristine sci-fi, bright daylight cityscape, anime face details, detailed human faces, text, letters, numbers, watermark, logo, motion blur, multiple panels, comic frame border, bright white background
```

**Teks web:** Chapter "AUTOPILOT", "07/07". Teks vertikal: "Kill switch. Batas harian. Daftar penerima." CTA: "Lihat daemon" / "Baca riset".

**Penempatan teks:** Headline besar + dua tombol CTA di sepertiga kiri (x 6–38%); teks vertikal tetap di kolom kanan; footer di strip bawah.

**Gerak kamera di web:** Masuk: scale 1.5 → 1.0 (kamera mundur dari dalam hatch, satu-satunya gerak mundur yang diizinkan). Lalu diam; hanya parallax mouse ±1% dan CTA fade-in.

## Layout scroll: zoom-through, bukan scroll ke bawah

- Satu layar penuh (fixed). Scroll/wheel/swipe tidak menggeser halaman; ia menggerakkan zoom dan pan gambar. GSAP ScrollTrigger (scrub) + Lenis.
- Perpindahan antar scene: gambar keluar `scale 1 → 1.9` sambil fade-out, gambar berikutnya fade-in `scale 0.8 → 1`. Karena titik zoom ada di tengah, terasa seperti masuk ke dalam objek.
- HUD tetap seperti referensi: chapter (kiri atas), logo (tengah), SOUND + EN (kanan atas), counter 01/07 besar (kiri bawah), teks vertikal (kanan) dengan `writing-mode: vertical-rl`, muncul huruf per huruf.
- Scroll di-snap per scene; tombol panah/keyboard juga berfungsi.

## Budget ukuran (supaya web ringan)

| aset | spesifikasi | perkiraan |
|---|---|---|
| Scene 1 video | 1080p, H.264, `-an`, `-g 1` | ≤ 6 MB (mobile 720p ≤ 3 MB) |
| Scene 2–7 gambar | WebP/AVIF 2560×1440, kualitas 75 | 200–400 KB tiap gambar |
| Total | | sekitar 8 MB, dimuat bertahap per scene |

```powershell
ffmpeg -i scene1.mp4 -an -c:v libx264 -g 1 -crf 24 -pix_fmt yuv420p -movflags +faststart scene1.web.mp4
```

## Musik (opsional, loop 90–120 dtk)

```
Dark ambient post-apocalyptic underscore, slow soft piano notes and distant strings, low synth drone, wind and faint machine hum, sparse bell tones, melancholic, no drums, no vocals, seamless loop.
```
Putar setelah klik "SOUND"; default volume 25–30%.
