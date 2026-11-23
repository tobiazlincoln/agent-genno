// X (Twitter) header, 3:1. Bottom strip of asset 4, one tagline at the bottom, in orange.
// Run from chaff/web:  node tools/banner.mjs
import sharp from 'sharp';
import opentype from 'opentype.js';
import { readFileSync, mkdirSync } from 'node:fs';

const W = 1500, H = 500;
const SRC = '../../asset/4.jpg';
const OUT = '../../desain/banner/x-banner.png';
const TAGLINE = 'Privacy autopilot for AI agents on Solana.';
const ORANGE = '#FF9A2E';

const meta = await sharp(SRC).metadata();
const cropH = Math.round(meta.width / 3);                       // 3:1 strip from the full source width
const art = await sharp(SRC)
  .extract({ left: 0, top: meta.height - cropH, width: meta.width, height: cropH })   // bottom part only
  .resize(W, H, { kernel: 'lanczos3' })
  .toBuffer();

// text as vector outlines, so it does not depend on fonts installed on this machine
// Barlow in sentence case: upright for the first phrase, italic for the rest
const load = (f) => { const b = readFileSync(`node_modules/@fontsource/barlow/files/${f}`); return opentype.parse(b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength)); };
const upright = load('barlow-latin-500-normal.woff'), italic = load('barlow-latin-400-italic.woff');
const split = TAGLINE.indexOf(' for ');
const runs = [[TAGLINE.slice(0, split + 1), upright], [TAGLINE.slice(split + 1), italic]];
const size = 32, tracking = 0.4;
const adv = (font, ch) => (font.charToGlyph(ch).advanceWidth * size) / font.unitsPerEm + tracking;
const width = runs.reduce((w, [t, f]) => w + [...t].reduce((a, ch) => a + adv(f, ch), 0), 0) - tracking;
let x = (W - width) / 2;
const baseline = H - 44;
let d = '';
for (const [text, font] of runs) for (const ch of text) { d += font.charToGlyph(ch).getPath(x, baseline, size).toPathData(2); x += adv(font, ch); }

const overlay = Buffer.from(`<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}">
  <defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0.45" stop-color="#000" stop-opacity="0"/>
    <stop offset="1" stop-color="#000" stop-opacity="0.72"/></linearGradient></defs>
  <rect width="${W}" height="${H}" fill="url(#g)"/>
  <path d="${d}" fill="${ORANGE}"/>
</svg>`);

mkdirSync('../../desain/banner', { recursive: true });
const info = await sharp(art).composite([{ input: overlay }]).png().toFile(OUT);
console.log(`${OUT}  ${info.width}x${info.height}  ${(info.size / 1024) | 0} KB  (crop ${meta.width}x${cropH} from ${meta.width}x${meta.height})`);
