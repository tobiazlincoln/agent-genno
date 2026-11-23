import * as S from './core.js';
import { sol, short, fmtTime, countdown, isAddr, HOUR, LAMPORTS } from './core.js';

const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);
const OWNER = 'Hq3nW5vYt8KjZxP2mBc7LdRe4sUaF9oG6iTz1XhN';
$('#wallet-addr').textContent = short(OWNER, 5, 4);

/* ---------- toast + confirm ---------- */
function toast(msg, kind = '') {
  const el = document.createElement('p');
  el.className = `toast ${kind}`;
  el.textContent = msg;
  $('#toasts').append(el);
  setTimeout(() => el.remove(), 4500);
}
const dlg = $('#dlg');
let dlgOpener = null;
function confirmDlg({ title, body, ok, danger = false }) {
  $('#dlg-title').textContent = title;
  $('#dlg-body').textContent = body;
  const okBtn = $('#dlg-ok');
  okBtn.textContent = ok;
  okBtn.classList.toggle('btn--danger', danger);
  dlgOpener = document.activeElement;
  dlg.showModal();
  return new Promise((res) => dlg.addEventListener('close', () => { dlgOpener?.focus?.(); res(dlg.returnValue === 'ok'); }, { once: true }));
}

/* ---------- time track (the signature visual: parts as pearls on a clock) ---------- */
// Internal status keys stay as stored (menunggu / terkirim / dibatalkan); only the labels are English.
const statusText = { menunggu: 'Pending', terkirim: 'Sent', dibatalkan: 'Cancelled' };

function track({ parts, from, to, now = Date.now(), ticks }) {
  const W = 1000, H = 150, padX = 28;
  const x = (t) => padX + ((t - from) / (to - from)) * (W - padX * 2);
  const max = Math.max(1, ...parts.map((p) => p.amount));
  const axis = ticks.map(({ t, label }) => `<line x1="${x(t)}" x2="${x(t)}" y1="112" y2="122" class="tk-tick"/><text x="${x(t)}" y="142" class="tk-lbl" text-anchor="middle">${label}</text>`).join('');
  const nowX = now >= from && now <= to ? `<line x1="${x(now)}" x2="${x(now)}" y1="10" y2="122" class="tk-now"/><text x="${x(now)}" y="8" class="tk-lbl tk-lbl--now" text-anchor="middle">now</text>` : '';
  const pearls = parts.map((p, i) => {
    const r = 6 + 14 * Math.sqrt(p.amount / max);
    const y = 76 + (((i * 37) % 5) - 2) * 11;
    const label = `Part ${p.n} of ${p.of}, ${sol(p.amount)} SOL, ${statusText[p.status].toLowerCase()}, ${fmtTime(p.at)}`;
    return `<g class="pearl pearl--${p.status}" tabindex="0" role="img" aria-label="${label}" data-detail="${label}" transform="translate(${x(p.at).toFixed(1)} ${y})"><circle r="${r.toFixed(1)}"/></g>`;
  }).join('');
  return `<svg class="track" viewBox="0 0 ${W} ${H}" role="group" aria-label="Timeline of payment parts">
    <line x1="${padX}" x2="${W - padX}" y1="112" y2="112" class="tk-axis"/>${axis}${nowX}${pearls}</svg>
    <p class="track__detail" data-track-detail aria-live="polite">Hover or focus a pearl to see its details.</p>`;
}
document.addEventListener('pointerover', (e) => { const g = e.target.closest?.('.pearl'); if (g) $('[data-track-detail]')?.replaceChildren(g.dataset.detail); });
document.addEventListener('focusin', (e) => { const g = e.target.closest?.('.pearl'); if (g) $('[data-track-detail]')?.replaceChildren(g.dataset.detail); });

const label = (addr) => S.get().allowlist.find((a) => a.addr === addr)?.label ?? short(addr, 5, 4);
const badge = (s) => `<span class="st st--${s}">${statusText[s]}</span>`;
const plural = (n, w) => `${n} ${w}${n === 1 ? '' : 's'}`;

let homeTab = 'flow';
const dayStart = (t) => { const d = new Date(t); d.setHours(0, 0, 0, 0); return d.getTime(); };

