// Chaff mascot as hand-built SVG: glossy hooded agent, 3D feel from gradients, highlights and soft shadows.
// Writes desain/logo/{chaff-logo.svg, chaff-mascot.svg, expressions/*.svg, png/*.png}. Run from chaff/web: node tools/logo.mjs
import sharp from 'sharp';
import { mkdirSync, writeFileSync } from 'node:fs';

const OUT = '../../desain/logo';
const S = 1024;

// geometry, traced from the approved render (1024 x 1024)
// hood: egg shape narrowing to a soft point at the bottom, with a fat peak that curls out and down at the upper left
const HOOD = 'M276 340 C278 292 340 262 412 256 C566 246 696 306 742 426 C778 512 770 594 724 664 C682 732 568 778 518 778 C468 778 354 732 312 664 C266 596 262 506 292 446 C302 424 314 404 334 388 C308 382 276 368 276 340 Z';
// face opening: shield shape, wide arched top, tapering to a soft point
const FACE = 'M366 438 C398 372 646 366 680 438 C706 490 696 566 664 624 C634 682 558 728 520 728 C482 728 406 682 376 624 C344 566 336 490 366 438 Z';

const W = '#FFFFFF';
const stroke = (d, w = 24) => `<path d="${d}" fill="none" stroke="${W}" stroke-width="${w}" stroke-linecap="round" stroke-linejoin="round"/>`;
const pill = (x, y, w, h) => `<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="${w / 2}" fill="${W}"/>`;

// eyes sit inside the face; extras sit outside the hood, upper right
const EXPRESSIONS = {
  '01-neutral': { eyes: pill(456, 486, 50, 118) + pill(600, 512, 44, 86) },
  '02-happy': { eyes: stroke('M440 566 Q476 506 512 566') + stroke('M588 566 Q624 506 660 566') },
  '03-sleepy': {
    eyes: stroke('M444 560 H512') + stroke('M590 560 H658'),
    extra: stroke('M718 318 H752 L718 352 H752', 12) + stroke('M772 244 H824 L772 296 H824', 15),
  },
  '04-suspicious': {
    eyes: '<path d="M438 548 H520 Q516 584 478 586 Q442 584 438 548 Z" fill="#fff"/><path d="M584 548 H666 Q662 584 624 586 Q588 584 584 548 Z" fill="#fff"/>',
  },
  '05-surprised': {
    eyes: '<circle cx="478" cy="556" r="38" fill="none" stroke="#fff" stroke-width="18"/><circle cx="624" cy="556" r="38" fill="none" stroke="#fff" stroke-width="18"/>',
    extra: '<rect x="770" y="214" width="22" height="70" rx="11" fill="#fff"/><circle cx="781" cy="312" r="13" fill="#fff"/>',
  },
  '06-sad': {
    eyes: stroke('M440 578 Q470 546 516 552') + stroke('M586 552 Q632 546 662 578'),
    extra: '<path d="M640 600 C640 600 662 628 662 644 A22 22 0 0 1 618 644 C618 628 640 600 640 600 Z" fill="#dbe8ff"/>',
  },
  '07-alert': {
    eyes: '<path d="M440 532 L522 566 L516 592 L446 576 Z" fill="#fff" stroke="#fff" stroke-width="10" stroke-linejoin="round"/><path d="M662 532 L580 566 L586 592 L656 576 Z" fill="#fff" stroke="#fff" stroke-width="10" stroke-linejoin="round"/>',
  },
  '08-thinking': {
    eyes: '<circle cx="476" cy="560" r="20" fill="#fff"/>' + pill(600, 500, 42, 114),
    extra: [[724, 306, 10], [752, 282, 11], [782, 264, 12], [814, 254, 12], [790, 296, 10]].map(([x, y, r]) => `<circle cx="${x}" cy="${y}" r="${r}" fill="#fff"/>`).join(''),
  },
  '09-error': { eyes: stroke('M450 530 L506 586 M506 530 L450 586', 22) + stroke('M596 530 L652 586 M652 530 L596 586', 22) },
};

