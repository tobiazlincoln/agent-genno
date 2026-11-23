// Planner, formatting, and demo state. The planner mirrors the daemon's rules:
// 3 to 5 parts, non-round sizes, 1 to 72 h delays, exact total by construction.

export const LAMPORTS = 1_000_000_000;
export const HOUR = 3_600_000;

const rnd = () => crypto.getRandomValues(new Uint32Array(1))[0] / 2 ** 32;
const randInt = (a, b) => a + Math.floor(rnd() * (b - a + 1));

export function plan(totalLamports, maxHours = 72, k = randInt(3, 5)) {
  const w = Array.from({ length: k }, () => 0.5 + rnd());
  const sum = w.reduce((a, b) => a + b, 0);
  const amounts = w.map((x) => Math.floor((totalLamports * x) / sum));
  amounts[k - 1] += totalLamports - amounts.reduce((a, b) => a + b, 0); // exact total
  // nudge round amounts (multiples of 0.001 SOL) so they do not stand out against other people's round values
  for (let i = 0; i < k; i++) {
    if (amounts[i] % 1_000_000 === 0 && amounts[i] > 2) {
      const j = (i + 1) % k;
      amounts[i] += 1;
      amounts[j] -= 1;
    }
  }
  const span = Math.max(1, maxHours - 1);
  const delays = Array.from({ length: k }, () => 1 + rnd() * span).sort((a, b) => a - b);
  for (let i = 1; i < k; i++) if (delays[i] - delays[i - 1] < 0.35) delays[i] = Math.min(maxHours, delays[i - 1] + 0.35);
  return amounts.map((amount, i) => ({ amount, delayH: delays[i] }));
}

export const sol = (l, d = 4) => (l / LAMPORTS).toLocaleString('en-US', { minimumFractionDigits: d, maximumFractionDigits: d });
export const short = (s, a = 4, b = 4) => (s.length > a + b + 1 ? `${s.slice(0, a)}…${s.slice(-b)}` : s);
export const fmtTime = (ms) => new Date(ms).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' });
export const countdown = (ms) => {
  const t = Math.max(0, Math.floor(ms / 1000));
  const p = (n) => String(n).padStart(2, '0');
  return `${p(Math.floor(t / 3600))}:${p(Math.floor((t % 3600) / 60))}:${p(t % 60)}`;
};
export const isAddr = (s) => /^[1-9A-HJ-NP-Za-km-z]{32,44}$/.test(s);

const B58 = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz';
const fakeB58 = (n) => Array.from({ length: n }, () => B58[randInt(0, B58.length - 1)]).join('');
export const fakeSig = () => fakeB58(88);

/* ---------- demo state (labelled "Data contoh" in the UI) ---------- */
const KEY = 'chaff.demo.v3';

export function makePlan(totalLamports, recipient, maxHours, createdAt = Date.now(), k) {
  const parts = plan(totalLamports, maxHours, k).map((p, i) => ({
    id: `${createdAt}-${i}`, amount: p.amount, at: createdAt + p.delayH * HOUR, status: 'menunggu',
  }));
  return { id: String(createdAt), createdAt, total: totalLamports, recipient, parts };
}

function seed() {
  const now = Date.now();
  const allowlist = [
    { label: 'Operations wallet', addr: 'Dk4qWm8t3ZpXn2vJrB7cYhLs9aQe6UfT1oGxN5iKb9mR' },
    { label: 'Infrastructure vendor', addr: '8cVnH2yPq4RtLb6ZwXkM9sFaJd3EuG7oTh5NrC1xYvQe' },
    { label: 'Data provider', addr: 'Fp7YtRk2Wm9XcQeVb4NzHs6LdJa3UoGi8TxP5nBr1CvM' },
  ];
  const plans = [];
  // a week of earlier activity so the charts have something real-looking to show
  [[6.2, 0.052, 1], [5.1, 0.038, 0], [4.3, 0.067, 1], [3.4, 0.029, 2], [2.6, 0.058, 0], [1.9, 0.044, 1], [1.2, 0.036, 2]].forEach(([d, sol, r], i) => {
    const t = now - d * 24 * HOUR;
    const pl = makePlan(Math.round(sol * LAMPORTS) + 1000 + i * 137, allowlist[r].addr, 30, t, 3 + (i % 3));
    pl.parts.forEach((p) => { if (p.at < now) { p.status = 'terkirim'; p.sig = fakeSig(); } });
    plans.push(pl);
  });
  const mid = makePlan(Math.round(0.05 * LAMPORTS) + 9_271, allowlist[0].addr, 36, now - 20 * HOUR, 4);
  mid.parts.forEach((p) => { if (p.at < now) { p.status = 'terkirim'; p.sig = fakeSig(); } });
  const fresh = makePlan(Math.round(0.031 * LAMPORTS) + 1_907, allowlist[0].addr, 24, now - 1 * HOUR, 3);
  const next = makePlan(Math.round(0.024 * LAMPORTS) + 4_411, allowlist[2].addr, 60, now - 0.5 * HOUR, 4);
  return { killed: false, capLamports: Math.round(0.12 * LAMPORTS), balance: Math.round(0.412 * LAMPORTS) + 8_330, allowlist, plans: [next, fresh, mid, ...plans.reverse()], probeAt: now - 41 * 60_000 };
}

let state;
try { state = JSON.parse(localStorage.getItem(KEY)); } catch { state = null; }
if (!state || !Array.isArray(state.plans)) {
  state = seed();
  try { localStorage.setItem(KEY, JSON.stringify(state)); } catch { /* storage blocked */ }
}

const subs = new Set();
export const get = () => state;
export const subscribe = (fn) => (subs.add(fn), () => subs.delete(fn));
export function set(mutator) {
  mutator(state);
  try { localStorage.setItem(KEY, JSON.stringify(state)); } catch { /* storage blocked: state still works for this session */ }
  subs.forEach((f) => f(state));
}

export const allParts = () => state.plans.flatMap((p) => p.parts.map((x, i) => ({ ...x, plan: p, n: i + 1, of: p.parts.length })));
export const pending = () => allParts().filter((p) => p.status === 'menunggu').sort((a, b) => a.at - b.at);
export const sentToday = () => { // amount planned today, excluding cancelled parts
  const start = new Date(); start.setHours(0, 0, 0, 0);
  return state.plans.filter((p) => p.createdAt >= start.getTime()).reduce((s, p) => s + p.parts.filter((x) => x.status !== 'dibatalkan').reduce((a, x) => a + x.amount, 0), 0);
};

// stands in for the daemon: release parts whose time has come, unless the kill switch is on
export function tick() {
  if (state.killed) return;
  const now = Date.now();
  const due = allParts().filter((p) => p.status === 'menunggu' && p.at <= now);
  if (!due.length) return;
  set((s) => s.plans.forEach((pl) => pl.parts.forEach((x) => { if (x.status === 'menunggu' && x.at <= now) { x.status = 'terkirim'; x.sig = fakeSig(); } })));
}