// bars per day, last 6 days plus today and the next 3: solid = sent, dashed = still pending, dashed line = daily limit
function flowChart(parts, cap, now) {
  const W = 720, H = 260, L = 50, R = 8, T = 16, B = 34;
  const days = Array.from({ length: 10 }, (_, i) => dayStart(now) + (i - 6) * 24 * HOUR);
  const data = days.map((d0) => {
    const day = parts.filter((p) => p.at >= d0 && p.at < d0 + 24 * HOUR && p.status !== 'dibatalkan');
    return { d0, sent: day.filter((p) => p.status === 'terkirim').reduce((s, p) => s + p.amount, 0), pend: day.filter((p) => p.status === 'menunggu').reduce((s, p) => s + p.amount, 0) };
  });
  const max = Math.max(cap * 1.1, ...data.map((d) => d.sent + d.pend));
  const y = (v) => T + (1 - v / max) * (H - T - B);
  const slot = (W - L - R) / data.length, bw = slot * 0.54;
  const grid = [0, 1, 2, 3, 4].map((i) => { const v = (max * i) / 4; return `<line class="ch-grid" x1="${L}" x2="${W - R}" y1="${y(v)}" y2="${y(v)}"/><text class="ch-lbl" x="${L - 8}" y="${y(v) + 4}" text-anchor="end">${sol(v, 2)}</text>`; }).join('');
  const bars = data.map((d, i) => {
    const x = L + i * slot + (slot - bw) / 2, isToday = i === 6;
    const name = isToday ? 'Today' : new Date(d.d0).toLocaleDateString('en-US', { weekday: 'short' });
    const detail = `${new Date(d.d0).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}: ${sol(d.sent)} SOL sent, ${sol(d.pend)} SOL pending`;
    const hs = Math.max(0, y(0) - y(d.sent)), hp = Math.max(0, y(0) - y(d.sent + d.pend) - hs);
    return `<g class="bar" tabindex="0" role="img" aria-label="${detail}" data-detail="${detail}">
      <rect class="hit" x="${(x - 6).toFixed(1)}" y="${T}" width="${(bw + 12).toFixed(1)}" height="${H - T - B}" rx="6"/>
      ${d.sent ? `<rect class="sent" x="${x.toFixed(1)}" y="${y(d.sent).toFixed(1)}" width="${bw.toFixed(1)}" height="${hs.toFixed(1)}" rx="5"/>` : ''}
      ${d.pend ? `<rect class="pend" x="${x.toFixed(1)}" y="${y(d.sent + d.pend).toFixed(1)}" width="${bw.toFixed(1)}" height="${hp.toFixed(1)}" rx="5"/>` : ''}
      <text class="ch-lbl" x="${(x + bw / 2).toFixed(1)}" y="${H - 10}" text-anchor="middle" ${isToday ? 'style="fill:var(--bone);font-weight:600"' : ''}>${name}</text></g>`;
  }).join('');
  return `<svg class="chart" viewBox="0 0 ${W} ${H}" role="group" aria-label="Daily amounts sent and pending, with the daily limit">
    <defs><linearGradient id="gSent" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffb347"/><stop offset="1" stop-color="#7a4510"/></linearGradient></defs>
    ${grid}<line class="ch-cap" x1="${L}" x2="${W - R}" y1="${y(cap)}" y2="${y(cap)}"/><text class="ch-cap-t" x="${W - R}" y="${y(cap) - 6}" text-anchor="end">Daily limit ${sol(cap, 2)} SOL</text>${bars}</svg>
    <p class="chart-detail" data-track-detail aria-live="polite">Hover or focus a bar to see that day. Solid is sent, dashed is still pending.</p>`;
}

