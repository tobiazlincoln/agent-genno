#!/usr/bin/env python3
"""agent.py — AI agent deterministik di dalam mainnet_tool.

Mengerti pola code yang sudah dibangun (template, blueprint, chaff PoC) melalui
registry patterns.json. Menjawab pertanyaan HANYA dari data beralamat
(file:baris / laporan) — bukan generasi bebas.

Tiga aturan keras (by construction, bukan janji):
  1. NO CRASH  — semua error jadi pesan jelas; tidak ada traceback ke user.
  2. NO HALU   — setiap klaim dikutip dari sumber (path:baris). Tidak ada klaim
                 tanpa sumber; jika tidak ada data, bilang TIDAK ADA DATA.
  3. TANPA DATA TANPA JAWABAN — pertanyaan di luar cakupan dijawab dengan daftar
                 apa yang BISA dijawab, bukan tebakan.

Dipanggil via: mainnet.py agent "<pertanyaan>" [--project DIR] [--blueprint FILE]
"""
import glob
import json
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.realpath(__file__))
PATTERNS_FILE = os.path.join(HERE, 'patterns.json')
EXTS = ('.py', '.ts', '.tsx', '.js', '.jsx', '.rs', '.sol', '.json', '.md', '.yml', '.yaml', '.toml', '.sh', '.env')
NO_DATA = 'TIDAK ADA DATA untuk itu — dan saya tidak menebak.'


def out(line=''):
    print(line)


def fail(msg):
    print(f'agent: {msg}')
    return 1


def safe_read(path, limit=4000):
    try:
        with open(path, errors='replace') as f:
            return f.read(limit)
    except OSError:
        return None


def read_json(path):
    d = safe_read(path)
    if d is None:
        return None
    try:
        return json.loads(d)
    except ValueError:
        return None


def find_report(project):
    if not project:
        return None
    p = os.path.join(HERE, 'reports', f'{project.upper()}-AUDIT.md')
    return p if os.path.exists(p) else None


def age_h(path):
    return (time.time() - os.path.getmtime(path)) / 3600


# ------------------------------------------------- pattern engine (pola code yang sudah dibangun)
def scan_patterns(root, patterns):
    """Scan project untuk pola. Return list of (pattern, hits) — hit = (relpath, line_no, snippet)."""
    results = []
    for pat in patterns:
        rx = re.compile(pat['regex'], re.I)
        hits = []
        for cur, dirs, files in os.walk(root):
            dirs[:] = [d for d in dirs if d not in ('node_modules', '__pycache__', '.git', 'dist', 'out', 'target', '.cache')]
            for f in files:
                if len(hits) >= 3:
                    break
                if not f.endswith(EXTS):
                    continue
                p = os.path.join(cur, f)
                try:
                    for i, line in enumerate(open(p, errors='replace'), 1):
                        if rx.search(line):
                            hits.append((os.path.relpath(p, root), i, line.strip()[:90]))
                            if len(hits) >= 3:
                                break
                except OSError:
                    continue
            if len(hits) >= 3:
                break
        results.append((pat, hits))
    return results


def quote_lines(path, rx_str, max_hits=6):
    """Kutip baris dari file yang cocok regex — sumber tercatat path:baris."""
    rx = re.compile(rx_str, re.I)
    hits = []
    try:
        for i, line in enumerate(open(path, errors='replace'), 1):
            if rx.search(line):
                hits.append((i, line.strip()[:110]))
                if len(hits) >= max_hits:
                    break
    except OSError:
        return None
    return hits


