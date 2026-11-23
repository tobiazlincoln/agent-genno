import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import Lenis from 'lenis';

gsap.registerPlugin(ScrollTrigger);

// f = focal point (% of the image) that the zoom dives into. Each still was composed with it near the centre.
const SCENES = [
  { chapter: 'Prologue', video: '/media/s1.mp4', f: [50, 52],
    v: ['It carries one payment', 'and one trail that can be followed.'],
    extra: `<div class="title"><h1>Chaff</h1><p>Privacy autopilot for AI agents on Solana.</p></div>` },
  { chapter: 'Watcher', img: '/media/s2.webp', f: [49.5, 36],
    alt: 'The head of a ruined surveillance machine. In its central lens, a small courier holds a glowing amber orb.',
    v: ['On a public chain, every transaction is watched.', 'Amounts, timing and patterns can be matched.'] },
  { chapter: 'Split', img: '/media/s3.webp', f: [50, 46],
    alt: 'Two robot hands hold a basin of dark water with four amber pearls of different sizes.',
    tag: '3–5 parts',
    v: ['One payment is split into several parts', 'of random size. The total stays exact.'] },
  { chapter: 'Delay', img: '/media/s4.webp', f: [50, 53],
    alt: 'A ruined plain under a huge moon. Four couriers walk separate paths, each carrying an amber orb.',
    tag: '1–72 hours',
    v: ['Each part waits on its own,', 'among other people\u2019s transactions.'],
    note: 'Measured 2026-11-22 on 3 weeks of pool data (8,996 transactions): these parts carry no signal above chance. The K1 gate did not pass, so this claim is limited to that measurement.' },
  { chapter: 'Arrival', img: '/media/s5.webp', f: [52, 46],
    alt: 'A robot courier in a cloak holds an orb on a cliff, facing an open concrete bunker door glowing amber.',
    v: ['They meet again at the recipient address,', 'with no whole amount to match against.'] },
  { chapter: 'Autopilot', img: '/media/s6.webp', f: [50, 50],
    alt: 'A cloaked robot sentinel sits at an old console with a lever, a gauge and a gate latch in an underground room.',
    v: ['The agent works on its own,', 'within the limits you set.'],
    note: 'Kill switch, daily limit and recipient list.',
    cta: '<button class="btn btn--ca" id="ca" type="button"></button>' },
];

// Set this to the token's contract address at launch. While it is empty the button shows a dash and does nothing.
const CONTRACT = '';

const N = SCENES.length;
const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
const $ = (s) => document.querySelector(s);
const pad = (n) => String(n).padStart(2, '0');

/* ---------- build scenes ---------- */
const host = $('#scenes');
host.innerHTML = SCENES.map((s, i) => {
  const media = s.video
    ? `<video src="${s.video}" poster="/media/s1-poster.jpg" muted playsinline preload="auto" aria-hidden="true"></video>`
    : `<img src="${s.img}" alt="${s.alt}" decoding="async" />`;
  return `<article class="scene" data-i="${i}" aria-label="${pad(i + 1)} of ${pad(N)}: ${s.chapter}">
    <div class="scene__art" style="--fx:${s.f[0]}%;--fy:${s.f[1]}%">${media}</div>
    <div class="scene__ui">
      ${s.extra || ''}
      <div class="stack">
        ${s.tag ? `<p class="stag" aria-hidden="true">${s.tag}</p>` : ''}
        <p class="vtext">${s.v.map((l) => `<span class="vline">${l}</span>`).join('')}</p>
        ${s.note ? `<p class="snote">${s.note}</p>` : ''}
        ${s.cta || ''}
      </div>
    </div>
  </article>`;
}).join('');

const ca = $('#ca');
const caLabel = (v) => { ca.innerHTML = `Contract address <b class="ca__v">${v}</b>`; };
caLabel(CONTRACT ? CONTRACT.slice(0, 4) + '…' + CONTRACT.slice(-4) : '—');
if (CONTRACT) {
  ca.title = 'Copy the contract address';
  ca.addEventListener('click', async () => {
    try { await navigator.clipboard.writeText(CONTRACT); caLabel('Copied'); } catch { caLabel('Copy failed'); }
    setTimeout(() => caLabel(CONTRACT.slice(0, 4) + '…' + CONTRACT.slice(-4)), 1800);
  });
} else {
  ca.setAttribute('aria-disabled', 'true');
  ca.title = 'Not launched yet';
}

const scenes = [...host.children];
const art = scenes.map((s) => s.querySelector('.scene__art'));
const ui = scenes.map((s) => s.querySelector('.scene__ui'));
const lines = ui.map((u) => u.querySelectorAll('.stag, .vline, .snote, .btn'));
const video = host.querySelector('video');

/* ---------- preload with a real percentage ---------- */
const loader = $('#loader');
const pct = $('#loader-pct');
const assets = [...host.querySelectorAll('img')].map((img) => new Promise((res) => (img.complete ? res() : ['load', 'error'].forEach((e) => img.addEventListener(e, res, { once: true })))));
assets.push(new Promise((res) => { video.addEventListener('loadeddata', res, { once: true }); setTimeout(res, 8000); video.load(); }));
let done = 0;
assets.forEach((p) => p.then(() => { pct.textContent = Math.round((++done / assets.length) * 100); }));