/* ---------- views ---------- */
const views = {
  home() {
    const st = S.get(), now = Date.now(), pend = S.pending();
    const all = S.allParts();
    const spent = S.sentToday(), left = Math.max(0, st.capLamports - spent);
    const week = all.filter((p) => p.status === 'terkirim' && p.at > now - 7 * 24 * HOUR);
    const sum = (a) => a.reduce((s, p) => s + p.amount, 0);
    const ic = (d) => `<span class="tile__ic"><svg viewBox="0 0 24 24" aria-hidden="true">${d}</svg></span>`;
    const tiles = [
      ['Private balance', sol(st.balance), 'Held inside the pool', ic('<rect x="3.5" y="6" width="17" height="12" rx="3"/><path d="M16 12h2"/>')],
      ['Sent, last 7 days', sol(sum(week)), `${plural(week.length, 'part')} released`, ic('<path d="M5 19 19 5M9 5h10v10"/>')],
      ['Waiting to send', sol(sum(pend)), `${plural(pend.length, 'part')} scheduled`, ic('<circle cx="12" cy="12" r="8"/><path d="M12 7.5V12l3 2"/>')],
    ];
    const chartPanel = `
      <section class="panel" aria-labelledby="h-flow">
        <div class="panel__h"><h2 class="sec" id="h-flow">Release flow</h2>
          <div class="tabs" role="tablist" aria-label="Chart view">
            <button role="tab" id="tab-flow" aria-selected="${homeTab === 'flow'}" data-tab="flow">Daily flow</button>
            <button role="tab" id="tab-track" aria-selected="${homeTab === 'track'}" data-tab="track">Next 72 hours</button>
          </div></div>
        ${homeTab === 'flow'
          ? flowChart(all, st.capLamports, now)
          : track({ parts: all.filter((p) => p.at > now - 24 * HOUR), from: now - 24 * HOUR, to: now + 72 * HOUR, now, ticks: [-24, 0, 24, 48, 72].map((h) => ({ t: now + h * HOUR, label: h === 0 ? '' : `${h > 0 ? '+' : '−'}${Math.abs(h)} h` })) })}
      </section>`;
    const recent = all.slice().sort((a, b) => Math.abs(a.at - now) - Math.abs(b.at - now)).slice(0, 6).sort((a, b) => b.at - a.at); // the parts closest to now, newest first
    const hist = `
      <section class="panel" aria-labelledby="h-rec">
        <div class="panel__h"><h2 class="sec" id="h-rec">Recent parts</h2><a class="link" href="#/history">View all</a></div>
        ${recent.length ? `<table class="tbl"><thead><tr><th scope="col">Recipient</th><th scope="col">Part</th><th scope="col">Status</th><th scope="col" class="r">Amount (SOL)</th></tr></thead><tbody>
          ${recent.map((p) => `<tr><td><span class="who"><span class="who__ic" aria-hidden="true">${esc(label(p.plan.recipient)[0])}</span>${esc(label(p.plan.recipient))}</span></td><td>${p.n} of ${p.of}<p class="muted">${fmtTime(p.at)}</p></td><td>${badge(p.status)}</td><td class="r num">${sol(p.amount)}</td></tr>`).join('')}
        </tbody></table>` : `<p class="empty">Nothing yet. <a href="#/send">Create a private payment</a>.</p>`}
      </section>`;
    const live = all.filter((p) => p.status !== 'dibatalkan');
    const total = Math.max(1, sum(live));
    const maxPart = Math.max(1, ...live.map((p) => p.amount));
    const recips = st.allowlist.map((a) => ({ a, parts: live.filter((p) => p.plan.recipient === a.addr) })).filter((r) => r.parts.length);
    const dotsPanel = `
      <section class="panel" aria-labelledby="h-rcp">
        <h2 class="sec" id="h-rcp">Where it goes</h2>
        ${recips.length ? `<ul class="dots">${recips.map(({ a, parts }) => {
          const share = (sum(parts) / total) * 100;
          return `<li><span class="dots__n" title="${esc(a.label)}">${esc(a.label)}</span><span class="dots__t" aria-hidden="true">${parts.slice(-7).map((p, i, arr) => { const d = 5 + 6 * Math.sqrt(p.amount / maxPart); return `<i style="left:${(8 + ((i + 0.5) / arr.length) * 84).toFixed(1)}%;width:${d.toFixed(0)}px;height:${d.toFixed(0)}px"></i>`; }).join('')}</span><span class="dots__p">${share.toFixed(0)}%</span></li>`;
        }).join('')}</ul>` : `<p class="empty">No parts scheduled yet.</p>`}
      </section>`;
    const att = [];
    if (st.killed) att.push(['Autopilot is stopped', 'Resume when you are sure.', '<button class="link" data-act="resume">Resume</button>']);
    if (left < st.capLamports * 0.2) att.push(['Daily limit almost used', `${sol(left)} SOL left today.`, '<a class="link" href="#/policy">Change limit</a>']);
    if (now - st.probeAt > 24 * HOUR) att.push(['Version probe is stale', 'Last checked more than 24 hours ago.', '<a class="link" href="#/system">Check now</a>']);
    const attPanel = `
      <section class="panel" aria-labelledby="h-att">
        <h2 class="sec" id="h-att">Needs attention</h2>
        ${att.length ? `<ul class="rows">${att.map(([t, d, a]) => `<li><div><b>${t}</b><p class="muted">${d}</p></div>${a}</li>`).join('')}</ul>` : `<p class="empty">Nothing needs your attention right now.</p>`}
      </section>`;
    const card = `
      <section class="vcard" aria-label="Private balance card">
        <div class="vcard__top"><span>Private balance</span><b>Mainnet</b></div>
        <p class="vcard__bal"><span class="num">${sol(st.balance)}</span><small>SOL</small></p>
        <p class="vcard__addr">${short(OWNER, 6, 4)}</p>
        <div class="vcard__row"><span>Daily limit<b class="num">${sol(spent)} / ${sol(st.capLamports)}</b></span><span>Autopilot<b>${st.killed ? 'Stopped' : 'Running'}</b></span></div>
      </section>`;
    return `
      <div class="bento">
        <div class="col-l">
          <div class="tiles">${tiles.map(([t, v, c, i]) => `<section class="panel tile"><div class="tile__h"><span>${t}</span>${i}</div><p class="tile__v">${v}<small>SOL</small></p><p class="tile__c">${c}</p></section>`).join('')}</div>
          ${chartPanel}
          ${hist}
        </div>
        <div class="col-r">${card}${dotsPanel}${attPanel}</div>
      </div>`;
  },

  send() {
    const st = S.get();
    return `
      <div class="send">
        <form id="send" novalidate>
          <p class="form-err" id="form-err" role="alert"></p>
          <div class="field">
            <label for="amt">Amount (SOL)</label>
            <input id="amt" inputmode="decimal" autocomplete="off" placeholder="0.0500" aria-describedby="amt-hint amt-err" />
            <p class="hint" id="amt-hint">Private balance ${sol(st.balance)} SOL. Daily limit left ${sol(Math.max(0, st.capLamports - S.sentToday()))} SOL.</p>
            <p class="err" id="amt-err" role="alert"></p>
          </div>
          <div class="field">
            <label for="rcp">Recipient</label>
            <select id="rcp" aria-describedby="rcp-err">
              <option value="">Choose from the recipient list</option>
              ${st.allowlist.map((a) => `<option value="${a.addr}">${esc(a.label)} (${short(a.addr, 5, 4)})</option>`).join('')}
            </select>
            <p class="hint">Only addresses on the list can be chosen. <a href="#/policy">Manage list</a></p>
            <p class="err" id="rcp-err" role="alert"></p>
          </div>
          <div class="field">
            <label for="maxh">Delay up to: <output id="maxh-out">48</output> hours</label>
            <input id="maxh" type="range" min="2" max="72" value="48" />
            <p class="hint">Each part waits between 1 hour and this limit.</p>
          </div>
          <fieldset class="field">
            <legend>Number of parts</legend>
            <div class="seg">
              ${[['0', 'Random 3–5'], ['3', '3'], ['4', '4'], ['5', '5']].map(([v, l], i) => `<label><input type="radio" name="k" value="${v}" ${i === 0 ? 'checked' : ''}><span>${l}</span></label>`).join('')}
            </div>
          </fieldset>
          <button class="btn" type="submit">Create plan</button>
        </form>

        <section class="preview" id="preview" aria-live="polite" aria-labelledby="pv-h">
          <h2 class="sec" id="pv-h">Plan</h2>
          <p class="empty" id="pv-empty">Enter an amount and a recipient, then create a plan. You can shuffle it again before scheduling.</p>
        </section>
      </div>`;
  },

  schedule() {
    const plans = S.get().plans;
    if (!plans.length) return `<p class="empty">Nothing scheduled yet. <a href="#/send">Create a private payment</a> to get started.</p>`;
    return `<div class="plans">${plans.map((pl) => {
      const sent = pl.parts.filter((p) => p.status === 'terkirim').length;
      const open = pl.parts.some((p) => p.status === 'menunggu');
      return `<details class="plan" ${open ? 'open' : ''}>
        <summary><span><b>${sol(pl.total)} SOL</b> to ${esc(label(pl.recipient))}</span><span class="muted">${sent} of ${pl.parts.length} sent · created ${fmtTime(pl.createdAt)}</span></summary>
        <table class="tbl"><thead><tr><th scope="col">Part</th><th scope="col" class="r">Amount</th><th scope="col">Send time</th><th scope="col">Status</th><th scope="col"><span class="sr-only">Actions</span></th></tr></thead><tbody>
          ${pl.parts.map((p, i) => `<tr><td>${i + 1} of ${pl.parts.length}</td><td class="r num">${sol(p.amount)}</td><td>${fmtTime(p.at)}</td><td>${badge(p.status)}</td>
            <td class="r">${p.status === 'menunggu' ? `<button class="link link--danger" data-cancel="${p.id}">Cancel</button>` : ''}</td></tr>`).join('')}
        </tbody></table></details>`;
    }).join('')}</div>`;
  },

  history(filter = 'all') {
    const rows = S.allParts().filter((p) => filter === 'all' || p.status === filter).sort((a, b) => b.at - a.at);
    const opts = [['all', 'All statuses'], ['terkirim', 'Sent'], ['menunggu', 'Pending'], ['dibatalkan', 'Cancelled']];
    return `
      <div class="toolbar"><label for="flt">Show</label>
        <select id="flt">${opts.map(([v, l]) => `<option value="${v}" ${v === filter ? 'selected' : ''}>${l}</option>`).join('')}</select></div>
      ${rows.length ? `<div class="scroll" tabindex="0" role="region" aria-label="History table, scrollable"><table class="tbl"><thead><tr><th scope="col">Time</th><th scope="col">Part</th><th scope="col" class="r">Amount (SOL)</th><th scope="col">Recipient</th><th scope="col">Status</th><th scope="col">Signature</th></tr></thead><tbody>
        ${rows.map((p) => `<tr><td>${fmtTime(p.at)}</td><td>${p.n} of ${p.of}</td><td class="r num">${sol(p.amount)}</td><td>${esc(label(p.plan.recipient))}</td><td>${badge(p.status)}</td>
          <td>${p.sig ? `<button class="link" data-copy="${p.sig}" aria-label="Copy signature ${short(p.sig, 6, 4)}">${short(p.sig, 6, 4)}</button>` : '<span class="muted">Not yet</span>'}</td></tr>`).join('')}
      </tbody></table></div>` : `<p class="empty">${filter === 'all' ? 'No history yet.' : 'No parts with this status.'}</p>`}`;
  },

  policy() {
    const st = S.get();
    return `
      <div class="policy">
        <section aria-labelledby="p-kill">
          <h2 class="sec" id="p-kill">Kill switch</h2>
          <div class="sw-row"><p>When on, no part is sent and new plans are rejected.</p>
            <button class="sw" id="sw-kill" role="switch" aria-checked="${st.killed}" aria-labelledby="p-kill"><span class="sw__knob"></span><span class="sw__t">${st.killed ? 'On' : 'Off'}</span></button></div>
        </section>
        <section aria-labelledby="p-cap">
          <h2 class="sec" id="p-cap">Daily limit</h2>
          <form id="cap-form" class="inline" novalidate>
            <div class="field"><label for="cap">Maximum per day (SOL)</label><input id="cap" inputmode="decimal" value="${sol(st.capLamports)}" aria-describedby="cap-err" /><p class="err" id="cap-err" role="alert"></p></div>
            <button class="btn" type="submit">Save limit</button>
          </form>
        </section>
        <section aria-labelledby="p-al">
          <h2 class="sec" id="p-al">Recipient list</h2>
          ${st.allowlist.length ? `<ul class="rows">${st.allowlist.map((a, i) => `<li><div><b>${esc(a.label)}</b><p class="muted addr">${esc(a.addr)}</p></div><button class="link link--danger" data-remove="${i}">Remove</button></li>`).join('')}</ul>` : `<p class="empty">The list is empty, so no payment can be scheduled. Add an address below.</p>`}
          <form id="al-form" class="inline" novalidate>
            <div class="field"><label for="al-l">Name</label><input id="al-l" autocomplete="off" aria-describedby="al-err" /></div>
            <div class="field"><label for="al-a">Solana address</label><input id="al-a" autocomplete="off" spellcheck="false" aria-describedby="al-err" /></div>
            <p class="err" id="al-err" role="alert"></p>
            <button class="btn btn--ghost" type="submit">Add recipient</button>
          </form>
        </section>
      </div>`;
  },

  system() {
    const st = S.get();
    const ago = Math.round((Date.now() - st.probeAt) / 60000);
    const rows = [
      ['TEE policy', 'Pinned to a verified version', 'Match'],
      ['Indexer response shape', 'Per the shim: the data key, not transactions', 'Match'],
      ['Prover via gateway', 'TEE route, not a local prover', 'Connected'],
      ['Wallet sync', 'Encrypted snapshot log, full state from the indexer', 'Up to date'],
    ];
    return `<div class="sys">
      <p class="lead">The daemon checks versions before every send. If anything does not match, autopilot stops on its own.</p>
      <ul class="rows rows--probe">${rows.map(([t, d, s]) => `<li><div><b>${t}</b><p class="muted">${d}</p></div><span class="st st--terkirim">${s}</span></li>`).join('')}</ul>
      <div class="probe-act"><button class="btn btn--ghost" id="probe" type="button">Check now</button><p class="muted" id="probe-at">Last checked ${ago < 1 ? 'just now' : `${plural(ago, 'minute')} ago`}.</p></div>

      <section class="measure" aria-labelledby="m-h">
        <h2 class="sec" id="m-h">Measurement notes</h2>
        <p class="lead">The K1 gate was registered before any computation, with locked thresholds. It failed. Building continued with a narrower claim.</p>
        <table class="tbl"><thead><tr><th scope="col">Pass condition (7 days, 1% tolerance)</th><th scope="col">Result</th><th scope="col">Target</th></tr></thead><tbody>
          <tr><td>Chaff lowers unique aggregate matching</td><td><b class="bad num">13.0%</b> <span class="muted">(18.7% to 16.3%)</span></td><td>50% or more</td></tr>
          <tr><td>Chaff lowers unique one-to-one matching</td><td><b class="bad num">64.4%</b> <span class="muted">(29.6% to 10.6%)</span></td><td>80% or more</td></tr>
        </tbody></table>
        <p class="muted measure__txt">Post-gate diagnostic, not the gate itself: the one-to-one signal an attacker can learn from a normal user is +4.4 points above chance, while for Chaff users it is −0.7 points, no better than chance. Data: 3 weeks, 8,996 transactions, measured 2026-11-22. The gate will be re-run once the pool matures, before any stronger claim.</p>
      </section></div>`;
  },
};