# ------------------------------------------------- jawaban berbasis sumber
def ans_status(args):
    bp = read_json(args.get('blueprint')) if args.get('blueprint') else None
    project = None
    if bp:
        project = bp.get('project', {}).get('name')
    elif args.get('project'):
        project = os.path.basename(os.path.realpath(args['project']))
    if not project:
        return fail('butuh --blueprint <file> atau --project <dir> untuk pertanyaan status')
    rep = find_report(project)
    if not rep:
        out(f'{NO_DATA} Laporan audit {project!r} tidak ditemukan di reports/.')
        out(f'Untuk membuatnya: python3 mainnet.py check <blueprint-{project}.json>')
        return 1
    out(f'STATUS {project} — sumber: {os.path.relpath(rep, HERE)} (umur {age_h(rep):.1f} jam)')
    if age_h(rep) > 24:
        out('PERINGATAN: laporan lebih tua dari 24 jam — jalankan check ulang sebelum dipercaya.')
    hits = quote_lines(rep, r'^\| (dimension|backtest|backend|frontend|ui-ux|user-|concept|workflow|framework|docker|implementasi|mainnet|api-|resource|fitur|tipe)')
    if not hits:
        return fail(f'laporan {rep} tidak bisa dibaca')
    for i, line in hits:
        out(f'  {line}')
    na = quote_lines(rep, r'^- \[', 10)
    if na:
        out('  NEXT ACTIONS (dari laporan):')
        for _, line in na:
            out(f'  {line[:150]}')
    return 0


def ans_why_broken(args):
    target = args.get('project') or (read_json(args.get('blueprint')) or {}).get('project', {}).get('name') if args.get('blueprint') else args.get('project')
    if not target and args.get('blueprint'):
        target = (read_json(args['blueprint']) or {}).get('project', {}).get('name')
    rep = find_report(target) if target else None
    if not rep:
        return fail(f'{NO_DATA} tidak ada laporan untuk {target!r} — jalankan check dulu')
    out(f'ANALISA BROKEN — sumber: {os.path.relpath(rep, HERE)}')
    text = safe_read(rep, 100000)
    if not text:
        return fail('laporan tidak bisa dibaca')
    cur = None
    shown = 0
    for line in text.splitlines():
        if line.startswith('## '):
            cur = line[3:].split(' — ')[0]
        m = re.match(r'^\| ([\w/-]+) \| (BROKEN) \| (.*)', line)
        if m and shown < 12:
            out(f'  [{cur}] {m.group(1)}: {m.group(3)[:130]}')
            shown += 1
    if not shown:
        out('  tidak ada check BROKEN di laporan — semua hijau atau belum teraudit')
    na = quote_lines(rep, r'^- \[', 12)
    if na:
        out('  perbaikan yang disarankan laporan (NEXT ACTIONS):')
        for _, line in na:
            out(f'  {line[:150]}')
    out('  (ini kutipan laporan — bukan interpretasi tambahan. kalau butuh mengapa lebih dalam: jalankan check ulang)')
    return 0


def ans_patterns(args):
    root = args.get('project')
    if not root or not os.path.isdir(root):
        return fail('butuh --project <dir> yang valid untuk analisa pola')
    pats = (read_json(PATTERNS_FILE) or {}).get('patterns')
    if not pats:
        return fail(f'{NO_DATA} patterns.json kosong/rusak di {PATTERNS_FILE}')
    out(f'POLA CODE di {os.path.realpath(root)} — bukti: file:baris')
    found, missing = [], []
    for pat, hits in scan_patterns(root, pats):
        if hits:
            found.append((pat, hits))
        else:
            missing.append(pat['label'])
    if not found:
        out(f'  {NO_DATA} Tidak ada pola terkenali terdeteksi di project ini.')
    for pat, hits in found:
        out(f"  [{pat['id']}] {pat['label']} (dimensi: {pat.get('dimension', '-')})")
        for rel, i, snip in hits:
            out(f'      {rel}:{i}: {snip}')
    if missing:
        out(f'  pola yang DICEK tapi tidak ditemukan: {", ".join(missing)}')
    out(f'  registry pola: {os.path.relpath(PATTERNS_FILE, HERE)} — tambah pola di situ, tanpa edit kode.')
    return 0


