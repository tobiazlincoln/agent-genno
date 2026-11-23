// Crops letterbox bars and converts scene stills to WebP. Run: npm run assets
import sharp from 'sharp';
const SRC = '../../asset', OUT = 'public/media';
const rowMean = (d, w, h, ch, y) => { let s = 0; for (let x = 0; x < w; x++) s += d[(y * w + x) * ch]; return s / w; };
for (const n of [2, 3, 4, 5, 6]) {
  const img = sharp(`${SRC}/${n}.jpg`);
  const { data, info } = await img.clone().greyscale().raw().toBuffer({ resolveWithObject: true });
  const { width: w, height: h, channels: ch } = info;
  let top = 0, bottom = h;
  while (top < h / 4 && rowMean(data, w, h, ch, top) < 12) top++;
  while (bottom > h * 0.75 && rowMean(data, w, h, ch, bottom - 1) < 6) bottom--;
  const crop = [2, 3].includes(n) && top > 4; // only 2 and 3 have letterbox bars; 4 and 6 have genuinely dark skies/vignettes
  const out = crop ? img.extract({ left: 0, top, width: w, height: bottom - top }) : img;
  const m = await out.resize({ width: 2560, withoutEnlargement: true }).webp({ quality: 82 }).toFile(`${OUT}/s${n}.webp`);
  console.log(`s${n}.webp  src ${w}x${h}  crop top ${top} bottom ${h - bottom}  ->  ${m.width}x${m.height}  ${(m.size / 1024) | 0} KB`);
}
// Video is compressed separately (14 MB -> 3 MB), run from chaff/web:
// node_modules\ffmpeg-static\ffmpeg.exe -i ..\..\asset\1.mp4 -an -c:v libx264 -preset slow -crf 28 -pix_fmt yuv420p -movflags +faststart public\media\s1.mp4