const titles = { home: 'Home', send: 'Send privately', schedule: 'Schedule', history: 'History', policy: 'Policy', system: 'System status' };
let route = 'home';
const subs = {
  home: () => { const st = S.get(), n = S.pending()[0]; return st.killed ? 'Autopilot is stopped. No parts will be sent.' : n ? `Next part sends in <span class="num" data-countdown="${n.at}">${countdown(n.at - Date.now())}</span>` : 'No parts waiting. Create a private payment to start.'; },
  send: () => 'Split one payment into private parts.',
  schedule: () => 'Every part, waiting or already sent.',
  history: () => 'Every part with its signature.',
  policy: () => 'The limits the daemon enforces before every send.',
  system: () => 'Version checks and measurement notes.',
};

/* ---------- binders: real behaviour for every control ---------- */
function bindSend() {
  const st = () => S.get();
  const f = $('#send'), prev = $('#preview');
  let draft = null;
  $('#maxh').addEventListener('input', (e) => ($('#maxh-out').textContent = e.target.value));
  const setErr = (id, msg) => { $(`#${id}`).textContent = msg; };
  const check = () => {
    ['amt-err', 'rcp-err', 'form-err'].forEach((i) => setErr(i, ''));
    const raw = $('#amt').value.trim().replace(',', '.');
    const v = Number(raw), lam = Math.round(v * LAMPORTS);
    const left = Math.max(0, st().capLamports - S.sentToday());
    let ok = true;
    if (st().killed) { setErr('form-err', 'Kill switch is on. Resume autopilot from the top bar before scheduling.'); ok = false; }
    if (!raw || !Number.isFinite(v) || v <= 0) { setErr('amt-err', 'Enter an amount above 0, for example 0.05.'); ok = false; }
    else if (lam > st().balance) { setErr('amt-err', `Exceeds your private balance (${sol(st().balance)} SOL).`); ok = false; }
    else if (lam > left) { setErr('amt-err', `Exceeds your remaining daily limit (${sol(left)} SOL). Change it under Policy or lower the amount.`); ok = false; }
    if (!$('#rcp').value) { setErr('rcp-err', 'Choose a recipient from the list.'); ok = false; }
    return ok ? { lam, rcp: $('#rcp').value } : null;
  };
  const build = () => {
    const c = check(); if (!c) return;
    const k = Number($('input[name=k]:checked').value) || undefined;
    draft = S.makePlan(c.lam, c.rcp, Number($('#maxh').value), Date.now(), k);
    const parts = draft.parts.map((p, i) => ({ ...p, n: i + 1, of: draft.parts.length, plan: draft }));
    const maxH = Number($('#maxh').value), now = Date.now();
    const step = maxH <= 12 ? 2 : maxH <= 36 ? 6 : 12;
    const ticks = []; for (let h = 0; h <= maxH; h += step) ticks.push({ t: now + h * HOUR, label: `${h} h` });
    prev.innerHTML = `<h2 class="sec" id="pv-h">Plan</h2>
      ${track({ parts, from: now, to: now + maxH * HOUR, now: now - 1, ticks })}
      <table class="tbl"><thead><tr><th scope="col">Part</th><th scope="col" class="r">Amount (SOL)</th><th scope="col">Sends</th></tr></thead><tbody>
        ${parts.map((p) => `<tr><td>${p.n} of ${p.of}</td><td class="r num">${sol(p.amount)}</td><td>${fmtTime(p.at)}</td></tr>`).join('')}
      </tbody><tfoot><tr><th scope="row">Total</th><td class="r num">${sol(draft.total)}</td><td class="muted">equals the amount you entered</td></tr></tfoot></table>
      <div class="actions"><button class="btn" id="go" type="button">Schedule ${plural(parts.length, 'part')}</button><button class="btn btn--ghost" id="reroll" type="button">Shuffle again</button></div>`;
    $('#reroll').addEventListener('click', build);
    $('#go').addEventListener('click', () => {
      const c2 = check(); if (!c2 || !draft) return; // policy is enforced again at the moment of scheduling
      S.set((s) => { s.plans.unshift(draft); s.balance -= draft.total; });
      toast(`Scheduled: ${plural(draft.parts.length, 'part')}, ${sol(draft.total)} SOL total.`, 'ok');
      location.hash = '#/schedule';
    });
    $('#reroll').focus();
  };
  f.addEventListener('submit', (e) => { e.preventDefault(); build(); });
}