function svg({ eyes, extra = '' }, withBg = true) {
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${S} ${S}" width="${S}" height="${S}">
  <title>Chaff mascot</title>
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#FF8418"/><stop offset="0.5" stop-color="#FF7A12"/><stop offset="1" stop-color="#DC2E0A"/>
    </linearGradient>
    <radialGradient id="bgGlow" cx="0.5" cy="0.4" r="0.55">
      <stop offset="0" stop-color="#FFB030" stop-opacity="0.95"/><stop offset="1" stop-color="#FFB030" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="hood" x1="0.12" y1="0.02" x2="0.82" y2="0.98">
      <stop offset="0" stop-color="#5E6B86"/><stop offset="0.32" stop-color="#2E3647"/><stop offset="1" stop-color="#0F131B"/>
    </linearGradient>
    <radialGradient id="hoodHi" cx="0.33" cy="0.2" r="0.5">
      <stop offset="0" stop-color="#fff" stop-opacity="0.32"/><stop offset="1" stop-color="#fff" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="rimIn" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#7C88A2"/><stop offset="0.45" stop-color="#2B3241"/><stop offset="1" stop-color="#3B4458"/>
    </linearGradient>
    <radialGradient id="face" cx="0.5" cy="0.64" r="0.62">
      <stop offset="0" stop-color="#030405"/><stop offset="1" stop-color="#13171F"/>
    </radialGradient>
    <linearGradient id="faceTop" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#000" stop-opacity="0.85"/><stop offset="0.36" stop-color="#000" stop-opacity="0"/>
    </linearGradient>
    <clipPath id="faceClip"><path d="${FACE}"/></clipPath>
    <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="20"/></filter>
    <filter id="soft" x="-10%" y="-10%" width="120%" height="120%"><feGaussianBlur stdDeviation="2.5"/></filter>
    <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur in="SourceGraphic" stdDeviation="10" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>
  ${withBg ? `<rect width="${S}" height="${S}" fill="url(#bg)"/><rect width="${S}" height="${S}" fill="url(#bgGlow)"/>` : ''}
  <path d="${HOOD}" transform="translate(6 26)" fill="#000" opacity="0.38" filter="url(#shadow)"/>
  <path d="${HOOD}" fill="url(#hood)" stroke="#090C12" stroke-width="10" stroke-linejoin="round"/>
  <path d="${HOOD}" fill="url(#hoodHi)"/>
  <path d="M334 374 C366 304 452 274 548 280" fill="none" stroke="#fff" stroke-opacity="0.28" stroke-width="13" stroke-linecap="round" filter="url(#soft)"/>
  <path d="M290 334 C300 300 344 280 396 276" fill="none" stroke="#fff" stroke-opacity="0.3" stroke-width="8" stroke-linecap="round" filter="url(#soft)"/>
  <path d="M708 452 C734 520 730 600 700 652" fill="none" stroke="#9AA6C0" stroke-opacity="0.18" stroke-width="10" stroke-linecap="round" filter="url(#soft)"/>
  <path d="${FACE}" fill="url(#face)" stroke="url(#rimIn)" stroke-width="12" stroke-linejoin="round"/>
  <g clip-path="url(#faceClip)">
    <path d="${FACE}" fill="url(#faceTop)"/>
    <path d="M350 454 Q522 426 700 454" fill="none" stroke="#353D4E" stroke-width="20"/>
    <path d="M352 445 Q522 417 698 445" fill="none" stroke="#7A8499" stroke-opacity="0.7" stroke-width="3"/>
  </g>
  <g filter="url(#glow)">${eyes}${extra}</g>
</svg>
`;
}

mkdirSync(`${OUT}/expressions`, { recursive: true });
mkdirSync(`${OUT}/expressions-transparent`, { recursive: true });
mkdirSync(`${OUT}/png`, { recursive: true });

const files = [];
const put = (path, body) => { writeFileSync(path, body); files.push(path); };
put(`${OUT}/chaff-logo.svg`, svg(EXPRESSIONS['01-neutral']));
put(`${OUT}/chaff-mascot.svg`, svg(EXPRESSIONS['01-neutral'], false));
for (const [name, e] of Object.entries(EXPRESSIONS)) {
  put(`${OUT}/expressions/${name}.svg`, svg(e));
  put(`${OUT}/expressions-transparent/${name}.svg`, svg(e, false));
}

// PNG exports (1024 px) and a contact sheet to check the set at a glance
const pngs = [];
for (const [name, e] of Object.entries(EXPRESSIONS)) {
  const buf = await sharp(Buffer.from(svg(e))).png().toBuffer();
  writeFileSync(`${OUT}/png/${name}.png`, buf);
  pngs.push(buf);
}
writeFileSync(`${OUT}/png/chaff-logo.png`, await sharp(Buffer.from(svg(EXPRESSIONS['01-neutral']))).png().toBuffer());
const cell = 340;
const sheet = await sharp({ create: { width: cell * 3, height: cell * 3, channels: 4, background: '#05070c' } })
  .composite(await Promise.all(pngs.map(async (b, i) => ({ input: await sharp(b).resize(cell - 20).toBuffer(), left: (i % 3) * cell + 10, top: Math.floor(i / 3) * cell + 10 }))))
  .png().toFile(`${OUT}/png/_sheet.png`);
console.log(`${files.length} SVG files, ${pngs.length + 1} PNG, sheet ${sheet.width}x${sheet.height}`);