def ans_chain(args):
    q = (args.get('question') or '').lower()
    stop = {'chain', 'jaringan', 'network', 'rpc', 'chainid', 'apa', 'itu', 'dan', 'the', 'tolong', 'kabar', 'tentang'}
    words = [w for w in re.split(r'\W+', q) if len(w) > 2 and w not in stop]
    nets = read_json(os.path.join(HERE, 'networks.json')) or {}
    said = False
    for name, n in nets.items():
        if name.startswith('_') or not isinstance(n, dict):
            continue
        blob = (name + ' ' + str(n.get('currency', '')) + ' ' + json.dumps(n)).lower()
        if words and not any(w in blob for w in words):
            continue
        out(f'  {name}: family={n.get("family")} chain_id={n.get("chain_id", "-")} rpc={n.get("rpc", "-")} currency={n.get("currency", "-")}')
        if n.get('note'):
            out(f'    catatan: {n["note"]}')
        said = True
    if not said:
        out(f'  {NO_DATA} chain tidak dikenal di networks.json.')
        out('  cari: python3 mainnet.py networks --find <nama>')
    else:
        out('  sumber: networks.json (registry lokal, chainId diverifikasi saat didaftarkan)')
    return 0


def ans_help():
    doc = safe_read(os.path.join(HERE, 'README.md'))
    if doc:
        hits = quote_lines(os.path.join(HERE, 'README.md'), r'^#{1,3} |^\| (`\w+)', 25)
        out('YANG SAYA BISA JAWAB (dengan data, bukan tebakan):')
        for _, line in hits:
            out(f'  {line[:120]}')
    out('  pertanyaan tentang cara pakai lengkap: baca PROMPTS.md (5 prompt siap tempel)')
    out('  detail panduan: README.md — sumber jawaban ini: README.md')
    return 0


ROUTES = [
    (r'status|audit|sehat|kondisi', lambda a: ans_status(a)),
    (r'kenapa|why|broken|gagal|error|next action|perbaikan', lambda a: ans_why_broken(a)),
    (r'pola|pattern|struktur|stack|teknologi|code', lambda a: ans_patterns(a)),
    (r'chain|jaringan|network|rpc|chainid', lambda a: ans_chain(a)),
    (r'cara|gimana|how|panduan|help|bisa apa', lambda a: ans_help()),
]


def run(argv, here=None):
    """Entry point dari mainnet.py agent. NO CRASH: apapun yang meledak jadi pesan jelas."""
    global HERE
    if here:
        HERE = here
    try:
        question = ' '.join(a for a in argv if not a.startswith('--') and not a.endswith('.json'))
        args = {'question': question, 'blueprint': None, 'project': None}
        rest = [a for a in argv if not a.startswith('--')]
        for a in rest:
            if a.endswith('.json') and not args['blueprint']:
                args['blueprint'] = a
        if '--project' in argv:
            args['project'] = argv[argv.index('--project') + 1]
        if '--blueprint' in argv:
            args['blueprint'] = argv[argv.index('--blueprint') + 1]
        if not question and not args['project'] and not args['blueprint']:
            out('agent: butuh pertanyaan. contoh:')
            out('  mainnet.py agent "status" --blueprint examples/blueprint-elysium.json')
            out('  mainnet.py agent "pola code" --project chaff/poc')
            out('  mainnet.py agent "chain elysium"')
            return 1
        for rx, fn in ROUTES:
            if re.search(rx, question, re.I):
                return fn(args) or 0
        out(NO_DATA)
        out('Pertanyaan tidak cocok dengan data yang saya punya. Yang bisa saya jawab:')
        out('  - "status <project>"        (dari laporan audit — butuh --blueprint/--project)')
        out('  - "kenapa broken"           (analisa BROKEN + next actions — butuh --project/--blueprint)')
        out('  - "pola code"               (deteksi pola — butuh --project)')
        out('  - "chain <nama>"            (fakta jaringan dari networks.json)')
        out('  - "cara pakai"              (panduan dari README)')
        return 1
    except Exception as e:  # NO CRASH: apapun yang meledak, user dapat pesan jelas
        out(f'agent: internal error ditangani (bukan crash): {type(e).__name__}: {e}')
        out('laporkan dengan: perintah persis yang dijalankan + output ini.')
        return 1