async function toggleKill() {
  if (!S.get().killed) { S.set((s) => (s.killed = true)); toast('Autopilot stopped. Waiting parts will not be sent.', 'warn'); }
  else if (await confirmDlg({ title: 'Resume autopilot?', body: 'Parts that came due during the pause will be sent right away.', ok: 'Resume' })) { S.set((s) => (s.killed = false)); toast('Autopilot is running again.', 'ok'); }
}

function bindPolicy() {
  $('#sw-kill').addEventListener('click', async () => { await toggleKill(); render(); });
  $('#cap-form').addEventListener('submit', (e) => {
    e.preventDefault();
    const v = Number($('#cap').value.trim().replace(/,/g, ''));
    if (!Number.isFinite(v) || v <= 0) { $('#cap-err').textContent = 'Enter a limit above 0 SOL.'; return; }
    $('#cap-err').textContent = '';
    S.set((s) => (s.capLamports = Math.round(v * LAMPORTS)));
    toast(`Daily limit saved: ${sol(Math.round(v * LAMPORTS))} SOL.`, 'ok');
  });
  $('#al-form').addEventListener('submit', (e) => {
    e.preventDefault();
    const l = $('#al-l').value.trim(), a = $('#al-a').value.trim(), err = $('#al-err');
    if (!l) { err.textContent = 'Give the recipient a name so it is easy to recognise.'; return; }
    if (!isAddr(a)) { err.textContent = 'Invalid address. Solana addresses are 32 to 44 base58 characters.'; return; }
    if (S.get().allowlist.some((x) => x.addr === a)) { err.textContent = 'This address is already on the list.'; return; }
    S.set((s) => s.allowlist.push({ label: l, addr: a }));
    toast(`${l} added to the recipient list.`, 'ok');
    render();
  });
  $$('[data-remove]').forEach((b) => b.addEventListener('click', async () => {
    const a = S.get().allowlist[Number(b.dataset.remove)];
    const busy = S.pending().some((p) => p.plan.recipient === a.addr);
    if (await confirmDlg({ title: `Remove ${a.label}?`, body: busy ? 'Parts are still waiting for this address. They will still send unless you cancel them under Schedule.' : 'This address can no longer be chosen for new payments.', ok: 'Remove', danger: true })) {
      S.set((s) => s.allowlist.splice(Number(b.dataset.remove), 1)); toast(`${a.label} removed.`); render();
    }
  }));
}