/* ---------- scroll story ---------- */
const chapterEl = $('#hud-chapter');
const countEl = $('#count-now');
const hint = $('#hint');
let current = -1;
const setChapter = (i) => {
  if (i === current) return;
  current = i;
  chapterEl.textContent = SCENES[i].chapter;
  countEl.textContent = pad(i + 1);
};
setChapter(0);

if (reduce) {
  document.documentElement.classList.add('is-static');
  video.addEventListener('loadedmetadata', () => { video.currentTime = video.duration; });
} else {
  const lenis = new Lenis({ lerp: 0.1 });
  lenis.on('scroll', ScrollTrigger.update);
  gsap.ticker.add((t) => lenis.raf(t * 1000));
  gsap.ticker.lagSmoothing(0);

  // Scene 0 is longer: scrolling plays the clip frame by frame. Every other scene is one unit.
  const DUR = [1.8, 1, 1, 1, 1, 1];
  const START = DUR.map((_, i) => DUR.slice(0, i).reduce((a, b) => a + b, 0));
  const D = START[N - 1] + 0.5;           // the last half unit is a short rest on the final scene
  const Z = DUR[0] - 0.22;                // end of the clip, orb fills the frame
  const proxy = { t: 0 };

  const nextPoint = (t, dir) => {
    const pts = START.slice(1);
    if (t < START[1]) return dir > 0 ? START[1] : Z;
    return dir > 0 ? (pts.find((p) => p >= t - 0.001) ?? D) : ([...pts].reverse().find((p) => p <= t + 0.001) ?? START[1]);
  };

  const tl = gsap.timeline({
    defaults: { ease: 'none' },
    scrollTrigger: {
      trigger: '#stage', start: 'top top', end: () => `+=${innerHeight * D * 0.95}`, pin: true, scrub: 0.6, anticipatePin: 1,
      invalidateOnRefresh: true,
      // free scroll while the clip plays; snap to scene starts after it
      snap: { snapTo: (v, self) => (v * D <= Z ? v : nextPoint(v * D, self.direction) / D), duration: { min: 0.25, max: 0.8 }, delay: 0.1, ease: 'power2.inOut' },
      onUpdate: (self) => {
        const t = self.progress * D;
        setChapter(Math.max(0, SCENES.findIndex((_, i) => t < (START[i + 1] ?? Infinity) - 0.11)));
      },
    },
  });

  gsap.set(art.slice(1), { opacity: 0, scale: 0.78 });
  gsap.set(ui.slice(1), { opacity: 0 });

  // clip scrubbing (all-intra encode, so every seek is a single frame decode)
  video.pause();
  // never queue a seek while one is still decoding: stacked seeks are what makes the frame tear and stutter
  let want = 0;
  const seek = () => { want = proxy.t; if (!video.seeking && Math.abs(video.currentTime - want) > 0.01) video.currentTime = want; };
  video.addEventListener('seeked', () => { if (Math.abs(video.currentTime - want) > 0.01) video.currentTime = want; });
  const setDuration = () => tl.to(proxy, { t: Math.max(0, video.duration - 0.05), duration: Z, onUpdate: seek }, 0);
  video.readyState >= 1 ? setDuration() : video.addEventListener('loadedmetadata', setDuration, { once: true });

  SCENES.forEach((_, i) => {
    const s = START[i], last = i === N - 1, hold = i === 0 ? 1.08 : 1.28;
    const end = s + DUR[i];
    if (i > 0) {
      tl.fromTo(art[i], { scale: 0.78, opacity: 0 }, { scale: 1, opacity: 1, ease: 'power1.out', duration: 0.22 }, s - 0.22);
      tl.fromTo(ui[i], { opacity: 0 }, { opacity: 1, duration: 0.05 }, s - 0.2);
      tl.fromTo(lines[i], { autoAlpha: 0, y: 16 }, { autoAlpha: 1, y: 0, duration: 0.07, stagger: { amount: 0.12 } }, s - 0.2);
    }
    tl.fromTo(art[i], { scale: 1 }, { scale: last ? 1.06 : hold, duration: last ? 0.5 : DUR[i] - 0.22, immediateRender: i === 0 }, s);
    if (!last) {
      tl.fromTo(ui[i], { opacity: 1 }, { opacity: 0, duration: 0.14, immediateRender: false }, end - 0.45);
      tl.fromTo(art[i], { scale: hold, opacity: 1 }, { scale: 2.4, opacity: 0, ease: 'power2.in', duration: 0.22, immediateRender: false }, end - 0.22);
    }
  });
  // wordmark belongs to the opening wide shot; it leaves as the orb takes over
  tl.to('.title', { opacity: 0, y: -24, duration: 0.35 }, 0.25);
  tl.to(hint, { opacity: 0, duration: 0.06 }, 0);
}

Promise.all(assets).then(() => {
  loader.classList.add('is-done');
  if (!reduce) gsap.from(lines[0], { autoAlpha: 0, y: 16, stagger: 0.12, duration: 0.8, delay: 0.4, ease: 'power2.out' });
  gsap.from('.title', { autoAlpha: 0, duration: 1.2, delay: 0.2 });
  setTimeout(() => loader.remove(), 900);
});