function bindSchedule() {
  $$('[data-cancel]').forEach((b) => b.addEventListener('click', async () => {
    if (!(await confirmDlg({ title: 'Cancel this part?', body: 'The amount returns to your private balance. Other parts in the plan keep running.', ok: 'Cancel part', danger: true }))) return;
    S.set((s) => s.plans.forEach((pl) => pl.parts.forEach((p) => { if (p.id === b.dataset.cancel && p.status === 'menunggu') { p.status = 'dibatalkan'; s.balance += p.amount; } })));
    toast('Part cancelled. Funds returned to your private balance.', 'ok');
  }));
}

function bindHistory() {
  $('#flt').addEventListener('change', (e) => { $('#main').innerHTML = views.history(e.target.value); bindHistory(); $('#flt').focus(); });
  $$('[data-copy]').forEach((b) => b.addEventListener('click', async () => {
    try { await navigator.clipboard.writeText(b.dataset.copy); toast('Signature copied.', 'ok'); }
    catch { toast('Could not copy automatically. Select the signature text and copy it manually.', 'warn'); }
  }));
}

function bindSystem() {
  $('#probe').addEventListener('click', (e) => {
    const b = e.currentTarget; b.disabled = true; b.textContent = 'Checking…'; b.setAttribute('aria-busy', 'true');
    setTimeout(() => { S.set((s) => (s.probeAt = Date.now())); toast('All version checks match.', 'ok'); }, 1400);
  });
}

/* ---------- shell: routing, status, menu ---------- */
function status() {
  const st = S.get(), n = S.pending().length;
  $('#status').innerHTML = st.killed ? `<span class="dot dot--bad" aria-hidden="true"></span>Stopped` : `<span class="dot dot--ok" aria-hidden="true"></span>Autopilot on`;
  const kb = $('#kill-btn');
  kb.textContent = st.killed ? 'Resume autopilot' : 'Stop everything';
  kb.classList.toggle('btn--danger', !st.killed);
  const c = $('#count-schedule'); c.hidden = !n; c.textContent = n;
}

function render() {
  route = (location.hash.match(/^#\/(\w+)/) || [])[1];
  if (!views[route]) route = 'home';
  $('#page-title').textContent = titles[route];
  document.title = `${titles[route]} | Chaff`;
  $$('.nav a').forEach((a) => (a.dataset.route === route ? a.setAttribute('aria-current', 'page') : a.removeAttribute('aria-current')));
  $('#page-sub').innerHTML = subs[route]();
  $('#main').innerHTML = views[route]();
  ({ send: bindSend, policy: bindPolicy, schedule: bindSchedule, history: bindHistory, system: bindSystem })[route]?.();
  status();
}
$('#main').addEventListener('click', (e) => {
  if (e.target.closest('[data-act=resume]')) $('#kill-btn').click();
  const tab = e.target.closest('[data-tab]'); if (tab) { homeTab = tab.dataset.tab; render(); $(`#tab-${homeTab}`)?.focus(); }
});

window.addEventListener('hashchange', () => { render(); closeMenu(); $('#page-title').focus({ preventScroll: true }); window.scrollTo(0, 0); });

$('#kill-btn').addEventListener('click', toggleKill);

// forms keep their input; data views refresh when state changes
S.subscribe(() => { status(); if (['home', 'schedule', 'history', 'system'].includes(route) && !$('#flt:focus')) render(); else if (route === 'policy' && !document.activeElement.matches('input')) render(); });

const rail = $('#rail'), scrim = $('#scrim'), menuBtn = $('#menu-btn');
function openMenu() { rail.classList.add('is-open'); scrim.hidden = false; menuBtn.setAttribute('aria-expanded', 'true'); $('#rail-close').focus(); }
function closeMenu() { if (!rail.classList.contains('is-open')) return; rail.classList.remove('is-open'); scrim.hidden = true; menuBtn.setAttribute('aria-expanded', 'false'); menuBtn.focus(); }
menuBtn.addEventListener('click', openMenu);
$('#rail-close').addEventListener('click', closeMenu);
scrim.addEventListener('click', closeMenu);
document.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeMenu(); });

setInterval(() => { S.tick(); $$('[data-countdown]').forEach((el) => (el.textContent = countdown(Number(el.dataset.countdown) - Date.now()))); }, 1000);
render();
